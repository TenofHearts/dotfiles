# Linux dotfiles

Organized like [dotfiles-apple](https://github.com/TenofHearts/dotfiles-apple):
application configuration lives in `config/`, and setup helpers live in
`scripts/`. Existing Linux settings, aliases, and development paths are retained.

```text
config/
  bash/.bashrc
  zsh/.zshrc
  vim/.vimrc
  tmux/.tmux.conf
  oh-my-posh/theme.omp.json
  cowsay/stegosaurus_and_cat.cow
scripts/
  links.py
  set_proxy.sh
install.sh
tests/
```

The old root paths are compatibility symlinks. Existing home-directory links
through those paths continue to work; edit the files under `config/`.
Prompt and cowsay settings use installed resources under `~/.config/`,
with a fallback to this checkout before installation.

## Install

Requires Python 3 and Bash. Preview changes, then install:

```sh
./install.sh --dry-run
./install.sh
python3 scripts/links.py status
```

The installer links Bash, Zsh, Vim, tmux, the prompt theme, and cowsay artwork.
It does not install packages. Existing files (including dangling symlinks) are
backed up under `~/.local/state/dotfiles/backups/<timestamp>/`.
Repeated installation leaves correct links alone. Symlinked destination parent
directories require manual resolution before installation.

Restore using the manifest path printed by the installer:

```sh
python3 scripts/links.py restore /path/to/manifest.json --dry-run
python3 scripts/links.py restore /path/to/manifest.json
```

Restoration refuses to overwrite files changed after installation.
Use `--home /tmp/example-home` for an isolated install or status check.
The installer uses `~/.config` for resources, matching the shell configs.
Your existing Linux setup still assumes optional tools such as Conda, rbenv,
fnm, uv, and Rust, and Zsh exports proxy settings for port 7897.

## Proxy helper

Source the helper to apply its exports in the current shell:

```sh
source scripts/set_proxy.sh
```

It obtains the proxy host from `/etc/resolv.conf` for the existing WSL-style setup.

## Validation

```sh
python3 -m unittest discover -s tests
bash -n install.sh config/bash/.bashrc
zsh -n config/zsh/.zshrc scripts/set_proxy.sh
```
