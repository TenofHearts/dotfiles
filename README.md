# Dotfiles

Personal Linux dotfiles for Ubuntu under WSL and native CachyOS.

## Quick start

Configuration setup requires Bash, Git, and Python 3.6+. Keep the checkout in a stable location: the installed files are symlinks into it.

```sh
git clone --recurse-submodules https://github.com/TenofHearts/dotfiles.git
cd dotfiles
./install.sh --dry-run
./install.sh
python3 scripts/links.py status
```

`install.sh` skips existing configurations and does not install packages. Use `--only APP` to link one profile. **`--force` deletes conflicting files or directories without a backup.**

## Optional software

Review the manifest for [Ubuntu under WSL](software/manifests/wsl-ubuntu.toml) or [CachyOS](software/manifests/cachyos.toml). Software management requires Python 3.11+, or Python 3.8+ with `tomli`.

```sh
./scripts/software.py plan   # Preview package commands for this host
./bootstrap.sh               # Install missing packages, then link configurations
```

Desktop packages are opt-in on CachyOS (`./scripts/software.py plan --group desktop`). For Node or Rust setup after installation, see the [runtime guide](runtimes/README.md).

## Desktop setup

Desktop configuration links are opt-in. Run `./install.sh --only APP` for each profile you use; `./install.sh --help` lists the names.

- **Kitty and Ghostty** use the [TTY submodule](https://github.com/TenofHearts/tty-config) at `config/tty`. Run `./install.sh --only kitty` or `./install.sh --only ghostty` to install or migrate the corresponding dotfiles symlinks. Install `ttf-0xproto-nerd` on CachyOS for the shared 12 pt font. If you manage your own terminal profile, review the submodule settings before merging them into your profile.
- **Hyprland:** `./install.sh --only hyprland` links the [CachyOS-based profile](config/hyprland/hyprland.lua), its [settings modules](config/hyprland/config), and the [shared shortcuts](config/hyprland/help.html) as individual files. `~/.config/hypr` and its `config/` subdirectory stay real directories. Keep login commands in `config/autostart.lua`, environment settings in `config/environment.lua`, and final overrides in `config/local.lua` under `~/.config/hypr/`. All three are optional and never installed or replaced. Back up any conflicting shared files before using `--force`. If upgrading from the old whole-directory symlink, move the **symlink itself** aside first and preserve any local-only files from its target.
- **Waybar with Noctalia:** Link `waybar` and `noctalia`. In the existing Noctalia session, launch `waybar -c ~/.config/waybar/with-noctalia.jsonc` once at login.
- **Rime:** Follow the [Fcitx5 deployment guide](config/rime/README.md) to install the pinned schema and link the input profile.

For app-specific setup, see [Neovim](config/nvim/README.md), [tmux](config/tmux/README.md), and [AI tools](config/ai/README.md).
