# WSL Ubuntu

This is the platform currently supported by `bootstrap.sh`.

The platform guard intentionally keeps environment detection separate from Linux distribution detection:

- WSL is detected from the kernel release.
- Ubuntu is detected from `/etc/os-release`.
- Native software provisioning selects the `apt` adapter.

Platform-specific settings such as proxy variables remain in `~/.zshrc.local` or `~/.bashrc.local`. Nothing in this directory is sourced automatically by the shared shell configuration.
