# Dotfiles

Personal shell, editor, tmux and prompt configuration for Linux. Configuration lives in `config/`; installation links it into your home directory. Existing configurations are skipped by default. `--force` deletes conflicts without backups.

Software management is optional and independent of configuration installation. One TOML manifest selects applications; small apt, dnf, pacman and Homebrew adapters handle package operations. Codex, Neovim and tmux configurations are pinned Git submodules.

## Quick start

Install Git and Python through your distribution first, then:

```sh
git clone --recurse-submodules https://github.com/TenofHearts/dotfiles.git
cd dotfiles

# Configuration only: Bash, Git and Python 3.6+, no third-party packages.
./install.sh --dry-run
./install.sh
python3 scripts/links.py status
```

For software management, use **Python 3.11+**, or Python 3.8+ with `tomli` installed in that interpreter. The linker does not need TOML support. On older systems, install `tomli` through your distro or a Python environment; the software command reports a missing parser before making changes.

```sh
./scripts/software.py plan                   # Inspect providers, conflicts and commands
./bootstrap.sh --dry-run                     # Preview software and configuration setup
./bootstrap.sh                              # Install missing software, then link configuration
./bootstrap.sh --software-only --group core  # Install only core software
./scripts/toolchains.sh --dry-run            # Separate Node LTS/Rust stable setup
./scripts/toolchains.sh
```

Review `software/manifest.toml` first. Native packages are the default. Neovim, Oh My Posh, uv, fnm and rustup explicitly use Homebrew; zoxide also retains its existing Homebrew provider. The optional `fun` group contains fortune/cowsay/lolcat. Bootstrap provisions Homebrew only if a selected application requires it and it is missing. Configuration installation alone never provisions it.

**Migrating an existing Homebrew workstation:** provider conflicts are reported and block transactions. For example, if fd is already installed through Homebrew, add `[software.fd]` with `provider = "brew"` to retain it. To migrate providers, remove the old provider's packages yourself, then install through the chosen provider. This tool never automatically removes packages or rewrites your manifest. It detects duplicates between the host's native package database and Homebrew, not arbitrary manually installed binaries.

Existing clones can adopt the HTTPS submodule URLs with `git submodule sync --recursive` before updating submodules. Public submodules need no GitHub SSH setup; private repositories still require access.

## Software manifest

Edit desired applications and providers in [`software/manifest.toml`](software/manifest.toml):

```toml
[defaults]
provider = "native"
groups = ["core", "editors", "development"]

[groups]
core = ["git", "zsh", "tmux", "ripgrep", "fd"]
editors = ["vim", "neovim"]
development = ["uv", "fnm", "rustup"]

[software.neovim]
provider = "brew"
command = "nvim"
minimum_version = "0.12"
```

Groups choose what to install. Application IDs are independent of distro package names. Explicit names and `--group` selections are combined; with neither, the default groups are selected. Repeat `--group` to combine groups.

[`software/packages.toml`](software/packages.toml) maps IDs to provider-specific package names:

```toml
[packages.fd]
apt = ["fd-find"]
dnf = ["fd-find"]
pacman = ["fd"]
brew = ["fd"]

[packages.git]
default = ["git"]
```

To add software, add a catalog mapping, then include its ID in a group. `default` is shorthand for names shared by all adapters; omit it when support differs. An absent mapping is an error, never an automatic fallback or a guessed package name. Package availability depends on your distro release and enabled repositories. The tool does not enable repositories, install AUR helpers, or promise that every catalog entry exists on every supported release. On Debian/Ubuntu the fd package commonly provides `fdfind`; installing a package does not rename its commands.

```sh
./scripts/software.py plan --group core
./scripts/software.py install --group core
./scripts/software.py check
./scripts/software.py update neovim uv
./scripts/software.py install git fd
./scripts/software.py plan --provider brew          # Override all selected providers
./scripts/software.py plan --native-manager dnf     # Override host detection
./scripts/software.py install --dry-run --group fun
```

- **Plan / dry run:** read installed-package databases and print transactions; no downloads, package changes, or local state files. Plans may include commands for a missing manager. A real direct install requires that manager to exist; bootstrap can explicitly provision Homebrew.
- **Install:** resolve all selected applications and provider conflicts before executing transactions. Install only missing packages, without explicitly upgrading already installed applications. Dependency resolution can still change related packages. Native managers retain their normal interactive transaction prompts.
- **Check:** exit 0 if selected packages are installed through the selected provider, without detected duplicates, and declared minimum executable versions are met. Otherwise exit 1. This is not a general application health check or a reproducibility guarantee.
- **Update:** explicitly update selected installed applications. Missing applications require `install` first. Dependencies may also be upgraded. On Arch, native updates are refused: run `sudo pacman -Syu` separately, then check again. Native installs use `pacman -S --needed`, never a standalone database refresh; maintain the system before installing packages.
- **Provider changes / removals:** no automatic migration, uninstallation, cleanup or full system upgrade. Removing a manifest entry leaves installed software in place.

