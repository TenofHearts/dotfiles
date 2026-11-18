#!/usr/bin/env bash
# Validate the platform currently supported by the bootstrap entry point.
set -euo pipefail

if [[ "$(uname -s)" != Linux ]]; then
    echo 'Supported platform: Ubuntu under WSL2.' >&2
    exit 1
fi

if [[ ! -r /proc/sys/kernel/osrelease ]] || ! grep -Eiq 'microsoft|wsl' /proc/sys/kernel/osrelease; then
    echo 'This bootstrap currently supports Ubuntu under WSL2 only.' >&2
    exit 1
fi

if [[ ! -r /etc/os-release ]]; then
    echo 'Cannot identify the Linux distribution: /etc/os-release is missing.' >&2
    exit 1
fi

. /etc/os-release
if [[ "${ID:-}" != ubuntu ]]; then
    echo "This bootstrap currently supports Ubuntu under WSL2 only (detected: ${ID:-unknown})." >&2
    exit 1
fi
