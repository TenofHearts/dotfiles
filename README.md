# Dotfiles

Personal shell, editor, terminal multiplexer, and prompt configuration for a Linux development environment. Configuration lives in `config/`; the installer links it into your home directory and skips existing configurations by default. Use `--force` to delete conflicts and replace them with links; no backups are created. Codex, Neovim, and tmux are maintained in separate Git submodules. The tmux configuration can also be installed independently on Linux, macOS, and Windows through WSL.

## Quick start

For Linux (including WSL2), the optional `bootstrap.sh` installs software from the editable `Brewfile`, configures stable Rust with editor components, and installs the configuration links. Run it as your normal user with sudo access and an internet connection:

```sh
git clone --recurse-submodules https://github.com/TenofHearts/dotfiles.git
cd dotfiles
./bootstrap.sh --dry-run       # Preview without downloading or changing anything
./bootstrap.sh                 # Install software and links; skip existing configurations
./bootstrap.sh --update        # Update all listed software and stable Rust
./bootstrap.sh --update neovim # Install or update one app
```

Install Git with your distribution's package manager first if needed to clone the repository. When Homebrew is absent, setup installs prerequisites through a small apt/dnf/pacman adapter, then runs the [official Homebrew installer](https://brew.sh/). Existing Homebrew installations skip native package commands. Use `--skip-prerequisites` if you manage prerequisites yourself or use another distribution. Homebrew manages development tools independently of your distribution's package versions. Open a new shell afterward to load its PATH.

To install only configuration links, the existing installer requires Bash, Git, and Python 3.6+ with no third-party Python packages:

```sh
git clone --recurse-submodules https://github.com/TenofHearts/dotfiles.git
cd dotfiles

# Review the personal settings described below before loading a new shell.
./install.sh --dry-run
./install.sh                    # Preserve and skip conflicting configurations
./install.sh --force --dry-run  # Preview deleting conflicts
./install.sh --force            # Delete conflicts and install links (no backups)
python3 scripts/links.py status
```

If you already cloned without submodules, run `git submodule update --init --recursive` before previewing installation. A real installation runs that command automatically; a dry run skips it.

Machine-specific configuration belongs outside this repository:

- `~/.bashrc.local` and `~/.zshrc.local` load last and can override shared settings. Put proxy settings, coursework paths, CUDA setup and other workstation settings here. No proxy is enabled by default.
- `~/.zprofile.local` loads early in Zsh; use it for `TMUX_AUTOSTART=0` because tmux starts before the final local hook.
- Existing Miniconda, rbenv, fnm and Cargo integrations load when available. Their tools or activated environments can take precedence over Homebrew tools.
- Zsh plugins load from `~/.zsh`, Homebrew, or common distro package locations. Both shells initialize zoxide when available, using `j` as the jump command.
- Select a Nerd Font in your terminal for prompt/editor icons. Neovim can disable icons with `vim.g.have_nerd_font = false` in `config/nvim/init.lua`.

For example, add only the settings you need to your shell's local file:

```sh
export NEMU_HOME="$HOME/Programing/PA/ics2024/nemu"
# Enable only if a proxy is running at this address:
# export http_proxy=http://127.0.0.1:7897
# export https_proxy="$http_proxy"
# export all_proxy="$http_proxy"
```

Open a new Bash or Zsh session to load its configuration. For Vim, install vim-plug separately and run `:PlugInstall`. For Neovim dependencies and first-run setup, see the [Neovim README](config/nvim/README.md).

## Repository structure

```text
.
├── install.sh                     # Installation entry point
├── bootstrap.sh                   # Optional Linux software setup and updates
├── Brewfile                       # Editable software list
├── scripts/
│   ├── links.py                   # Install, inspect, and restore symlinks
│   ├── prerequisites.sh           # Native prerequisites only: apt/dnf/pacman
│   └── set_proxy.sh               # Export host-derived proxy settings
├── config/
│   ├── bash/.bashrc
│   ├── zsh/.zshrc
│   ├── vim/.vimrc
│   ├── codex/                     # Git submodule: shared Codex CLI preferences
│   │   ├── dotfiles.config.toml
│   │   └── README.md
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
├── tests/                        # Installer and prerequisite adapter regression tests
└── .gitmodules                    # Codex, Neovim and tmux submodule sources
```

