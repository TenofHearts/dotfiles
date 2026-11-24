import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


path = Path(__file__).resolve().parents[1] / "platform/cachyos/hypr-rdp/hypr_ipc.py"
spec = importlib.util.spec_from_file_location("hypr_ipc", path)
ipc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ipc)


class IpcTests(unittest.TestCase):
    def setUp(self):
        self.desktop = ipc.Desktop("test_123_456")
        self.run = self.enterContext(patch.object(ipc.subprocess, "run"))

    def test_only_exact_rdp_output_can_be_removed(self):
        for name in ("eDP-1", "hypr-rdp-1"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.desktop.remove_output(name)
        self.run.assert_not_called()

    def test_remove_and_confirmation_target_same_compositor(self):
        self.run.side_effect = [subprocess.CompletedProcess([], 0, stdout=data)
                                for data in (b"ok", b'[{"name":"hypr-rdp"}]')]
        with self.assertRaisesRegex(RuntimeError, "remains"):
            self.desktop.remove_output("hypr-rdp")
        prefix = ["hyprctl", "-i", self.desktop.instance]
        self.assertEqual([call.args[0] for call in self.run.call_args_list],
                         [prefix + ["output", "remove", "hypr-rdp"], prefix + ["-j", "monitors", "all"]])
