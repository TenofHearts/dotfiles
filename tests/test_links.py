import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("links", Path(__file__).resolve().parents[1] / "scripts/links.py")
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)
        self.tmp.cleanup()

    def test_backup_idempotence_and_restore(self):
        original = self.home / ".bashrc"
        original.write_text("original\n")
        links.install(self.home, False)
        self.assertEqual(links.status(self.home), 0)
        links.install(self.home, False)
        manifests = list(self.home.glob(".local/state/dotfiles/backups/*/manifest.json"))
        self.assertEqual(len(manifests), 1)
        links.restore(manifests[0], False)
        self.assertFalse(original.is_symlink())
        self.assertEqual(original.read_text(), "original\n")
        self.assertFalse((self.home / ".zshrc").exists())

    def test_dry_run_has_no_writes(self):
        links.install(self.home, True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_only_codex_installs_and_restores_without_other_configs(self):
        original = self.home / ".bashrc"
        original.write_text("keep local shell\n")
        links.install(self.home, True, "codex")
        self.assertEqual(list(self.home.iterdir()), [original])
        links.install(self.home, False, "codex")
        self.assertEqual(links.status(self.home, "codex"), 0)
        self.assertEqual(original.read_text(), "keep local shell\n")
        self.assertFalse((self.home / ".zshrc").exists())
        links.install(self.home, False, "codex")
        manifests = list(self.home.glob(".local/state/dotfiles/backups/*/manifest.json"))
        self.assertEqual(len(manifests), 1)
        links.restore(manifests[0], False)
        self.assertFalse((self.home / ".codex/dotfiles.config.toml").exists())
        self.assertEqual(original.read_text(), "keep local shell\n")

    def test_codex_profile_preserves_machine_config_and_state(self):
        codex_home = self.home / ".codex"
        codex_home.mkdir()
        local = codex_home / "config.toml"
        local.write_text('[projects."/machine/project"]\ntrust_level = "trusted"\n')
        auth = codex_home / "auth.json"
        auth.write_text("local credentials placeholder\n")
        links.install(self.home, False)
        profile = codex_home / "dotfiles.config.toml"
        self.assertTrue(profile.is_symlink())
        self.assertFalse(local.is_symlink())
        manifest = next(self.home.glob(".local/state/dotfiles/backups/*/manifest.json"))
        links.restore(manifest, False)
        self.assertFalse(profile.exists())
        self.assertEqual(local.read_text(), '[projects."/machine/project"]\ntrust_level = "trusted"\n')
        self.assertEqual(auth.read_text(), "local credentials placeholder\n")

    def test_restore_protects_replaced_files(self):
        links.install(self.home, False)
        changed = self.home / ".zshrc"
        changed.unlink()
        changed.write_text("changed\n")
        manifest = next(self.home.glob(".local/state/dotfiles/backups/*/manifest.json"))
        with self.assertRaises(RuntimeError):
            links.restore(manifest, False)
        self.assertEqual(changed.read_text(), "changed\n")
        self.assertTrue((self.home / ".bashrc").is_symlink())

    def test_symlink_parent_rejected(self):
        target = self.home / "elsewhere"
        target.mkdir()
        (self.home / ".config").symlink_to(target)
        with self.assertRaises(RuntimeError):
            links.install(self.home, False)
        self.assertFalse((self.home / ".bashrc").exists())

    def test_dangling_link_is_backed_up(self):
        dest = self.home / ".zshrc"
        dest.symlink_to("missing-original")
        links.install(self.home, False)
        manifest = next(self.home.glob(".local/state/dotfiles/backups/*/manifest.json"))
        links.restore(manifest, False)
        self.assertEqual(dest.readlink(), Path("missing-original"))

    def test_symlink_backup_parent_rejected_before_changes(self):
        target = self.home / "elsewhere"
        target.mkdir()
        (self.home / ".local").symlink_to(target)
        original = self.home / ".bashrc"
        original.write_text("original\n")
        with self.assertRaises(RuntimeError):
            links.install(self.home, False)
        self.assertEqual(original.read_text(), "original\n")
        self.assertEqual(list(target.iterdir()), [])

    def test_legacy_link_is_migrated_and_restored(self):
        dest = self.home / ".zshrc"
        legacy = links.ROOT / ".zshrc"
        dest.symlink_to(legacy)
        links.install(self.home, False)
        self.assertEqual(dest.resolve(), (links.ROOT / "config/zsh/.zshrc").resolve())
        self.assertNotEqual(dest.readlink(), legacy)
        manifest = next(self.home.glob(".local/state/dotfiles/backups/*/manifest.json"))
        links.restore(manifest, False)
        self.assertEqual(dest.readlink(), legacy)
