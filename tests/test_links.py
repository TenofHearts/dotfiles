import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
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

    def test_replacement_without_backups_and_idempotence(self):
        original = self.home / ".bashrc"
        original.write_text("original\n")
        directory = self.home / ".config/nvim"
        directory.mkdir(parents=True)
        (directory / "local.lua").write_text("local config\n")
        links.install(self.home, False, force=True)
        self.assertEqual(links.status(self.home), 0)
        self.assertTrue(original.is_symlink())
        self.assertTrue(directory.is_symlink())
        before = original.lstat().st_mtime_ns
        links.install(self.home, False, force=True)
        self.assertEqual(original.lstat().st_mtime_ns, before)
        self.assertFalse((self.home / ".local").exists())

    def test_dry_run_has_no_writes(self):
        links.install(self.home, True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_only_codex_installs_without_other_configs(self):
        original = self.home / ".bashrc"
        original.write_text("keep local shell\n")
        links.install(self.home, True, "codex")
        self.assertEqual(list(self.home.iterdir()), [original])
        links.install(self.home, False, "codex")
        self.assertEqual(links.status(self.home, "codex"), 0)
        self.assertEqual(original.read_text(), "keep local shell\n")
        self.assertFalse((self.home / ".zshrc").exists())
        links.install(self.home, False, "codex")
        self.assertFalse((self.home / ".local").exists())

    def test_codex_only_installer_initializes_its_submodule(self):
        bin_dir = self.home / "bin"
        bin_dir.mkdir()
        log = self.home / "git-args"
        fake_git = bin_dir / "git"
        fake_git.write_text('#!/bin/sh\nprintf \'%s\\n\' "$@" > "$DOTFILES_TEST_GIT_LOG"\n')
        fake_git.chmod(0o755)
        env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
               "DOTFILES_TEST_GIT_LOG": str(log)}
        for option in (["--only", "codex"], ["--only=codex"]):
            with self.subTest(option=option):
                subprocess.run(["bash", str(links.ROOT / "install.sh"), *option,
                                "--home", str(self.home)], env=env, check=True, capture_output=True)
                self.assertEqual(log.read_text().splitlines(),
                                 ["-C", str(links.ROOT), "submodule", "update", "--init",
                                  "--recursive", "--", "config/codex"])
        self.assertTrue((self.home / ".codex/dotfiles.config.toml").is_symlink())
        self.assertFalse((self.home / ".bashrc").exists())

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
        self.assertEqual(local.read_text(), '[projects."/machine/project"]\ntrust_level = "trusted"\n')
        self.assertEqual(auth.read_text(), "local credentials placeholder\n")

    def test_restore_protects_replaced_files(self):
        links.install(self.home, False)
        changed = self.home / ".zshrc"
        changed.unlink()
        changed.write_text("changed\n")
        manifest = self.home / "old-manifest.json"
        manifest.write_text(json.dumps([
            {"dest": str(self.home / name), "source": str(links.ROOT / source), "backup": None}
            for name, source in links.FILES.items()
        ]))
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

    def test_dangling_link_is_replaced(self):
        dest = self.home / ".zshrc"
        dest.symlink_to("missing-original")
        links.install(self.home, False, force=True)
        self.assertTrue(links.linked(dest, links.ROOT / "config/zsh/.zshrc"))

    def test_symlink_target_is_preserved(self):
        target = self.home / "elsewhere"
        target.mkdir()
        original = target / "local.lua"
        original.write_text("keep\n")
        (self.home / ".config").mkdir()
        (self.home / ".config/nvim").symlink_to(target)
        links.install(self.home, False, force=True)
        self.assertEqual(original.read_text(), "keep\n")
        self.assertTrue(links.linked(self.home / ".config/nvim", links.ROOT / "config/nvim"))

    def test_legacy_link_is_migrated(self):
        dest = self.home / ".zshrc"
        legacy = links.ROOT / ".zshrc"
        dest.symlink_to(legacy)
        links.install(self.home, False, force=True)
        self.assertEqual(dest.resolve(), (links.ROOT / "config/zsh/.zshrc").resolve())
        self.assertNotEqual(dest.readlink(), legacy)

    def test_dry_run_preserves_conflicts(self):
        original = self.home / ".bashrc"
        original.write_text("keep\n")
        links.install(self.home, True)
        self.assertEqual(original.read_text(), "keep\n")
        self.assertEqual(list(self.home.iterdir()), [original])

    def test_restore_existing_backup(self):
        dest = self.home / ".bashrc"
        saved = self.home / "old-backup"
        saved.write_text("original\n")
        dest.symlink_to(links.ROOT / "config/bash/.bashrc")
        manifest = self.home / "old-manifest.json"
        manifest.write_text(json.dumps([
            {"dest": str(dest), "source": str(links.ROOT / "config/bash/.bashrc"),
             "backup": str(saved)}
        ]))
        links.restore(manifest, False)
        self.assertFalse(dest.is_symlink())
        self.assertEqual(dest.read_text(), "original\n")

    def test_conflicts_are_skipped_and_other_links_installed(self):
        original = self.home / ".bashrc"
        original.write_text("keep shell\n")
        directory = self.home / ".config/nvim"
        directory.mkdir(parents=True)
        (directory / "local.lua").write_text("keep editor\n")
        dangling = self.home / ".zshrc"
        dangling.symlink_to("missing-original")
        links.install(self.home, False)
        self.assertEqual(original.read_text(), "keep shell\n")
        self.assertEqual((directory / "local.lua").read_text(), "keep editor\n")
        self.assertEqual(os.readlink(dangling), "missing-original")
        self.assertTrue(links.linked(self.home / ".vimrc", links.ROOT / "config/vim/.vimrc"))
        self.assertEqual(links.status(self.home), 1)
        links.install(self.home, False)
        self.assertEqual(original.read_text(), "keep shell\n")

    def test_force_dry_run_preserves_conflicts(self):
        original = self.home / ".bashrc"
        original.write_text("keep\n")
        links.install(self.home, True, force=True)
        self.assertEqual(original.read_text(), "keep\n")
        self.assertEqual(list(self.home.iterdir()), [original])

    def test_force_cli_replaces_only_selected_app(self):
        shell = self.home / ".bashrc"
        shell.write_text("keep\n")
        vim = self.home / ".vimrc"
        vim.write_text("replace\n")
        subprocess.run(["bash", str(links.ROOT / "install.sh"), "--only", "vim",
                        "--force", "--home", str(self.home)], check=True, capture_output=True)
        self.assertTrue(vim.is_symlink())
        self.assertEqual(shell.read_text(), "keep\n")
