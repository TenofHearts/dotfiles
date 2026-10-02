# Dotfiles

Personal shell, editor, terminal multiplexer, and prompt configuration for a Linux development environment. Configuration lives in `config/`; the installer links it into your home directory and backs up existing files. Neovim is maintained in a separate Git submodule.

## Quick start

The installer requires Bash, Git, and Python 3 with no third-party Python packages. Install the applications you intend to use separately: this repository does not install system packages, change your login shell, or bootstrap shell plugins.

```sh
git clone --recurse-submodules https://github.com/TenofHearts/dotfiles.git
cd dotfiles

# Review the personal settings described below before loading a new shell.
./install.sh --dry-run
./install.sh
python3 scripts/links.py status
```

If you already cloned without submodules, run `git submodule update --init --recursive` before previewing installation. A real installation runs that command automatically; a dry run skips it.

Before opening a new shell, adapt these settings to your machine:

- Bash contains absolute `/home/ten_of_hearts/...` paths for Miniconda and the ICS coursework projects. Zsh derives those paths from `$HOME`, but retains the same project layout.
- Zsh exports lowercase proxy variables pointing to `http://127.0.0.1:7897`. Change or remove them if your proxy uses another address or you do not use one.
- Both shells invoke `rbenv`; Bash sources `$HOME/.cargo/env`, and Zsh invokes `fnm` even outside its directory check. Install these tools or adjust those startup lines. Zsh's uv setup checks for `~/.local/bin`, rather than checking whether `uv` and `uvx` exist.
- Optional Zsh integrations expect autojump under `~/.autojump` and autosuggestions/syntax-highlighting under `~/.zsh`. CUDA integration targets `/usr/local/cuda-12.9` when its compiler exists.
- Select a Nerd Font in your terminal for prompt/editor icons. Neovim can disable icons with `vim.g.have_nerd_font = false` in `config/nvim/init.lua`.

Open a new Bash or Zsh session to load its configuration. For Vim, install vim-plug separately and run `:PlugInstall`. For Neovim dependencies and first-run setup, see the [Neovim README](config/nvim/README.md).

## Repository structure

```text
.
├── install.sh                     # Installation entry point
├── scripts/
│   ├── links.py                   # Install, inspect, and restore symlinks
│   └── set_proxy.sh               # Export host-derived proxy settings
├── config/
│   ├── bash/.bashrc
│   ├── zsh/.zshrc
│   ├── vim/.vimrc
│   ├── tmux/.tmux.conf
│   ├── oh-my-posh/theme.omp.json
│   ├── cowsay/stegosaurus_and_cat.cow
│   └── nvim/                      # Git submodule: TenofHearts/nvim-config
│       ├── init.lua               # Editor options and active plugins
│       ├── nvim-pack-lock.json    # Pinned plugin revisions
│       ├── formatters/clang-format.yaml
│       └── lua/
│           ├── custom/            # Language settings and extension loader
│           └── kickstart/         # Health check and plugin modules/examples
├── tests/test_links.py            # Installer regression tests
└── .gitmodules                    # Neovim submodule source
```

The installer uses these fixed destinations under the selected home directory; it does not consult `XDG_CONFIG_HOME`:

| Source | Destination |
| --- | --- |
| `config/bash/.bashrc` | `~/.bashrc` |
| `config/zsh/.zshrc` | `~/.zshrc` |
| `config/vim/.vimrc` | `~/.vimrc` |
| `config/tmux/.tmux.conf` | `~/.tmux.conf` |
| `config/nvim/` | `~/.config/nvim` |
| `config/oh-my-posh/theme.omp.json` | `~/.config/oh-my-posh/theme.omp.json` |
| `config/cowsay/stegosaurus_and_cat.cow` | `~/.config/cowsay/stegosaurus_and_cat.cow` |

## Script usage

### `install.sh`

```sh
./install.sh                    # Initialize submodules and install links
./install.sh --dry-run          # Preview link changes without writing files
./install.sh --home /tmp/demo-home  # Install into an alternate home
```

Resolves the repository from its own location, updates submodules on real installs, and delegates to `links.py install`. Arguments are forwarded to Python. Keep the checkout in place: the installed files are relative symlinks into it.

### `scripts/links.py`

```sh
python3 scripts/links.py install [--home PATH] [--dry-run]
python3 scripts/links.py status [--home PATH]
python3 scripts/links.py restore /path/to/manifest.json [--dry-run]
python3 scripts/links.py --help
```

- **Install:** checks source availability and destination parents, leaves correct links alone, and moves conflicting files, directories, or dangling symlinks into a timestamped backup. Writes a manifest and creates relative symlinks. Repeating an unchanged installation creates no new backup. If installation fails partway through, it attempts to undo changes already made.
- **Status:** reports `OK` or `MISSING/CHANGED` for each destination. Exits with code 0 when every link matches, or 1 otherwise. It checks link targets, not configuration contents or application dependencies.
- **Restore:** reads the manifest, validates all entries before changing files, removes installer links, and restores saved originals. Destinations with no original backup are simply unlinked. It refuses to overwrite a destination that has been replaced with another file or link, and refuses missing backups. The manifest contains absolute paths; `--home` does not relocate a restore.

