# Linux dotfiles

For CachyOS and [Ubuntu under WSL](platform/wsl-ubuntu/README.md). Install Bash, Git, and Python 3.6+ first. Keep the checkout in place: the installed configurations are symlinks.

```sh
git clone --recurse-submodules https://github.com/TenofHearts/dotfiles.git
cd dotfiles
./install.sh --dry-run
./install.sh
python3 scripts/links.py status
```

To install one profile, use `./install.sh --only NAME`. Run `./install.sh --help` for the names. Desktop profiles are opt-in. Existing files are skipped; **`--force` deletes conflicts without a backup**.

## Packages

`install.sh` only links files. To install packages as well, preview with `./bootstrap.sh --dry-run`, then run `./bootstrap.sh`. This requires Python 3.11+, or Python 3.8+ with `tomli`. For the optional CachyOS desktop packages, use `./scripts/software.py install --group desktop`. See [Node and Rust setup](runtimes/README.md) for toolchains.

## Profiles

- [Neovim](config/nvim/README.md): `./install.sh --only nvim`. Use Neovim 0.12+, Git, ripgrep, and fd; start `nvim` once to install plugins. Pyright needs Node/npm.
- [tmux](config/tmux/README.md): `./install.sh --only tmux`. Use tmux 3.2+, Git, and `less`.
- [Codex and OpenCode](config/ai/README.md): install the CLI, then link `codex` or `opencode`. For OpenCode, keep the gateway key in `~/.config/opencode/thirdparty.key` (mode `0600`).
- Kitty or Ghostty: link `kitty` or `ghostty` and install `ttf-0xproto-nerd` on CachyOS.
- Hyprland: link `hyprland`. If upgrading from a whole-directory `~/.config/hypr` symlink, preserve local files and move the symlink aside first. See the [shortcut help](config/hyprland/help.html).
- Waybar with Noctalia: link `waybar` and `noctalia`, then run `waybar -c ~/.config/waybar/with-noctalia.jsonc` at login.
- [FreeRDP client](config/freerdp/README.md): on CachyOS, run `./scripts/software.py install freerdp fzf`, then `./install.sh --only freerdp`. Open a new dotfiles Zsh shell.
- Follow the [hypr-rdp service guide](platform/cachyos/hypr-rdp/README.md) or [Rime input method guide](config/rime/README.md) for those profiles.