The installer uses these fixed destinations under the selected home directory; it does not consult `XDG_CONFIG_HOME`:

| Source | Destination |
| --- | --- |
| `config/bash/.bashrc` | `~/.bashrc` |
| `config/zsh/.zshrc` | `~/.zshrc` |
| `config/vim/.vimrc` | `~/.vimrc` |
| `config/tmux/.tmux.conf` | `~/.tmux.conf` |
| `config/codex/dotfiles.config.toml` | `~/.codex/dotfiles.config.toml` |
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

### Homebrew tradeoffs

Homebrew is the default for the optional software bootstrap because one Brewfile keeps development tools consistent across distro families and provides newer tools independently of distro release cycles. Configuration installation itself does not require Homebrew: use `./install.sh` and supply applications through your preferred package manager.

The costs of using Homebrew by default are:

- **Duplicate software and PATH precedence.** Distro and Homebrew copies may coexist. These shell configurations put Homebrew tools first when available, which can change which Git, Python or compiler a command uses. Use the final local shell hook to override that choice.
- **Additional storage and maintenance.** Homebrew brings its own dependency tree; maintain it separately from system security updates. Keep system services, drivers and distro components under the native package manager.
- **Platform and prefix constraints.** Binary package availability depends on the platform and installation prefix. The standard Linux prefix is `/home/linuxbrew/.linuxbrew`; other locations can require source builds. Homebrew is not a universal solution for every Linux system. See [Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux).
- **Rolling upgrades rather than a reproducible environment.** This Brewfile does not pin versions. Upgrades may cross major versions and upgrade related dependencies; a named update can therefore affect more than one tool. See the [Homebrew FAQ](https://docs.brew.sh/FAQ#why-does-brew-upgrade-formula-or-brew-install-formula-also-upgrade-a-bunch-of-other-stuff).

Distro-specific commands live only in `scripts/prerequisites.sh` and run only when Homebrew is missing. Its apt, dnf and pacman branches cover prerequisite package mappings, not complete distro certification. Other systems can install prerequisites manually and pass `--skip-prerequisites`; this does not bypass Homebrew's own platform requirements. The adapter never performs a full distro upgrade. Review pending system updates yourself before installing prerequisites.

### `install.sh`

```sh
./install.sh                    # Initialize submodules and install links
./install.sh --dry-run          # Preview link changes without writing files
./install.sh --force            # Delete conflicting configurations; no backups
./install.sh --only codex       # Install only the shared Codex profile
./install.sh --home /tmp/demo-home  # Install into an alternate home
```

Resolves the repository from its own location, updates required submodules on real installs, and delegates to `links.py install`. Use `--only APP` to select one application's configuration; for Codex, launch with `codex --profile dotfiles` afterward. Arguments are forwarded to Python. Keep the checkout in place: the installed files are relative symlinks into it.

### `scripts/links.py`

```sh
python3 scripts/links.py install [--only APP] [--home PATH] [--dry-run] [--force]
python3 scripts/links.py status [--only APP] [--home PATH]
python3 scripts/links.py restore /path/to/manifest.json [--dry-run]
python3 scripts/links.py --help
```

- **Install:** leaves correct links alone, reports and skips existing files, directories and conflicting symlinks (including dangling links), and installs the remaining links. Skipped conflicts are not errors; use `status` to check whether all requested links are installed. `--force` permanently deletes conflicts before linking; no backups or manifests are created. `--dry-run --force` previews replacements without deleting anything. Sources and destination parents for links to be installed are checked before changes begin. Symlinked destination parents such as `~/.config` require manual review and are rejected. A failed installation may leave partial changes.
- **Status:** reports `OK` or `MISSING/CHANGED` for each destination. Exits with code 0 when every link matches, or 1 otherwise. It checks link targets, not configuration contents or application dependencies.
- **Restore (existing backups only):** reads a manifest from an older installation, validates all entries before changing files, removes installer links, and restores saved originals. Destinations with no original backup are simply unlinked. It refuses to overwrite a destination that has been replaced with another file or link, and refuses missing backups. The manifest contains absolute paths; `--home` does not relocate a restore.

Older installations stored backup manifests under:

```text
~/.local/state/dotfiles/backups/<timestamp>/manifest.json
```

To restore a backup created by an older installation, use its exact manifest:

```sh
python3 scripts/links.py restore "$HOME/.local/state/dotfiles/backups/<timestamp>/manifest.json" --dry-run
python3 scripts/links.py restore "$HOME/.local/state/dotfiles/backups/<timestamp>/manifest.json"
```

Replace `<timestamp>` with the actual backup directory. Restore moves backed-up originals back into place, so that backup is consumed. Only entries changed by that installation are included. New installations cannot be undone using this command because they do not create backups. This also applies to `--force`.

### `scripts/set_proxy.sh`

Source this script from the shell where you want its exports to persist:

```sh
source scripts/set_proxy.sh
```

Reads the nameserver address from `/etc/resolv.conf` and exports uppercase `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` using HTTP port `7897`. This assumes the nameserver address also reaches a proxy host, as in some WSL setups; it does not discover or start a proxy. It expects a single nameserver entry. This helper is opt-in and is never sourced automatically. Align uppercase and lowercase variables if clients use different capitalization.

To clear both sets for the current session:

```sh
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
```

### Tests

```sh
python3 -m unittest discover -s tests -v
```

Runs installer tests in temporary home directories and prerequisite dispatch tests with mocked commands; no packages are installed. Covers skipping conflicts by default, forced replacement without backups, repeated installation, restoration of older manifests, dry runs, changed-file protection, dangling and legacy links, and rejection of symlinked destination parents.

## Application configurations

### Bash

[`config/bash/.bashrc`](config/bash/.bashrc) provides a familiar shell for everyday command-line work and development. It builds on familiar Bash defaults, keeping established shell behavior while making development tools easier to access. The guiding principle is practical convenience through straightforward startup configuration. Use `~/.bashrc.local` for workstation-specific paths and settings.

### Zsh

[`config/zsh/.zshrc`](config/zsh/.zshrc) configures the main interactive development shell. Its emphasis is on reducing friction during everyday terminal work and making language environments convenient to use. User-specific paths generally derive from `$HOME`, making the configuration easier to reuse across accounts. The overall approach is to keep environment setup in one place and load optional integrations conditionally where supported, with final machine-specific overrides in `~/.zshrc.local`.

### tmux

Interactive Zsh terminals automatically attach to a persistent `main` session before loading the rest of the shell configuration. After detaching or exiting tmux, the outer shell finishes loading normally. This skips terminals already inside tmux and VS Code terminals; set `TMUX_AUTOSTART=0` to disable it.

For machine-specific settings, create `~/.zprofile.local` (kept outside this repository):

```zsh
export TMUX_AUTOSTART=0  # Disable automatic tmux startup on this machine; use 1 to enable.
```

`.zshrc` sources this file before the tmux check, including in non-login shells. Keep it limited to environment settings, since it also runs for shells inside tmux. Without a setting, tmux autostart defaults to enabled.

[`config/tmux/.tmux.conf`](config/tmux/.tmux.conf) provides persistent window, pane, and resize modes with Vim-style navigation, colored status badges, and Ctrl+h help in a scrollable popup. New windows and splits preserve the current directory. Alt navigation remains available to the desktop window manager, including GlazeWM. The configuration uses tmux's built-in key tables and pickers without a plugin framework; it requires tmux 3.2 or newer and `less`.

### Codex

[`config/codex/`](config/codex/) provides shared Codex CLI preferences with automatic approval review, Vim input mode, and a status bar showing model, project, context, and usage limits. It is maintained in a separate Git submodule. Bash and Zsh load the profile through the `codex` alias. Machine-specific settings remain in `~/.codex/config.toml`, with shared profile values taking precedence.

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

For Codex, Neovim, or tmux changes, commit and push inside `config/codex`, `config/nvim`, or `config/tmux` first, then commit the updated submodule reference in this repository. See their READMEs for setup and syncing instructions.

To bring an existing checkout to its committed submodule revision after pulling:

```sh
git pull
git submodule update --init --recursive
```

The parent repository pins specific Codex, Neovim, and tmux commits; updating to a different submodule revision is a deliberate change.
