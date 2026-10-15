#!/usr/bin/env bash
# Install/update personal software, then reuse the existing dotfiles installer.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
dry_run=0
links=1
update=0
formulae=()

usage() {
    cat <<'EOF'
Usage: ./bootstrap.sh [--dry-run] [--software-only]
       ./bootstrap.sh [--dry-run] --update [FORMULA ...]

Default: install Homebrew if needed, install/upgrade Brewfile software,
install Node LTS through fnm and stable Rust with editor components, and install dotfile links.
--software-only  Skip dotfile links.
--update         Update software only; optional formula names select individual apps.
--dry-run        Print commands without downloads, installs, or filesystem changes.

Examples:
  ./bootstrap.sh
  ./bootstrap.sh --update
  ./bootstrap.sh --update neovim uv
  ./bootstrap.sh --update node  # Latest Node release through fnm (keeps your default)
EOF
}

while (($#)); do
    case "$1" in
        --dry-run) dry_run=1 ;;
        --software-only) links=0 ;;
        --update) update=1; links=0 ;;
        -h|--help) usage; exit 0 ;;
        -*) echo "Unknown option: $1" >&2; exit 2 ;;
        *) formulae+=("$1") ;;
    esac
    shift
done
if ((${#formulae[@]})) && (( ! update )); then
    echo "Formula names require --update." >&2
    exit 2
fi
for formula in "${formulae[@]}"; do
    if [[ ! "$formula" =~ ^[a-zA-Z0-9][a-zA-Z0-9@+._/-]*$ ]]; then
        echo "Invalid formula name: $formula" >&2
        exit 2
    fi
done

run() {
    printf '+ '; printf '%q ' "$@"; printf '\n'
    if (( ! dry_run )); then "$@"; fi
}

if [[ "$(uname -s)" != Linux ]] || ! command -v apt-get >/dev/null 2>&1; then
    echo "This bootstrap supports Ubuntu/Debian Linux (including WSL2)." >&2
    exit 1
fi
if (( EUID == 0 && ! dry_run )); then
    echo "Run as your normal user. Homebrew requests sudo when needed." >&2
    exit 1
fi

# Locate Homebrew even before the user's shell has loaded its environment.
brew_bin="$(command -v brew || true)"
if [[ -z "$brew_bin" ]]; then
    for candidate in /home/linuxbrew/.linuxbrew/bin/brew "$HOME/.linuxbrew/bin/brew"; do
        if [[ -x "$candidate" ]]; then brew_bin="$candidate"; break; fi
    done
fi
if [[ -z "$brew_bin" ]] || (( links )); then
    run sudo apt-get update
    run sudo apt-get install -y build-essential procps curl file git ca-certificates
fi
if [[ -z "$brew_bin" ]]; then
    if (( dry_run )); then
        echo '+ Download and run https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh with Bash'
        brew_bin=brew
    else
        command -v curl >/dev/null || { echo "Install curl first." >&2; exit 1; }
        installer="$(mktemp)"
        trap 'rm -f "$installer"' EXIT
        curl --fail --show-error --location https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$installer"
        bash "$installer"
        for candidate in /home/linuxbrew/.linuxbrew/bin/brew "$HOME/.linuxbrew/bin/brew"; do
            if [[ -x "$candidate" ]]; then brew_bin="$candidate"; break; fi
        done
        [[ -n "$brew_bin" ]] || { echo "Homebrew was not found after installation." >&2; exit 1; }
    fi
fi
if (( ! dry_run )); then
    eval "$("$brew_bin" shellenv)"
fi
run "$brew_bin" update
if ((${#formulae[@]})); then
    for formula in "${formulae[@]}"; do
        if [[ "$formula" == node ]]; then
            # Keep Node under fnm, even for a single-app update.
            if (( dry_run )); then
                echo '+ Install or upgrade Homebrew formula: fnm'
                run fnm install --latest
            else
                if "$brew_bin" list --formula --versions fnm >/dev/null 2>&1; then
                    run "$brew_bin" upgrade --formula fnm
                else
                    run "$brew_bin" install --formula fnm
                fi
                run "$("$brew_bin" --prefix)/bin/fnm" install --latest
            fi
        elif (( dry_run )); then
            printf '+ Install or upgrade Homebrew formula: %s\n' "$formula"
        elif "$brew_bin" list --formula --versions "$formula" >/dev/null 2>&1; then
            run "$brew_bin" upgrade --formula "$formula"
        else
            run "$brew_bin" install --formula "$formula"
        fi
    done
else
    run "$brew_bin" bundle upgrade --file="$ROOT/Brewfile"
    # Use Homebrew's fnm binary even when an older standalone copy exists.
    if (( dry_run )); then
        run fnm install --lts
    else
        run "$("$brew_bin" --prefix)/bin/fnm" install --lts
    fi
    # rustup is keg-only; its bin directory also contains the toolchain proxies.
    if (( dry_run )); then
        rustup_bin=rustup
    else
        rustup_bin="$("$brew_bin" --prefix rustup)/bin/rustup"
    fi
    run "$rustup_bin" toolchain install stable --profile minimal
    run "$rustup_bin" component add --toolchain stable rust-analyzer rust-src rustfmt clippy
    if (( dry_run )); then
        echo '+ Set Rust default to stable only if no default is configured'
    elif ! "$rustup_bin" default >/dev/null 2>&1; then
        run "$rustup_bin" default stable
    fi
    if (( links )); then run "$ROOT/install.sh"; fi
fi
echo 'Done. Open a new shell to load the installed tools.'
