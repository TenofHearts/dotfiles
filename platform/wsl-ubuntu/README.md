# WSL Ubuntu

Inside Ubuntu on WSL2, run these commands as your normal user from the repository root. Bootstrap requires Bash, Git, and Python 3.11+ (or 3.8+ with `tomli`).

```sh
./platform/wsl-ubuntu/check.sh   # Confirm this is Ubuntu under WSL
./bootstrap.sh --dry-run         # Preview package installation and configuration links
./bootstrap.sh
```

Bootstrap installs the [WSL packages](../../software/manifests/wsl-ubuntu.toml) using apt and Homebrew. Open a new shell to use the linked configuration. Keep machine-specific settings such as proxy variables in `~/.zshrc.local` or `~/.bashrc.local`.
