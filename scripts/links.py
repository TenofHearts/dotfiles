#!/usr/bin/env python3
"""Idempotent configuration links; no third-party Python dependencies."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_APPS = {"freerdp", "ghostty", "hyprland", "hypr-rdp", "kitty", "waybar", "noctalia", "rime", "shotori"}
FILES = {
    ".bashrc": "config/bash/.bashrc",
    ".zshrc": "config/zsh/.zshrc",
    ".vimrc": "config/vim/.vimrc",
    ".tmux.conf": "config/tmux/.tmux.conf",
    ".config/opencode/dotfiles.config.json": "config/ai/opencode/dotfiles.config.json",
    ".config/opencode/personal-instructions.md": "config/ai/opencode/personal-instructions.md",
    ".config/opencode/cli.json": "config/ai/opencode/cli.json",
    ".codex/dotfiles.config.toml": "config/ai/codex/dotfiles.config.toml",
    ".config/nvim": "config/nvim",
    ".config/ghostty/config.ghostty": "config/tty/ghostty/config.ghostty",
    ".config/ghostty/cursor_tail.glsl": "config/tty/ghostty/cursor_tail.glsl",
    ".config/kitty/kitty.conf": "config/tty/kitty/kitty.conf",
    ".config/freerdp/sdl-freerdp.json": "config/freerdp/sdl-freerdp.json",
    ".config/freerdp/connection.rdp.example": "config/freerdp/connection.rdp.example",
    ".config/freerdp/rdp.zsh": "config/freerdp/rdp.zsh",
    ".config/waybar": "config/waybar",
    ".config/noctalia/zz-dotfiles-bars.toml": "config/noctalia/zz-dotfiles-bars.toml",
    ".config/noctalia/zz-dotfiles-launcher.toml": "config/noctalia/zz-dotfiles-launcher.toml",
    ".config/noctalia/zz-dotfiles-templates.toml": "config/noctalia/zz-dotfiles-templates.toml",
    ".config/shotori/settings.toml": "config/shotori/settings.toml",
    ".local/libexec/hypr-rdp/workspaces.py": "platform/cachyos/hypr-rdp/workspaces.py",
    ".local/libexec/hypr-rdp/hypr_ipc.py": "platform/cachyos/hypr-rdp/hypr_ipc.py",
    ".config/systemd/user/hypr-rdp.service.d/50-workspaces.conf": "platform/cachyos/hypr-rdp/50-workspaces.conf",
    ".local/share/fcitx5/rime/default.custom.yaml": "config/rime/default.custom.yaml",
    ".local/share/fcitx5/rime/rime_ice.custom.yaml": "config/rime/rime_ice.custom.yaml",
    ".config/fcitx5/profile": "config/rime/fcitx5/profile",
    ".config/fcitx5/conf/rime.conf": "config/rime/fcitx5/conf/rime.conf",
    ".config/fcitx5/conf/classicui.conf": "config/rime/fcitx5/conf/classicui.conf",
    ".config/oh-my-posh/theme.omp.json": "config/oh-my-posh/theme.omp.json",
    ".config/cowsay/stegosaurus_and_cat.cow": "config/cowsay/stegosaurus_and_cat.cow",
}

# Only shared files are linked; both directories and local Lua modules stay user-owned.
for filename in ("hyprland.lua", "bindings.lua", "help.html", "config/animations.lua",
                 "config/binds.lua", "config/colors.lua", "config/decorations.lua", "config/inputs.lua",
                 "config/misc.lua", "config/monitors.lua", "config/variables.lua", "config/windowrules.lua",
                 "config/workspaces.lua"):
    FILES[f".config/hypr/{filename}"] = f"config/hyprland/{filename}"

for theme in ("purity-of-essence", "purity-of-form"):
    for asset in ("theme.conf", "panel.svg", "highlight.svg"):
        FILES[f".local/share/fcitx5/themes/{theme}/{asset}"] = f"config/rime/fcitx5/themes/{theme}/{asset}"


def exists(path):
    return os.path.lexists(path)


def linked(dest, source):
    return dest.is_symlink() and Path(os.path.abspath(dest.parent / os.readlink(dest))) == source.absolute()


def check_parents(dest, home):
    for parent in dest.parents:
        if parent == home:
            break
        if parent.is_symlink():
            raise RuntimeError(f"Symlinked parent needs manual review: {parent}")


def application(source):
    parts = source.split("/")
    if parts[:2] == ["platform", "cachyos"]:
        return parts[2]
    return parts[2] if parts[1] in {"ai", "tty"} else parts[1]


def selected_files(only=None):
    return {name: src for name, src in FILES.items()
            if (application(src) == only if only else application(src) not in DESKTOP_APPS)}


def xdg_root(home, variable, default):
    root = Path(os.environ.get(variable, ""))
    if not root.is_absolute():  # XDG base directories must be absolute.
        return home / default
    if ".." in root.parts:
        raise RuntimeError(f"Use an absolute {variable} without '..': {root}")
    if home != Path.home().absolute() and root != home and home not in root.parents:
        return home / default  # An alternate --home must not write into the real account.
    return root


def destinations(home, only):
    for name, source in selected_files(only).items():
        dest = home / name
        if application(source) in {"freerdp", "rime", "hyprland"} or (application(source) == "hypr-rdp" and name.startswith(".config/")):
            base, variable = (".config", "XDG_CONFIG_HOME") if name.startswith(".config/") else (".local/share", "XDG_DATA_HOME")
            dest = xdg_root(home, variable, base) / Path(name).relative_to(base)
        yield dest, ROOT / source


def install(home, dry_run, only=None, force=False):
    tty_root = ROOT / "config/tty"
    pending = []
    for dest, source in destinations(home, only):
        if linked(dest, source):
            continue
        legacy_link = (tty_root in source.parents
                       and any(linked(dest, old_root / source.relative_to(tty_root))
                               for old_root in (tty_root.parent, tty_root.with_name("shell"))))
        if exists(dest) and not force and not legacy_link:
            print(f"Skip existing configuration: {dest} (use --force to replace)")
        else:
            pending.append((dest, source))
    # Never follow a parent directory link into an unrelated checkout.
    for dest, source in pending:
        if not source.exists():
            raise RuntimeError(f"Missing source: {source}")
        check_parents(dest, home)
    if not pending:
        print("No configuration links to install.")
        return
    for dest, source in pending:
        print(f"{'Replace and link' if exists(dest) else 'Link'} {dest} -> {source}")
    if dry_run:
        return
    for dest, source in pending:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)
        elif exists(dest):
            dest.unlink()
        dest.symlink_to(os.path.relpath(source, dest.parent.resolve()), target_is_directory=source.is_dir())


def restore(manifest, dry_run):
    records = json.loads(manifest.read_text())
    # Check every entry before changing anything.
    for record in records:
        dest, source = Path(record["dest"]), Path(record["source"])
        if exists(dest) and not linked(dest, source):
            raise RuntimeError(f"Refusing to overwrite a changed file: {dest}")
        if record["backup"] and not exists(Path(record["backup"])):
            raise RuntimeError(f"Backup missing: {record['backup']}")
    for record in reversed(records):
        dest, source = Path(record["dest"]), Path(record["source"])
        print(f"Restore {dest}")
        if dry_run:
            continue
        if linked(dest, source):
            dest.unlink()
        if record["backup"]:
            shutil.move(record["backup"], str(dest))


def status(home, only=None):
    bad = False
    for dest, source in destinations(home, only):
        ok = linked(dest, source)
        print(f"{'OK' if ok else 'MISSING/CHANGED'} {dest}")
        bad |= not ok
    return int(bad)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "status", "restore"))
    parser.add_argument("manifest", nargs="?", type=Path)
    parser.add_argument("--home", type=Path, default=Path.home(), help="Alternate home for testing")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Delete conflicting configurations before installing links; no backups")
    parser.add_argument("--only", choices=sorted({application(src) for src in FILES.values()}),
                        help="Install or inspect only this application's configuration")
    args = parser.parse_args()
    if args.only and args.action == "restore":
        parser.error("--only applies to install and status; restore uses its backup manifest")
    if args.force and args.action != "install":
        parser.error("--force applies only to install")
    home = args.home.absolute()
    if args.action == "install":
        install(home, args.dry_run, args.only, args.force)
    elif args.action == "status":
        return status(home, args.only)
    else:
        if not args.manifest:
            parser.error("restore requires a backup manifest")
        restore(args.manifest, args.dry_run)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError) as error:
        sys.exit(str(error))
