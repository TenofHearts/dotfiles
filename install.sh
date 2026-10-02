#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [[ " $* " != *" --dry-run "* ]]; then
    git -C "$ROOT" submodule update --init --recursive
fi
exec python3 "$ROOT/scripts/links.py" install "$@"