Backup manifests are printed after installation and stored under:

```text
~/.local/state/dotfiles/backups/<timestamp>/manifest.json
```

To undo an installation, use its exact manifest:

```sh
python3 scripts/links.py restore "$HOME/.local/state/dotfiles/backups/<timestamp>/manifest.json" --dry-run
python3 scripts/links.py restore "$HOME/.local/state/dotfiles/backups/<timestamp>/manifest.json"
```

Replace `<timestamp>` with the actual backup directory. Restore moves backed-up originals back into place, so that backup is consumed. Only entries changed by that installation are included. Installation rejects symlinked destination parents such as `~/.config`, and symlinked backup parents, to avoid writing through them into another location.

### `scripts/set_proxy.sh`

Source this script from the shell where you want its exports to persist:

```sh
source scripts/set_proxy.sh
```

Reads the nameserver address from `/etc/resolv.conf` and exports uppercase `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` using HTTP port `7897`. This assumes the nameserver address also reaches a proxy host, as in some WSL setups; it does not discover or start a proxy. It expects a single nameserver entry. Its uppercase variables coexist with Zsh's lowercase localhost defaults, so align both sets if clients use different capitalization.

To clear both sets for the current session:

```sh
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
```

### `tests/test_links.py`

```sh
python3 -m unittest discover -s tests -v
```

Runs the installer tests in temporary home directories. Covers backups, repeated installation, restoration, dry runs, changed-file protection, dangling and legacy links, and rejection of symlinked destination/backup parents.

## Application configurations

### Bash

[`config/bash/.bashrc`](config/bash/.bashrc) provides a familiar shell for everyday command-line work and development. It builds on standard Debian-style Bash defaults, keeping established shell behavior while making development tools easier to access. The guiding principle is practical convenience through straightforward startup configuration. Some paths reflect the original workstation, so adapting it to another machine requires reviewing those assumptions.

### Zsh

[`config/zsh/.zshrc`](config/zsh/.zshrc) configures the main interactive development shell. Its emphasis is on reducing friction during everyday terminal work and making language environments convenient to use. User-specific paths generally derive from `$HOME`, making the configuration easier to reuse across accounts. The overall approach is to keep environment setup in one place and load optional integrations conditionally where supported, while retaining some machine-specific assumptions described in the quick start.

### tmux

[`config/tmux/.tmux.conf`](config/tmux/.tmux.conf) supports working across multiple terminal windows and panes within a persistent session. The guiding principle is to make navigation require fewer keystrokes and preserve working-directory context when creating new workspaces. The configuration stays small and focuses on interaction preferences, making it easy to understand and adapt without introducing a larger plugin framework.

### Vim

[`config/vim/.vimrc`](config/vim/.vimrc) provides a lightweight editing environment built around familiar Vim behavior. A small set of plugins improves common editing tasks while keeping the configuration straightforward. Its guiding principle is incremental enhancement: retain the core editor workflow and add conveniences where they help everyday use. Plugin installation is separate from the dotfiles installer.

### Neovim

[`config/nvim/`](config/nvim/) provides the primary development editor and is maintained as a separate Git submodule. Its design separates editor behavior from language-specific settings, pins plugin revisions, and respects project-specific tooling. Keeping it in its own repository lets the editor configuration evolve independently while this repository records a deliberate version. See the [Neovim README](config/nvim/README.md) for setup and usage details.

### Oh My Posh

[`config/oh-my-posh/theme.omp.json`](config/oh-my-posh/theme.omp.json) defines a shared prompt for Bash and Zsh. Its purpose is to make useful development and session context visible at a glance. The guiding principle is to keep prompt presentation in one reusable theme, separate from each shell's startup logic, so both shells have a consistent appearance and changes can be made in one place.

### cowsay

[`config/cowsay/stegosaurus_and_cat.cow`](config/cowsay/stegosaurus_and_cat.cow) adds a personal touch to terminal output with custom stegosaurus-and-cat artwork. It remains a standalone asset that can be used on demand rather than being tied to shell startup. The guiding principle is simple reuse: keep the artwork in cowsay's native format and let the application handle the accompanying message bubble.

## Editing and updates

Edit files under `config/`; installed symlinks expose those edits directly. If you move the checkout, rerun installation to repair links. To add another managed configuration, add its destination/source pair to `FILES` in `scripts/links.py`.

For Neovim changes, commit and push inside `config/nvim` first, then commit the updated submodule reference in this repository. See its README for plugin update instructions.

To bring an existing checkout to its committed submodule revision after pulling:

```sh
git pull
git submodule update --init --recursive
```

The parent repository pins a specific Neovim commit; updating to a different submodule revision is a deliberate change.