Minimum versions are checked against the selected provider's executable after real installs/updates and during `check`. A too-old distro candidate causes a failure with guidance; the tool does not automatically switch providers. Installing a package successfully does not guarantee it meets the declared version. No package transaction rollback is attempted on failure.

The old hand-maintained Brewfile has been replaced by this manifest. Export a generated Brewfile when useful:

```sh
# Only applications currently assigned to Homebrew:
./scripts/software.py export-brewfile > /tmp/dotfiles.Brewfile
# A full Homebrew selection for another workstation:
./scripts/software.py export-brewfile --provider brew > /tmp/dotfiles-all.Brewfile
```

## Bootstrap and runtime setup

`bootstrap.sh` wraps software installation and the independent dotfile installer:

```sh
./bootstrap.sh --dry-run
./bootstrap.sh --group core --software-only
./bootstrap.sh --force                # Delete conflicting configurations; no backups
./bootstrap.sh --update neovim uv     # Software updates only
./bootstrap.sh --skip-prerequisites   # Supply Homebrew prerequisites yourself
```

Native detection uses `ID` and `ID_LIKE` from `/etc/os-release`, not whichever package-manager executable happens to be on PATH. `--native-manager apt|dnf|pacman` overrides it. Unknown distro families require an explicit native adapter choice or an all-Homebrew selection. Immutable systems and special packaging environments may need manual setup.

