import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
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

    def test_app_only_installer_initializes_its_submodule(self):
        bin_dir = self.home / "bin"
        bin_dir.mkdir()
        log = self.home / "git-args"
        fake_git = bin_dir / "git"
        fake_git.write_text('#!/bin/sh\nprintf \'%s\\n\' "$@" > "$DOTFILES_TEST_GIT_LOG"\n')
        fake_git.chmod(0o755)
        env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
               "DOTFILES_TEST_GIT_LOG": str(log)}
        for app, destination, submodule in (
            ("codex", ".codex/dotfiles.config.toml", "config/ai"),
            ("opencode", ".config/opencode/dotfiles.config.json", "config/ai"),
            ("freerdp", ".config/freerdp/rdp.zsh", "config/freerdp"),
            ("ghostty", ".config/ghostty/config.ghostty", "config/tty"),
            ("kitty", ".config/kitty/kitty.conf", "config/tty"),
        ):
            for option in (["--only", app], ["--only=" + app]):
                with self.subTest(option=option):
                    subprocess.run(["bash", str(links.ROOT / "install.sh"), *option,
                                    "--home", str(self.home)], env=env, check=True, capture_output=True)
                    self.assertEqual(log.read_text().splitlines(),
                                     ["-C", str(links.ROOT), "submodule", "update", "--init",
                                      "--recursive", "--", submodule])
                    self.assertTrue((self.home / destination).is_symlink())
        self.assertFalse((self.home / ".bashrc").exists())

    def test_freerdp_only_links_shared_files_under_xdg(self):
        xdg = self.home / "settings"
        profile = xdg / "freerdp"
        connections = profile / "connections"
        connections.mkdir(parents=True)
        local = connections / "workstation.rdp"
        local.write_text("local configuration\n")
        self.assertFalse(any("freerdp" in src for src in links.selected_files().values()))
        env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(xdg))
        for action in ("install", "status"):
            subprocess.run(["python3", str(links.ROOT / "scripts/links.py"), action, "--only", "freerdp"],
                           env=env, check=True, capture_output=True)
        for name in ("rdp.zsh", "sdl-freerdp.json", "connection.rdp.example"):
            self.assertTrue(links.linked(profile / name, links.ROOT / "config/freerdp" / name))
        self.assertFalse(profile.is_symlink())
        self.assertEqual(local.read_text(), "local configuration\n")

    def test_terminal_install_migrates_only_legacy_dotfiles_links(self):
        ghostty = self.home / ".config/ghostty/config.ghostty"
        kitty = self.home / ".config/kitty/kitty.conf"
        ghostty.parent.mkdir(parents=True)
        kitty.parent.mkdir(parents=True)
        legacy = links.ROOT / "config/ghostty/config.ghostty"
        ghostty.symlink_to(os.path.relpath(legacy, ghostty.parent))
        shader = ghostty.parent / "cursor_tail.glsl"
        shader.symlink_to(links.ROOT / "config/shell/ghostty/cursor_tail.glsl")
        kitty.write_text("local profile\n")
        links.install(self.home, False)
        links.install(self.home, True, only="ghostty")
        self.assertTrue(links.linked(ghostty, legacy))
        links.install(self.home, False, only="ghostty")
        links.install(self.home, False, only="kitty")
        self.assertEqual(links.status(self.home, only="ghostty"), 0)
        self.assertTrue(shader.is_file())
        self.assertEqual(kitty.read_text(), "local profile\n")

    def test_opencode_preserves_local_settings_and_key(self):
        config = self.home / ".config/opencode"
        config.mkdir(parents=True)
        local = config / "opencode.json"
        local.write_text('{"model": "local/model"}\n')
        key = config / "thirdparty.key"
        key.write_text("local credentials placeholder\n")
        key.chmod(0o600)
        links.install(self.home, False, only="opencode")
        self.assertEqual(links.status(self.home, only="opencode"), 0)
        self.assertTrue((config / "cli.json").is_symlink())
        self.assertTrue((config / "personal-instructions.md").is_symlink())
        self.assertEqual(local.read_text(), '{"model": "local/model"}\n')
        self.assertEqual(key.read_text(), "local credentials placeholder\n")
        self.assertEqual(key.stat().st_mode & 0o777, 0o600)
        self.assertFalse((self.home / ".codex").exists())

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

    def test_hyprland_and_waybar_are_independent_configuration_links(self):
        links.install(self.home, False)
        self.assertFalse((self.home / ".config/hypr").exists())
        self.assertFalse((self.home / ".config/waybar").exists())
        links.install(self.home, False, only="hyprland")
        hypr = self.home / ".config/hypr"
        self.assertFalse(hypr.is_symlink())
        self.assertFalse((hypr / "config").is_symlink())
        for name in ("hyprland.lua", "config/inputs.lua", "bindings.lua", "help.html"):
            self.assertTrue(links.linked(hypr / name, links.ROOT / "config/hyprland" / name))
        self.assertFalse((self.home / ".config/waybar").exists())
        links.install(self.home, False, only="waybar")
        self.assertTrue((self.home / ".config/waybar").is_symlink())
        self.assertEqual(links.status(self.home, only="hyprland"), 0)
        self.assertEqual(links.status(self.home, only="waybar"), 0)

    def test_hyprland_force_preserves_local_modules(self):
        hypr = self.home / ".config/hypr"
        (hypr / "config").mkdir(parents=True)
        paths = [hypr / name for name in ("config/autostart.lua", "config/environment.lua",
                                          "config/local.lua", "xdph.conf")]
        for path in paths:
            path.write_text("local settings\n")
        links.install(self.home, False, only="hyprland", force=True)
        self.assertEqual(links.status(self.home, only="hyprland"), 0)
        for path in paths:
            self.assertFalse(path.is_symlink())
            self.assertEqual(path.read_text(), "local settings\n")

    def test_hyprland_force_rejects_legacy_directory_link(self):
        hypr = self.home / ".config/hypr"
        hypr.parent.mkdir()
        hypr.symlink_to(links.ROOT / "config/hyprland")
        with self.assertRaisesRegex(RuntimeError, "Symlinked parent"):
            links.install(self.home, False, only="hyprland", force=True)
        self.assertTrue(hypr.is_symlink())

    @unittest.skipUnless(shutil.which("Hyprland"), "requires the Hyprland Lua config verifier")
    def test_hyprland_loads_optional_local_files_from_linked_profile(self):
        config = self.home / "settings"
        profile = config / "hypr/hyprland.lua"
        env = dict(os.environ, XDG_CONFIG_HOME=str(config))
        subprocess.run(["python3", str(links.ROOT / "scripts/links.py"), "install", "--home", str(self.home),
                        "--only", "hyprland"], env=env, check=True, capture_output=True)

        def verify():
            result = subprocess.run(["Hyprland", "--verify-config", "--config", str(profile)],
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            return result.stdout

        self.assertIn("config ok", verify())
        modules = profile.parent / "config"
        (modules / "autostart.lua").write_text("STARTUP_LOADED = true\n")
        (modules / "environment.lua").write_text("ENV_LOADED = true\n")
        (modules / "local.lua").write_text('if STARTUP_LOADED and ENV_LOADED and TERMINAL then\n'
                                           '    error("local override reached")\nend\n')
        self.assertIn("local override reached", verify())

    def test_desktop_input_and_capture_are_opt_in_and_preserve_user_data(self):
        rime = self.home / ".local/share/fcitx5/rime"
        rime.mkdir(parents=True)
        learned = rime / "user.yaml"
        learned.write_text("local state\n")
        links.install(self.home, False, force=True)
        self.assertEqual(list(rime.iterdir()), [learned])
        self.assertFalse((self.home / ".config/fcitx5").exists())
        settings = self.home / ".config/shotori/settings.toml"
        self.assertFalse(settings.exists())
        links.install(self.home, False, only="rime", force=True)
        self.assertTrue((rime / "default.custom.yaml").is_symlink())
        self.assertEqual(learned.read_text(), "local state\n")
        self.assertFalse(settings.exists())
        links.install(self.home, False, only="shotori")
        self.assertTrue(links.linked(settings, links.ROOT / "config/shotori/settings.toml"))

    def test_rdp_dropin_is_opt_in_and_preserves_the_base_service(self):
        units = self.home / ".config/systemd/user"
        units.mkdir(parents=True)
        base = units / "hypr-rdp.service"
        base.write_text("existing service\n")
        dropin = units / "hypr-rdp.service.d/50-workspaces.conf"
        links.install(self.home, False)
        self.assertFalse(dropin.exists())
        links.install(self.home, False, only="hypr-rdp")
        self.assertTrue(dropin.is_symlink())
        self.assertEqual(links.status(self.home, "hypr-rdp"), 0)
        self.assertEqual(base.read_text(), "existing service\n")
        self.assertFalse((self.home / ".config/hypr-rdp/config.toml").exists())

    def test_rime_install_and_status_use_fcitx_xdg_roots(self):
        config, data = self.home / "settings", self.home / "data"
        env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(config), XDG_DATA_HOME=str(data))
        cli = ["python3", str(links.ROOT / "scripts/links.py")]
        for action in ("install", "status"):
            subprocess.run(cli + [action, "--only", "rime"], env=env, check=True, capture_output=True)
        self.assertTrue((config / "fcitx5/profile").is_symlink())
        self.assertTrue((data / "fcitx5/rime/default.custom.yaml").is_symlink())
        self.assertTrue((data / "fcitx5/themes/purity-of-form/theme.conf").is_symlink())
        sandbox = self.home / "other-home"
        subprocess.run(cli + ["install", "--only", "rime", "--home", str(sandbox)],
                       env=env, check=True, capture_output=True)
        self.assertTrue((sandbox / ".local/share/fcitx5/rime/default.custom.yaml").is_symlink())
