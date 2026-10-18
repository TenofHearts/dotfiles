# Dotfiles

Personal shell, editor, terminal multiplexer, and prompt configuration for a Linux development environment. Configuration lives in `config/`; the installer links it into your home directory and backs up existing files. Neovim and tmux are maintained in separate Git submodules. The tmux configuration can also be installed independently on Linux, macOS, and Windows through WSL.

## Quick start

For Ubuntu/Debian Linux (including WSL2), `bootstrap.sh` installs software from the editable `Brewfile`, configures stable Rust with editor components, and installs the configuration links. Run it as your normal user with sudo access and an internet connection:

```sh
git clone --recurse-submodules https://github.com/TenofHearts/dotfiles.git
cd dotfiles
./bootstrap.sh --dry-run       # Preview without downloading or changing anything
./bootstrap.sh                 # Install software and configuration links
./bootstrap.sh --update        # Update all listed software and stable Rust
./bootstrap.sh --update neovim # Install or update one app
```

Install Git with `sudo apt-get install git` first if needed to clone the repository. Full setup installs build prerequisites through apt; software-only updates do this when Homebrew is absent, then runs the [official Homebrew installer](https://brew.sh/). Homebrew manages development tools independently of your distribution's package versions. Open a new shell afterward to load its PATH.

To install only configuration links, the existing installer requires Bash, Git, and Python 3 with no third-party Python packages:

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

- Both shells derive Miniconda and ICS coursework paths from `$HOME`, but retain the original project layout. Miniconda and coursework are not installed by the bootstrap.
- Zsh exports lowercase proxy variables pointing to `http://127.0.0.1:7897`. Change or remove them if your proxy uses another address or you do not use one.
- Existing rbenv, fnm, and Cargo environment files are loaded when available. Homebrew supplies Python, fnm, uv, and rustup; fnm manages Node.js; existing language managers or activated environments can take precedence over these tools.
- Optional Zsh integrations load autosuggestions/syntax-highlighting from `~/.zsh` or Homebrew. Both Bash and Zsh initialize zoxide when available, using `j` as the jump command. CUDA integration targets `/usr/local/cuda-12.9` when its compiler exists; CUDA is not installed by the bootstrap.
- Select a Nerd Font in your terminal for prompt/editor icons. Neovim can disable icons with `vim.g.have_nerd_font = false` in `config/nvim/init.lua`.

Open a new Bash or Zsh session to load its configuration. For Vim, install vim-plug separately and run `:PlugInstall`. For Neovim dependencies and first-run setup, see the [Neovim README](config/nvim/README.md).

## Repository structure

```text
.
├── install.sh                     # Installation entry point
├── bootstrap.sh                   # Ubuntu/Debian software setup and updates
├── Brewfile                       # Editable software list
├── scripts/
│   ├── links.py                   # Install, inspect, and restore symlinks
│   └── set_proxy.sh               # Export host-derived proxy settings
├── config/
│   ├── bash/.bashrc
│   ├── zsh/.zshrc
│   ├── vim/.vimrc
│   ├── tmux/                      # Git submodule: shared tmux configuration
│   │   ├── .tmux.conf
│   │   └── README.md              # Standalone setup and sync instructions
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
└── .gitmodules                    # Neovim and tmux submodule sources
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

### `bootstrap.sh` and `Brewfile`

```sh
./bootstrap.sh                         # Software, Rust components, and dotfile links
./bootstrap.sh --software-only         # Software and Rust components only
./bootstrap.sh --update                # Upgrade everything in Brewfile and stable Rust
./bootstrap.sh --update neovim uv       # Install/upgrade selected Homebrew formulae only
./bootstrap.sh --dry-run --update       # Preview updates
```

Edit `Brewfile` to choose what belongs on every machine. It includes shells/plugins, Vim/Neovim, tmux, search tools, Oh My Posh, Python, uv, fnm, Rust tooling, and build helpers. Add a line such as `brew "jq"` to keep another tool in your standard setup. A named update can install a formula outside this list, but does not add it to the file.

The software list includes fnm, uv, rustup, zoxide, Zsh plugins, tmux, Vim/Neovim, Oh My Posh, CMake, ccache, htop, rsync, wget, and the shell's fortune/cowsay/lolcat greeting. Ripgrep and fd provide the editor's search dependencies independently of tools bundled with other applications. Ruby/rbenv, MySQL, QEMU, RISC-V/multilib compilers, and opam were left optional because they serve particular projects. Docker is currently supplied by Windows Docker Desktop through WSL, so the bootstrap does not install a competing Linux daemon.

The [Homebrew Bundle command](https://docs.brew.sh/Brew-Bundle-and-Brewfile) installs missing packages and upgrades listed packages. “Latest” means the stable version currently packaged by Homebrew; unversioned entries can cross major versions. Full setup/update installs the latest Node LTS through fnm, preserving an existing default. `./bootstrap.sh --update node` installs the latest Node release through fnm; use `fnm use <version>` and `fnm default <version>` to switch when ready. The first fnm installation supplies a default on a new machine. Global npm packages are not copied between Node versions. Rust uses the latest stable toolchain with `rust-analyzer`, `rust-src`, `rustfmt`, and `clippy`. An existing default Rust toolchain is preserved. Removing an entry does not uninstall software. The bootstrap stops on a failed command; rerun it after fixing the cause. Software installation is not rolled back by the link installer's restore command.

This does not change your login shell. Ruby/rbenv, MySQL, QEMU, RISC-V/multilib compilers, Miniconda, CUDA/GPU drivers, GUI applications, Nerd Fonts, and Vim plugins remain separate installations. The Neovim configuration currently requires Neovim 0.12+; check `nvim --version` against its README if Homebrew's stable package has not reached that requirement.

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

Interactive Zsh terminals automatically attach to a persistent `main` session before loading the rest of the shell configuration. After detaching or exiting tmux, the outer shell finishes loading normally. This skips terminals already inside tmux and VS Code terminals; set `TMUX_AUTOSTART=0` to disable it.

For machine-specific settings, create `~/.zprofile.local` (kept outside this repository):

```zsh
export TMUX_AUTOSTART=0  # Disable automatic tmux startup on this machine; use 1 to enable.
```

`.zshrc` sources this file before the tmux check, including in non-login shells. Keep it limited to environment settings, since it also runs for shells inside tmux. Without a setting, tmux autostart defaults to enabled.

[`config/tmux/.tmux.conf`](config/tmux/.tmux.conf) provides persistent window, pane, and resize modes with Vim-style navigation, colored status badges, and Ctrl+h help in a scrollable popup. New windows and splits preserve the current directory. Alt navigation remains available to the desktop window manager, including GlazeWM. The configuration uses tmux's built-in key tables and pickers without a plugin framework; it requires tmux 3.2 or newer and `less`.

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

For Neovim or tmux changes, commit and push inside `config/nvim` or `config/tmux` first, then commit the updated submodule reference in this repository. See their READMEs for plugin updates and standalone tmux syncing instructions.

To bring an existing checkout to its committed submodule revision after pulling:

```sh
git pull
git submodule update --init --recursive
```

The parent repository pins specific Neovim and tmux commits; updating to a different submodule revision is a deliberate change.
