"""Exercise the listener hooks against an in-memory Hyprland desktop."""
import importlib.util
from pathlib import Path
import tempfile
import unittest


HELPER = Path(__file__).resolve().parents[1] / "platform/cachyos/hypr-rdp/workspaces.py"
spec = importlib.util.spec_from_file_location("rdp_workspaces", HELPER)
hooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hooks)

LEFT, RIGHT, RDP = "DP-1", "HDMI-A-1", "hypr-rdp"
LOCAL = {"1": LEFT, "2": LEFT, "3": LEFT, "4": RIGHT}


class FakeDesktop:
    def __init__(self):
        self.ids = {LEFT: 0, RIGHT: 1}
        self.homes = LOCAL.copy()
        self.views = {LEFT: "1", RIGHT: "4"}
        self.persistent = {"2"}
        self.windows = {"a1": "1", "a3": "3", "b1": "4", "b2": "4"}
        self.focused, self.window = RIGHT, "b2"
        self.claim = None

    def add_rdp(self, output_id=7):
        self.claim = None
        self.ids[RDP] = output_id
        self.views[RDP] = "8"
        self.homes["8"] = RDP

    @staticmethod
    def ref(ws):
        address = ws.removeprefix("name:") if ws else ""
        return {"id": int(ws) if ws and ws.isdecimal() else None,
                "name": address, "address": address,
                "type": "special" if address.startswith("special:") else "normal"}

    def monitors(self):
        return [{"id": ident, "name": name, "description": "" if name == RDP else name,
                 "hardwareDetails": {"backend": "headless" if name == RDP else "drm"},
                 "make": "", "model": "", "activeWorkspace": self.ref(self.views[name]),
                  "specialWorkspace": self.ref(None), "focused": self.focused == name,
                 "disabled": False, "mirrorOf": "none"} for name, ident in self.ids.items()]

    def workspaces(self):
        return [{**self.ref(ws), "monitor": mon, "windows": sum(w == ws for w in self.windows.values()),
                 "ispersistent": ws in self.persistent} for ws, mon in self.homes.items()]

    def client(self, stable_id):
        ws = self.windows[stable_id]
        return {"stableId": stable_id, "mapped": True, "workspace": self.ref(ws)}

    def clients(self):
        return [self.client(stable_id) for stable_id in self.windows]

    def active_window(self):
        return self.client(self.window) if self.window else {}

    def claim_output(self, name, token):
        self.claim = (name, token)

    def verify_output(self, name, token):
        if self.claim != (name, token):
            raise RuntimeError("RDP output was replaced")

    def _collect(self, ws):
        if ws not in self.views.values() and ws not in self.windows.values() and ws not in self.persistent:
            self.homes.pop(ws, None)

    def show(self, monitor, selector):
        if selector in self.homes:
            self.move(selector, monitor)
        else:
            self.homes[selector] = monitor
        previous = self.views[monitor]
        self.views[monitor] = selector
        self._collect(previous)
        self.focus_monitor(monitor)

    def move(self, selector, monitor):
        source = self.homes[selector]
        if source == monitor:
            return
        if self.views[source] == selector:
            # Hyprland leaves every output with a visible workspace.
            number = 1
            while str(number) in self.homes:
                number += 1
            self.views[source] = str(number)
            self.homes[str(number)] = source
        self.homes[selector] = monitor
        self.focus_monitor(self.focused)

    def focus_monitor(self, monitor):
        visible = self.views[monitor]
        self.focused = monitor
        if self.windows.get(self.window) != visible:
            self.window = next((key for key, ws in self.windows.items() if ws == visible), None)

    def focus_window(self, stable_id):
        ws = self.windows[stable_id]
        monitor = self.homes[ws]
        self.show(monitor, ws)
        self.window = stable_id

    def remove_output(self, name):
        del self.ids[name], self.views[name]
        # Model native output loss: surviving workspaces land on the first display.
        fallback = next(iter(self.ids))
        for ws, mon in self.homes.copy().items():
            if mon == name:
                self.homes[ws] = fallback
                self._collect(ws)
        if self.focused == name:
            self.focus_monitor(fallback)


class RdpWorkspaceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.statefile = Path(tmp.name) / "state.json"
        self.d = FakeDesktop()

    def hook(self, action):
        hooks.lifecycle(action, self.d, self.statefile)

    def start_listener(self):
        self.hook("prepare")
        self.d.add_rdp()
        self.hook("ready")

    def assert_local(self, left="1", right="4", monitor=RIGHT, window="b2"):
        self.assertEqual({ws: self.d.homes.get(ws) for ws in LOCAL}, LOCAL)
        self.assertEqual((self.d.views[LEFT], self.d.views[RIGHT]), (left, right))
        self.assertEqual((self.d.focused, self.d.window), (monitor, window))

    def assert_idle_rdp(self):
        self.assertIn(RDP, self.d.ids)
        idle = self.d.views[RDP]
        self.assertEqual({ws for ws, mon in self.d.homes.items() if mon == RDP}, {idle})
        self.assertNotIn(idle, self.d.windows.values())
        self.assertNotIn(idle, LOCAL)

    def test_ready_repairs_startup_migration_and_restores_focus(self):
        self.hook("prepare")
        self.d.add_rdp()
        self.d.move("3", RDP)  # Inactive but occupied, from the other display.
        self.d.show(RDP, "4")
        self.assertEqual(self.d.focused, RDP)
        self.hook("ready")
        self.assert_local()
        self.assert_idle_rdp()

    def test_handoff_and_disconnect_return_whole_workspaces_and_original_focus(self):
        self.start_listener()
        original_windows = self.d.windows.copy()
        self.hook("connect")
        self.assertEqual({self.d.homes.get(ws) for ws in LOCAL}, {RDP})
        self.assertEqual((self.d.focused, self.d.views[RDP]), (RDP, "4"))
        self.assertEqual(self.d.windows, original_windows)
        for mon in (LEFT, RIGHT):
            self.assertEqual(self.d.homes[self.d.views[mon]], mon)
            self.assertNotIn(self.d.views[mon], self.d.windows.values())

        self.d.show(RDP, "9")
        self.d.windows["c1"] = "9"
        self.d.focus_window("c1")
        self.hook("connect")  # A duplicate notification must preserve current work.
        self.assertEqual((self.d.views[RDP], self.d.window), ("9", "c1"))
        self.hook("disconnect")
        self.assert_local()
        self.assert_idle_rdp()
        self.assertEqual(self.d.homes["9"], RIGHT)
        self.assertEqual(self.d.windows, {**original_windows, "c1": "9"})

    def test_second_session_starts_from_fresh_local_view(self):
        self.start_listener()
        self.hook("connect")
        self.hook("disconnect")
        self.d.focus_window("a3")
        self.hook("disconnect")
        self.hook("ready")
        self.assert_local(left="3", monitor=LEFT, window="a3")
        self.hook("connect")
        self.assertEqual((self.d.focused, self.d.views[RDP]), (RDP, "3"))
        self.d.show(RDP, "4")
        self.hook("disconnect")
        self.assert_local(left="3", monitor=LEFT, window="a3")
        self.assert_idle_rdp()

    def test_prepare_refuses_preexisting_rdp_and_stop_leaves_it_alone(self):
        self.d.add_rdp()
        before = (self.d.monitors(), self.d.workspaces(), self.d.clients())
        with self.assertRaises(RuntimeError):
            self.hook("prepare")
        self.hook("stop")
        self.assertEqual((self.d.monitors(), self.d.workspaces(), self.d.clients()), before)

    def test_pinned_window_refuses_handoff_before_any_parking(self):
        self.start_listener()
        client = self.d.client
        self.d.client = lambda key: {**client(key), "pinned": key == "b1"}
        with self.assertRaisesRegex(RuntimeError, "Unpin"):
            self.hook("connect")
        self.assert_local()
        self.assert_idle_rdp()

    def test_before_stop_saves_idle_view_not_original_startup_view(self):
        self.start_listener()
        self.d.focus_window("a3")
        self.hook("before-stop")
        self.d.remove_output(RDP)
        self.d.focus_window("b1")
        self.hook("stop")
        self.assert_local(left="3", monitor=LEFT, window="a3")

    def test_stop_without_disconnect_restores_desktop_then_removes_owned_output(self):
        self.start_listener()
        self.hook("connect")
        self.d.show(RDP, "9")
        self.d.windows["c1"] = "9"
        self.hook("stop")
        self.assertNotIn(RDP, self.d.ids)
        self.assert_local()
        self.assertEqual(self.d.homes["9"], RIGHT)
        self.d.focus_window("a3")
        self.hook("stop")
        self.assert_local(left="3", monitor=LEFT, window="a3")
        self.start_listener()  # A clean stop permits a new invocation.
        self.assert_idle_rdp()

    def test_stop_recovers_after_native_output_has_already_disappeared(self):
        self.start_listener()
        self.hook("connect")
        self.d.remove_output(RDP)
        self.assertEqual(self.d.homes["4"], LEFT)
        self.hook("stop")
        self.assertNotIn(RDP, self.d.ids)
        self.assert_local()

    def test_stop_refuses_replacement_output_with_same_name(self):
        self.start_listener()
        self.d.remove_output(RDP)
        self.d.add_rdp(output_id=7)  # Hyprland can re-use the previous monitor ID
        before = (self.d.monitors(), self.d.workspaces())
        with self.assertRaises(RuntimeError):
            self.hook("stop")
        self.assertEqual((self.d.monitors(), self.d.workspaces()), before)


if __name__ == "__main__":
    unittest.main()
