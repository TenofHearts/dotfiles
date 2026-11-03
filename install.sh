#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
only=""
read_only=0
for arg in "$@"; do
    if [[ "$read_only" == 1 ]]; then
        only="$arg"
        read_only=0
    else
        case "$arg" in
            --only) read_only=1 ;;
            --only=*) only="${arg#--only=}" ;;
        esac
    fi
done
if [[ " $* " != *" --dry-run "* ]]; then
    case "$only" in
        "") git -C "$ROOT" submodule update --init --recursive ;;
        codex|nvim|tmux) git -C "$ROOT" submodule update --init --recursive -- "config/$only" ;;
    esac
fi
exec python3 "$ROOT/scripts/links.py" install "$@"
