#!/usr/bin/env python3
"""Add missing Fcitx5 Rime Ice runtime files from the pinned macOS baseline."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

REVISION = "3aea6d3694fb3d94ec663641f021f788822897ad"
URL = "https://github.com/iDvel/rime-ice.git"
DATA = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
TARGET = DATA / "fcitx5/rime"


def runtime_file(path):
    if len(path.parts) > 1:
        return path.parts[0] in {"cn_dicts", "en_dicts", "lua", "opencc"}
    return (path.name in {"default.yaml", "custom_phrase.txt"}
            or path.name.endswith((".schema.yaml", ".dict.yaml"))
            or path.match("symbols_*.yaml"))


def main():
    with tempfile.TemporaryDirectory(prefix="dotfiles-rime-") as tmp:
        repo = Path(tmp)
        def git(*args, **kwargs):
            return subprocess.run(["git", "-C", tmp, *args], check=True, **kwargs)

        git("init", "-q")
        git("fetch", "-q", "--depth=1", URL, REVISION)
        revision = git("rev-parse", "FETCH_HEAD", capture_output=True, text=True).stdout.strip()
        if revision != REVISION:
            raise SystemExit("Rime Ice revision mismatch")
        git("checkout", "-q", "--detach", REVISION)
        paths = [Path(os.fsdecode(name)) for name in
                 git("ls-files", "-z", capture_output=True).stdout.split(b"\0") if name]
        files = [path for path in paths if runtime_file(path)]
        for path in files:
            if (repo / path).is_symlink():
                raise SystemExit(f"Unexpected symlink in Rime Ice: {path}")
            for directory in (TARGET / path).parents:
                if directory == DATA:
                    break
                if directory.is_symlink():
                    raise SystemExit(f"Symlinked data directory needs manual review: {directory}")

        added = 0
        for path in files:
            dest = TARGET / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            if os.path.lexists(dest):
                continue
            # Publish only complete files. link() also refuses to replace a race winner.
            with tempfile.NamedTemporaryFile(dir=dest.parent) as staged:
                with (repo / path).open("rb") as source:
                    shutil.copyfileobj(source, staged)
                staged.flush()
                try:
                    os.link(staged.name, dest)
                    added += 1
                except FileExistsError:
                    pass
        print(f"Rime Ice {REVISION}: added {added}, kept {len(files) - added} at {TARGET}")


if __name__ == "__main__":
    main()
