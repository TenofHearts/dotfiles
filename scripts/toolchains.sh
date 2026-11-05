#!/usr/bin/env bash
# Explicit runtime setup, independent of the application/package manifest.
set -euo pipefail
selection=all
dry_run=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) dry_run=1 ;;
        all|node|rust) selection="$arg" ;;
        -h|--help) echo 'Usage: ./scripts/toolchains.sh [all|node|rust] [--dry-run]'; exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 2 ;;
    esac
done
run() {
    printf '+ '; printf '%q ' "$@"; printf '\n'
    if (( ! dry_run )); then "$@"; fi
}
# Prefer the same Homebrew tools as the shared shells, when installed.
if ! command -v brew >/dev/null 2>&1; then
    for candidate in /home/linuxbrew/.linuxbrew/bin/brew "$HOME/.linuxbrew/bin/brew"; do
        if [[ -x "$candidate" ]]; then eval "$("$candidate" shellenv)"; break; fi
    done
fi
if command -v brew >/dev/null 2>&1; then
    eval "$(brew shellenv)"
    if [[ -x "$HOMEBREW_PREFIX/opt/rustup/bin/rustup" ]]; then
        export PATH="$HOMEBREW_PREFIX/opt/rustup/bin:$PATH"
    fi
fi
if [[ "$selection" == all || "$selection" == node ]]; then
    (( dry_run )) || command -v fnm >/dev/null || { echo 'Install fnm first.' >&2; exit 1; }
    run fnm install --lts
fi
if [[ "$selection" == all || "$selection" == rust ]]; then
    (( dry_run )) || command -v rustup >/dev/null || { echo 'Install rustup first.' >&2; exit 1; }
    run rustup toolchain install stable --profile minimal
    run rustup component add --toolchain stable rust-analyzer rust-src rustfmt clippy
    if (( dry_run )); then
        echo '+ Set Rust default to stable only if no default is configured'
    elif ! rustup default >/dev/null 2>&1; then
        run rustup default stable
    fi
fi
