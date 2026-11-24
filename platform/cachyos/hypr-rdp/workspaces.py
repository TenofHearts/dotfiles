#!/usr/bin/env python3
"""Workspace lifecycle hooks for the user's hypr-rdp.service (Hyprland 0.57)."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import time
import tomllib


OUTPUT = "hypr-rdp"


def selector(ws):
    address = ws.get("address", "")
    if not address:
        return None
    if ws.get("type") == "special" or address.startswith("special:"):
        return address
    return str(ws["id"]) if isinstance(ws.get("id"), int) else "name:" + address


def regular(desktop):
    return {selector(w): w for w in desktop.workspaces() if w["type"] != "special"}


def physical(monitors):
    return {m["name"]: m for m in monitors if not m.get("disabled") and
            m.get("mirrorOf", "none") in ("none", "") and m["name"] != OUTPUT and
            not is_headless(m) and m["name"] != "FALLBACK"}


def is_headless(monitor):
    # The headless backend can report empty EDID strings. 0.57 exposes the
    # actual backend independently of the output's name or description.
    return monitor.get("hardwareDetails", {}).get("backend", "").lower() == "headless"


def snapshot(desktop):
    displays = physical(desktop.monitors())
    if not displays:
        raise RuntimeError("No active physical display; refusing to move workspaces")
    focus = next((name for name, m in displays.items() if m["focused"]), next(iter(displays)))
    w = desktop.active_window()
    return {"focus": focus, "window": w.get("stableId"),
            "views": {n: selector(m["activeWorkspace"]) for n, m in displays.items()},
            "special": {n: selector(m.get("specialWorkspace", {})) for n, m in displays.items()},
            "homes": {k: w["monitor"] for k, w in regular(desktop).items() if w["monitor"] in displays}}


def save(path, state):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as f:
        json.dump(state, f)
    os.replace(f.name, path)


def unused(desktop, base):
    used = regular(desktop)
    name = "name:" + base
    i = 0
    while name in used:
        i += 1
        name = f"name:{base}-{i}"
    return name


def owned_output(desktop, state):
    m = next((m for m in desktop.monitors() if m["name"] == OUTPUT), None)
    if m and (not is_headless(m) or m["id"] != state.get("output_id")):
        raise RuntimeError("RDP output identity does not match the recorded output; leaving it alone")
    if m:
        desktop.verify_output(OUTPUT, state["token"])
    return m


def display(desktop, name, ws):
    m = next((m for m in desktop.monitors() if m["name"] == name), None)
    if m is None:
        raise RuntimeError(f"Display disappeared: {name}")
    if selector(m["activeWorkspace"]) != ws:
        desktop.show(name, ws)


def park_output(desktop, state, path):
    remote = owned_output(desktop, state)
    if remote and selector(remote.get("specialWorkspace", {})):
        desktop.show_special(OUTPUT, None)
    ws = regular(desktop).get(state["idle"])
    # A user may have opened a window on our placeholder. It is now a real
    # workspace: allocate an empty replacement and bring the old one home.
    if ws and (ws["windows"] or ws["monitor"] != OUTPUT):
        state["idle"] = unused(desktop, "rdp-idle")
        save(path, state)
    display(desktop, OUTPUT, state["idle"])


def restore(desktop, state, path, output_present):
    snap = state["snapshot"]
    monitors = physical(desktop.monitors())
    if not monitors:
        raise RuntimeError("No physical display for restoration; saved state retained")
    fallback = snap["focus"] if snap["focus"] in monitors else next(iter(monitors))
    if output_present:
        park_output(desktop, state, path)

    # Restore each visible workspace as a whole. set_workspace may recreate
    # an originally visible empty workspace that Hyprland garbage-collected.
    for name, ws in snap["views"].items():
        if name in monitors and ws:
            display(desktop, name, ws)

    for ws, w in regular(desktop).items():
        if output_present and ws == state["idle"]:
            continue
        home = snap["homes"].get(ws)
        if not home and w["monitor"] != OUTPUT:
            continue
        target = home if home in monitors else fallback
        if target != w["monitor"]:
            desktop.move(ws, target)

    for name, ws in snap["special"].items():
        if name in monitors and ws and any(selector(w) == ws for w in desktop.workspaces()):
            if selector(monitors[name].get("specialWorkspace", {})) != ws:
                desktop.show_special(name, ws)
    desktop.focus_monitor(fallback)
    if snap["window"]:
        window = next((w for w in desktop.clients() if w.get("stableId") == snap["window"]), None)
        if window and window.get("mapped", True) and selector(window["workspace"]) in (
                snap["special"].get(fallback), snap["views"].get(fallback)):
            desktop.focus_window(snap["window"])


def lifecycle(action, desktop, statefile):
    state = json.loads(statefile.read_text()) if statefile.exists() else None
    invocation = os.getenv("INVOCATION_ID")
    if action == "status":
        print("Workspace lifecycle:", state["phase"] if state else "not running")
        return
    if action == "prepare":
        if state or any(m["name"].startswith(OUTPUT) for m in desktop.monitors()):
            raise RuntimeError("Existing state or RDP output; inspect status before starting")
        snap = snapshot(desktop)
        save(statefile, {"phase": "starting", "invocation": invocation, "snapshot": snap,
                         "idle": unused(desktop, "rdp-idle")})
        return
    if not state:
        if action == "stop":
            return
        raise RuntimeError("No pre-start snapshot for this compositor")
    if invocation and state["invocation"] != invocation:
        raise RuntimeError("State belongs to another service invocation; leaving it alone")

    if action in ("ready", "connect") and state["phase"] == "starting":
        deadline = time.monotonic() + 5
        while True:
            m = next((m for m in desktop.monitors() if m["name"] == OUTPUT and not m.get("disabled")), None)
            if m and is_headless(m) and m["activeWorkspace"].get("address"):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("Managed headless output did not become ready")
            time.sleep(0.05)
        token = secrets.token_hex(16)
        desktop.claim_output(OUTPUT, token)
        state.update(output_id=m["id"], token=token, phase="initializing")
        save(statefile, state)
        restore(desktop, state, statefile, True)
        state.update(phase="idle", snapshot=None)
        save(statefile, state)
    if action == "ready":
        if state["phase"] not in ("idle", "connected"):
            raise RuntimeError("Initialization incomplete")
        return
    if action == "stop" and state["phase"] == "starting":
        # No positively identified owned output. Never delete one by prefix.
        if any(m["name"].startswith(OUTPUT) for m in desktop.monitors()):
            raise RuntimeError("Unclaimed output remains after startup failure; manual inspection needed")
        restore(desktop, state, statefile, False)
        statefile.unlink()
        return

    output = owned_output(desktop, state)
    if action == "connect":
        if state["phase"] == "connected":
            return
        if not output or state["phase"] != "idle":
            raise RuntimeError("Not ready for a handoff")
        snap = snapshot(desktop)
        displays = physical(desktop.monitors())
        if any(w.get("pinned") and w.get("mapped", True) and selector(w["workspace"]) in snap["homes"]
               for w in desktop.clients()):
            raise RuntimeError("Unpin local windows before workspace handoff; leaving the desktop in place")
        if snap["views"].keys() != displays.keys():
            raise RuntimeError("Physical displays changed during snapshot; refusing handoff")
        parking = {name: unused(desktop, "rdp-local-" + str(m["id"])) for name, m in displays.items()}
        state.update(phase="transferring", snapshot=snap)
        save(statefile, state)  # write-ahead recovery before the first move
        try:
            for name in snap["views"]:
                if snap["special"][name]:
                    desktop.show_special(name, None)
                display(desktop, name, parking[name])
            for ws in snap["homes"]:
                w = regular(desktop).get(ws)
                if w and w["monitor"] != OUTPUT:
                    desktop.move(ws, OUTPUT)
            display(desktop, OUTPUT, snap["views"][snap["focus"]])
            desktop.focus_monitor(OUTPUT)
        except (OSError, RuntimeError, KeyError):
            restore(desktop, state, statefile, owned_output(desktop, state) is not None)
            state.update(phase="idle", snapshot=None)
            save(statefile, state)
            raise
        state["phase"] = "connected"
    elif action == "disconnect":
        if state["phase"] in ("idle", "stopping"):
            return
        restore(desktop, state, statefile, output is not None)
        state.update(phase="idle", snapshot=None)
    elif action == "before-stop":
        # SIGTERM can remove the monitor before ExecStopPost gets to inspect it.
        # Preserve the current local view, not the one from server startup.
        if state["snapshot"] is None:
            state["snapshot"] = snapshot(desktop)
        state["phase"] = "stopping"
    elif action == "stop":
        if state["snapshot"] is None:
            if not output:
                statefile.unlink()
                return
            state["snapshot"] = snapshot(desktop)
        save(statefile, state)
        if output:
            restore(desktop, state, statefile, True)
            if owned_output(desktop, state):
                desktop.remove_output(OUTPUT)
        restore(desktop, state, statefile, False)
        statefile.unlink()
        return
    else:
        raise ValueError(action)
    save(statefile, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "prepare", "ready", "connect", "disconnect", "before-stop", "stop"))
    action = parser.parse_args().action
    instance = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", instance):
        raise RuntimeError("A valid HYPRLAND_INSTANCE_SIGNATURE is required")
    runtime = Path(os.environ["XDG_RUNTIME_DIR"])
    root = runtime / ("hypr-rdp-workspaces-" + instance)
    statefile = root / "state.json"
    if action == "status":
        lifecycle(action, None, statefile)
        return
    lockinfo = (runtime / "hypr" / instance / "hyprland.lock").read_text().splitlines()
    if lockinfo[1:2] != [os.environ.get("WAYLAND_DISPLAY")]:
        raise RuntimeError("Hyprland instance does not match WAYLAND_DISPLAY")
    from hypr_ipc import Desktop
    root.mkdir(mode=0o700, exist_ok=True)
    with (root / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if action in ("prepare", "stop"):
            probe = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "hypr-rdp"], stdout=subprocess.DEVNULL)
            if probe.returncode != 1:
                raise RuntimeError("Cannot establish that hypr-rdp is stopped")
        if action == "prepare":
            config = Path.home() / ".config/hypr-rdp/config.toml"
            with config.open("rb") as f:
                settings = tomllib.load(f)
            if any(settings.get(k) for k in ("output", "on_session_start", "on_session_end")):
                raise RuntimeError("Existing native output or session hook configuration conflicts with the drop-in")
        lifecycle(action, Desktop(instance), statefile)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        sys.exit(f"hypr-rdp-workspaces: {error}")
