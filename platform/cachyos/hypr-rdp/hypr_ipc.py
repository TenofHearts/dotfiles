"""Pinned hyprctl adapter for the Hyprland 0.57.2 Lua API."""
import json
import re
import subprocess


def _lua(value):
    if not isinstance(value, str) or not value or "\0" in value:
        raise ValueError("Expected a nonempty Hyprland identifier without NUL")
    # Lua decimal escapes encode bytes, not code points. Escape '/' too:
    # hyprctl recognizes substrings like '/instances' anywhere in its argv.
    return '"' + ''.join(chr(b) if 32 <= b < 127 and chr(b) not in '"\\/'
                         else f"\\{b:03d}" for b in value.encode("utf-8")) + '"'


def _monitor(name):
    # get_monitor also accepts relative selectors. Only act on the exact name.
    return f"local name = {_lua(name)}; local m = assert(hl.get_monitor(name)); assert(m.name == name)"


def _window(stable_id):
    if not isinstance(stable_id, str) or not re.fullmatch(r"[0-9a-f]+", stable_id):
        raise ValueError("Expected a hexadecimal stable window ID")
    return (f"local id = {_lua(stable_id)}; local w = assert(hl.get_window('stableid:' .. id)); "
            "assert(w.mapped and w.stable_id == id)")


def _dispatch(expression):
    return f"assert(hl.dispatch(hl.dsp.{expression}).ok)"


class Desktop:
    def __init__(self, instance):
        # An empty argument makes hyprctl use the environment; numbers are indices.
        if not isinstance(instance, str) or "_" not in instance or not re.fullmatch(r"[A-Za-z0-9_-]+", instance):
            raise ValueError("Expected a Hyprland instance signature")
        self.instance = instance

    def _run(self, operation, *args):
        try:
            result = subprocess.run(["hyprctl", "-i", self.instance, *args], capture_output=True, timeout=3)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"hyprctl {operation} timed out") from None
        # Responses can contain titles or fragments of the Lua command. Keep them
        # out of service logs, including when a JSON response is malformed.
        if result.returncode:
            raise RuntimeError(f"hyprctl {operation} failed (exit {result.returncode})")
        return result.stdout

    def _json(self, shape, command, *args):
        raw = self._run(command, "-j", command, *args)
        try:
            data = json.loads(raw)
        except ValueError:
            raise RuntimeError(f"hyprctl {command} returned invalid JSON") from None
        if not isinstance(data, shape) or (shape is list and not all(isinstance(x, dict) for x in data)):
            raise RuntimeError(f"hyprctl {command} returned an unexpected response")
        return data

    def _ok(self, operation, *args):
        if self._run(operation, *args).strip() != b"ok":
            raise RuntimeError(f"hyprctl {operation} did not confirm success")

    def _eval(self, operation, *statements):
        self._ok(operation, "eval", "; ".join(statements))

    def monitors(self):
        return self._json(list, "monitors", "all")

    def workspaces(self):
        return self._json(list, "workspaces")

    def clients(self):
        return self._json(list, "clients")

    def active_window(self):
        return self._json(dict, "activewindow")

    def claim_output(self, name, token):
        self._eval("claim RDP output", _monitor(name), "assert(m.hardware_details.backend == 'headless')",
                   f"_G.dotfiles_rdp_output = {{monitor = m, token = {_lua(token)}}}")

    def verify_output(self, name, token):
        # Numeric monitor IDs can be reused. Lua holds a weak reference to the
        # original object; a recreation or Lua config reload invalidates proof.
        self._eval("verify RDP output", _monitor(name), "local claim = _G.dotfiles_rdp_output",
                   f"assert(claim and claim.token == {_lua(token)} and claim.monitor == m)")

    def show(self, monitor, selector):
        self._eval("show workspace", _monitor(monitor), f"local s = {_lua(selector)}",
                   "m:set_workspace(s)", "assert(m.active_workspace and m.active_workspace == hl.get_workspace(s))")

    def show_special(self, monitor, selector):
        # In 0.57.2 set_special_workspace prepends 'special:' to string inputs.
        # Strip exactly one prefix, even for an address like 'special:special:a'.
        if selector is None:
            self._eval("hide special workspace", _monitor(monitor), "m:set_special_workspace(nil)",
                       "assert(m.active_special_workspace == nil)")
        else:
            if not isinstance(selector, str) or not selector.startswith("special:"):
                raise ValueError("Expected a full special workspace address")
            bare = _lua(selector.removeprefix("special:"))
            self._eval("show special workspace", _monitor(monitor), f"local bare = {bare}",
                       "m:set_special_workspace(bare)",
                       "assert(m.active_special_workspace and m.active_special_workspace.addressable_name == 'special:' .. bare)")

    def move(self, selector, monitor):
        # Moving the active regular workspace off the focused output carries
        # focus and warps the cursor. The caller parks that output beforehand.
        self._eval("move workspace", _monitor(monitor), f"local w = assert(hl.get_workspace({_lua(selector)}))",
                   "local src = assert(w.monitor)", "assert(src == m or not src.focused or src.active_workspace ~= w)",
                   _dispatch("workspace.move({workspace = w, monitor = m})"), "assert(w.monitor == m)")

    def focus_monitor(self, monitor):
        self._eval("focus monitor", _monitor(monitor), _dispatch("focus({monitor = m})"), "assert(m.focused)")

    def focus_window(self, stable_id):
        self._eval("focus window", _window(stable_id), _dispatch("focus({window = 'stableid:' .. id})"),
                   "assert(hl.get_active_window() == w)")

    def remove_output(self, name):
        if name != "hypr-rdp":
            raise ValueError("Only the hypr-rdp output may be removed")
        self._ok("remove output", "output", "remove", name)
        if any(m["name"] == name for m in self.monitors()):
            raise RuntimeError("hypr-rdp output remains after removal")
