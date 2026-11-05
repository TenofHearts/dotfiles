#!/usr/bin/env bash
# Optional software setup followed by independent configuration installation.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
action=install
links=1
dry_run=0
force=0
software_args=()

usage() {
    cat <<'HELP'
Usage: ./bootstrap.sh [--dry-run] [--software-only] [--force]
                      [--group GROUP] [--provider native|brew]
                      [--native-manager apt|dnf|pacman] [--skip-prerequisites]
       ./bootstrap.sh --update [APP ...] [--dry-run] [--group GROUP]

Install software from software/manifest.toml, provisioning Homebrew only when
selected and missing, then install configuration links (skip conflicts).
--software-only  Skip configuration links.
--force          Delete conflicting configurations when linking (no backups).
--update         Update selected installed applications; skip configuration links.
--dry-run        Preview without downloads, package transactions, or link changes.

Use ./scripts/software.py --help for software commands. Runtime setup is separate:
./scripts/toolchains.sh [all|node|rust] [--dry-run]
HELP
}

while (($#)); do
    case "$1" in
        --software-only) links=0; shift ;;
        --force) force=1; shift ;;
        --update) action=update; links=0; shift ;;
        --dry-run) dry_run=1; software_args+=("$1"); shift ;;
        --skip-prerequisites) software_args+=("$1"); shift ;;
        --group|--provider|--native-manager)
            (($# >= 2)) || { echo "Missing value for $1" >&2; exit 2; }
            software_args+=("$1" "$2"); shift 2 ;;
        --group=*|--provider=*|--native-manager=*) software_args+=("$1"); shift ;;
        -h|--help) usage; exit 0 ;;
        -*) echo "Unknown option: $1" >&2; exit 2 ;;
        *) software_args+=("$1"); shift ;;
    esac
done
if [[ "$(uname -s)" != Linux ]]; then
    echo 'This bootstrap supports Linux (including WSL2).' >&2
    exit 1
fi
if [[ "$action" == install ]]; then software_args+=(--bootstrap-brew); fi
python3 "$ROOT/scripts/software.py" "$action" "${software_args[@]}"
if (( links )); then
    link_args=()
    (( ! force )) || link_args+=(--force)
    (( ! dry_run )) || link_args+=(--dry-run)
    "$ROOT/install.sh" "${link_args[@]}"
fi
