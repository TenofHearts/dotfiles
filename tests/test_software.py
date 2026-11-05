"""Safety boundaries: resolve before writes, preserve provider choices, safe previews."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from software.adapters import ADAPTERS
from software.adapters.base import Adapter, Runner
from software.manager import Catalog, inspect, native_manager, read_toml, transaction_commands, version_problems

ROOT = Path(__file__).resolve().parents[1]


class SoftwareTests(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog(read_toml(ROOT / "software/manifest.toml"),
                               read_toml(ROOT / "software/packages.toml"))

    def test_detection_uses_os_identity_not_installed_executables(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "os-release"
            path.write_text('ID=custom\nID_LIKE="arch linux"\n')
            self.assertEqual(native_manager(path), "pacman")
            path.write_text('ID=alpine\n')
            self.assertIsNone(native_manager(path))

    def test_unmapped_provider_and_unknown_app_fail_before_transactions(self):
        for names in (["git", "fnm"], ["git", "typo"]):
            with self.subTest(names=names), self.assertRaises(ValueError):
                self.catalog.select(names, provider="native", native="apt")

    def test_conflicting_provider_blocks_the_entire_transaction(self):
        runner = Runner()
        backends = {name: cls(runner) for name, cls in ADAPTERS.items()}
        selection = self.catalog.select(["git", "fd"], native="apt")
        def installed(backend, package):
            return backend is backends["brew"] and package == "fd"
        with patch.object(Adapter, "available", return_value=True), \
             patch.object(ADAPTERS["apt"], "installed", return_value=False), \
             patch.object(ADAPTERS["brew"], "installed", autospec=True, side_effect=installed):
            rows = inspect(self.catalog, selection, backends, "apt")
        with self.assertRaisesRegex(RuntimeError, "Provider conflicts: fd"):
            transaction_commands(rows, "install", backends)

    def test_arch_update_rejected_before_other_manager_transactions(self):
        runner = Runner(dry_run=True)
        backends = {name: cls(runner) for name, cls in ADAPTERS.items()}
        rows = [dict(name=name, manager=manager, packages=[name], missing=[], conflicts=[])
                for name, manager in (("uv", "brew"), ("git", "pacman"))]
        with self.assertRaisesRegex(RuntimeError, "partial upgrades"):
            transaction_commands(rows, "update", backends)

    def test_version_check_uses_selected_provider_and_reports_old_editor(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            (prefix / "bin").mkdir()
            (prefix / "bin/nvim").touch()
            runner = Runner()
            backend = ADAPTERS["brew"](runner, "/chosen/brew")
            rows = [dict(name="neovim", manager="brew", missing=[])]
            replies = [subprocess.CompletedProcess([], 0, directory),
                       subprocess.CompletedProcess([], 0, "NVIM v0.11.5")]
            with patch.object(runner, "query", side_effect=replies) as query:
                problems = version_problems(self.catalog, rows, {"brew": backend})
            self.assertIn("requires >= 0.12", problems[0])
            self.assertEqual(query.call_args.args[0], [str(prefix / "bin/nvim"), "--version"])

    def test_cli_plan_and_install_only_missing_packages(self):
        # Fake package databases and commands, not the host's package managers.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "installed"
            log = root / "transactions"
            script = '''#!{python}
import os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
state = pathlib.Path(os.environ['SOFTWARE_TEST_STATE'])
log = pathlib.Path(os.environ['SOFTWARE_TEST_LOG'])
if name == 'brew':
    sys.exit(1)
if name == 'dpkg-query':
    installed = sys.argv[-1] == 'git' or state.exists()
    print('installed' if installed else 'not-installed')
    sys.exit(0 if installed else 1)
if name == 'sudo':
    os.execv(str(pathlib.Path(sys.argv[0]).parent / sys.argv[1]), sys.argv[1:])
with log.open('a') as stream:
    stream.write(' '.join(sys.argv[1:]) + '\\n')
if 'install' in sys.argv:
    state.touch()
'''.format(python=sys.executable)
            for name in ("dpkg-query", "apt-get", "brew", "sudo"):
                executable = root / name
                executable.write_text(script)
                executable.chmod(0o755)
            env = dict(os.environ, PATH=str(root), SOFTWARE_TEST_STATE=str(state), SOFTWARE_TEST_LOG=str(log))
            command = [sys.executable, str(ROOT / "scripts/software.py")]
            args = ["git", "fd", "--provider", "native", "--native-manager", "apt"]
            for action in ("plan", "install"):
                preview = ["--dry-run"] if action == "install" else []
                result = subprocess.run(command + [action] + args + preview, env=env,
                                        text=True, capture_output=True, check=True)
                self.assertIn("fd-find", result.stdout)
                self.assertFalse(log.exists())
                self.assertFalse(state.exists())
            subprocess.run(command + ["install"] + args, env=env, check=True, capture_output=True)
            self.assertEqual(log.read_text().splitlines(), ["update", "install fd-find"])
            log.unlink()
            subprocess.run(command + ["install"] + args, env=env, check=True, capture_output=True)
            self.assertFalse(log.exists())