Homebrew provisioning is isolated in `software/bootstrap.py`. It uses the same catalog/adapters to install native build prerequisites, downloads the [official installer](https://github.com/Homebrew/install), and runs it as the normal user. Existing Homebrew skips this step. `--skip-prerequisites` also permits provisioning on systems outside the native adapters if you supply the prerequisites and select only Homebrew applications. Direct `software.py install` does not provision Homebrew unless passed `--bootstrap-brew`.

Application installation does not initialize language runtimes. Run separately:

```sh
./scripts/toolchains.sh node   # Install current Node LTS through fnm
./scripts/toolchains.sh rust   # Install stable Rust plus editor components
./scripts/toolchains.sh        # Both
```

Existing Node/Rust defaults are preserved where the managers support this; Rust defaults to stable only when no default exists. This replaces the previous automatic runtime setup in bootstrap. `--update node` is no longer a package-manager alias: use fnm directly for a non-LTS Node release. Global npm packages are not copied between Node versions.

## Homebrew tradeoffs

Homebrew provides a convenient shared catalog and recent development tools across distro release cycles. It remains useful for explicit version-sensitive exceptions, or as an override for the entire software selection. Configuration installation does not require it.

Costs include duplicate distro/Homebrew tools, PATH precedence changes, additional dependency storage and a second update workflow. Its binary package and platform support depend on the host and installation prefix. A manifest of unversioned names is not a reproducible environment, and updates may affect dependencies beyond the requested application. See [Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux), [support tiers](https://docs.brew.sh/Support-Tiers), and the [Homebrew FAQ](https://docs.brew.sh/FAQ).

Keep services, drivers and system components under the distro package manager. These shells initialize Homebrew when available, potentially preferring its tools; use your final local shell hook to change PATH precedence.

## Machine-specific settings

- `~/.bashrc.local` and `~/.zshrc.local` load last. Put proxy settings, coursework paths, CUDA setup and other workstation settings here. No proxy is enabled by default.
- `~/.bash_profile.local` and `~/.zprofile.local` load early in Bash and Zsh, respectively. Use it for `TMUX_AUTOSTART=0`, since tmux starts before the final hook.
- Existing Miniconda, rbenv, fnm and Cargo integrations load when available. Activated environments can change tool precedence.
- Zsh plugins load from `~/.zsh`, Homebrew, or common distro package locations. Both shells initialize zoxide with `j` as the jump command when available.
- Select a Nerd Font for prompt/editor icons, or disable Neovim icons with `vim.g.have_nerd_font = false`.

For example, add only the settings you need to the shell's local file:

```sh
export NEMU_HOME="$HOME/Programing/PA/ics2024/nemu"
# Enable only if a proxy is running:
# export http_proxy=http://127.0.0.1:7897
# export https_proxy="$http_proxy"
# export all_proxy="$http_proxy"
```

This does not change your login shell. Vim plugins, Nerd Fonts, Miniconda, CUDA/drivers and GUI applications remain separate installations. For Neovim dependencies and first-run setup, see its [README](config/nvim/README.md).

## Repository layout

```text
bootstrap.sh             # Optional software setup, then configuration links
install.sh               # Configuration installer
software/
  manifest.toml          # Application groups and provider choices
  packages.toml          # Package-name mappings, including build prerequisites
  manager.py             # Detection, selection, status and transaction planning
  bootstrap.py           # Optional Homebrew provisioning
  adapters/              # apt, dnf, pacman, Homebrew
scripts/
  software.py            # Software CLI
  toolchains.sh          # Explicit Node/Rust runtime setup
  links.py               # Install, inspect, restore configuration links
  set_proxy.sh           # Opt-in proxy helper
config/                  # Shell/editor/prompt configuration and Git submodules
tests/                   # File-preservation and package-transaction safety tests
```

The linker uses fixed destinations under the selected home and does not consult `XDG_CONFIG_HOME`. It rejects symlinked destination parents rather than following them into another configuration tree. Configuration sources remain in this checkout; keep it in place.

| Source | Destination |
| --- | --- |
| `config/bash/.bashrc` | `~/.bashrc` |
| `config/zsh/.zshrc` | `~/.zshrc` |
| `config/vim/.vimrc` | `~/.vimrc` |
| `config/tmux/.tmux.conf` | `~/.tmux.conf` |
| `config/ai/codex/dotfiles.config.toml` | `~/.codex/dotfiles.config.toml` |
| `config/nvim/` | `~/.config/nvim` |
| `config/oh-my-posh/theme.omp.json` | `~/.config/oh-my-posh/theme.omp.json` |
| `config/cowsay/stegosaurus_and_cat.cow` | `~/.config/cowsay/stegosaurus_and_cat.cow` |

## Configuration scripts

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

Runs installer tests in temporary home directories and software safety tests with fake package managers; no packages are installed. Covers skipping conflicts by default, forced replacement without backups, repeated installation, restoration of older manifests, dry runs, changed-file protection, dangling links, and rejection of symlinked destination parents.

## Application configurations

### Bash

[`config/bash/.bashrc`](config/bash/.bashrc) provides a familiar shell for everyday command-line work and development. It builds on familiar Bash defaults, keeping established shell behavior while making development tools easier to access. The guiding principle is practical convenience through straightforward startup configuration. It matches Zsh’s prompt, tmux autostart, Emacs editing, shared history, `cx` and Git shortcuts, UV and Cargo helpers, zoxide jumps, and optional welcome message using Bash-compatible setup. Bash history is kept separately in `~/.bash_history`. Use `~/.bashrc.local` for workstation-specific paths and settings.

### Zsh

[`config/zsh/.zshrc`](config/zsh/.zshrc) configures the main interactive development shell. Its emphasis is on reducing friction during everyday terminal work and making language environments convenient to use. User-specific paths generally derive from `$HOME`, making the configuration easier to reuse across accounts. The overall approach is to keep environment setup in one place and load optional integrations conditionally where supported, with final machine-specific overrides in `~/.zshrc.local`.

### tmux

Interactive Bash and Zsh terminals automatically attach to a persistent `main` session before loading the rest of the shell configuration. After detaching or exiting tmux, the outer shell finishes loading normally. This skips terminals already inside tmux and VS Code terminals; set `TMUX_AUTOSTART=0` to disable it.

For machine-specific settings, create `~/.zprofile.local` (kept outside this repository):

```zsh
export TMUX_AUTOSTART=0  # Disable automatic tmux startup on this machine; use 1 to enable.
```

`.zshrc` sources this file before the tmux check, including in non-login shells. For Bash, put the same setting in `~/.bash_profile.local`; `.bashrc` loads it before its tmux check. Keep it limited to environment settings, since it also runs for shells inside tmux. Without a setting, tmux autostart defaults to enabled.

[`config/tmux/.tmux.conf`](config/tmux/.tmux.conf) provides persistent window, pane, and resize modes with Vim-style navigation, colored status badges, and Ctrl+h help in a scrollable popup. New windows and splits preserve the current directory. Alt navigation remains available to the desktop window manager, including GlazeWM. The configuration uses tmux's built-in key tables and pickers without a plugin framework; it requires tmux 3.2 or newer and `less`.

### AI agents

[`config/ai/`](config/ai/) contains shared AI agent configuration from [TenofHearts/ai-config](https://github.com/TenofHearts/ai-config), organized by agent. Its [`codex/`](config/ai/codex/) directory provides shared Codex CLI preferences with automatic approval review, Vim input mode, and a status bar showing model, project, context, and usage limits. It is maintained in a separate Git submodule. Bash and Zsh load the profile through the `codex` alias. Machine-specific settings remain in `~/.codex/config.toml`, with shared profile values taking precedence.

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

For AI agent, Neovim, or tmux changes, commit and push inside `config/ai`, `config/nvim`, or `config/tmux` first, then commit the updated submodule reference in this repository. See their READMEs for setup and syncing instructions.

To bring an existing checkout to its committed submodule revision after pulling:

```sh
git pull
git submodule update --init --recursive
```

The parent repository pins specific Codex, Neovim, and tmux commits; updating to a different submodule revision is a deliberate change.
