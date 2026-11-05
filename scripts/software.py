#!/usr/bin/env python3
"""Manage selected applications through native packages or Homebrew."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from software.adapters.base import Runner
from software.bootstrap import provision_brew
from software.manager import (Catalog, adapters, display, inspect, native_manager,
                              read_toml, transaction_commands, version_problems)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "install", "check", "update", "export-brewfile"))
    parser.add_argument("names", nargs="*", help="Application IDs from the catalog")
    parser.add_argument("--group", action="append", default=[], help="Select a group; repeatable")
    parser.add_argument("--provider", choices=("native", "brew"), help="Override manifest providers")
    parser.add_argument("--native-manager", choices=("apt", "dnf", "pacman"), help="Override /etc/os-release detection")
    parser.add_argument("--dry-run", action="store_true", help="Print transactions without executing them")
    parser.add_argument("--bootstrap-brew", action="store_true", help="Install Homebrew if selected and missing (install/plan only)")
    parser.add_argument("--skip-prerequisites", action="store_true", help="Manage Homebrew prerequisites yourself")
    args = parser.parse_args()
    if args.bootstrap_brew and args.action not in ("install", "plan"):
        parser.error("--bootstrap-brew applies only to install and plan")
    catalog = Catalog(read_toml(ROOT / "software/manifest.toml"), read_toml(ROOT / "software/packages.toml"))
    native = args.native_manager or native_manager()
    selection = catalog.select(args.names, args.group, args.provider, native)
    if args.action == "export-brewfile":
        print(catalog.brewfile(selection), end="")
        return 0
    runner = Runner(args.dry_run or args.action == "plan")
    backends = adapters(runner, native)
    rows = inspect(catalog, selection, backends, native)
    display(rows)
    if args.action == "check":
        problems = version_problems(catalog, rows, backends)
        for problem in problems:
            print(problem, file=sys.stderr)
        return int(bool(problems) or any(r["missing"] or r["conflicts"] for r in rows))
    action = "install" if args.action == "plan" else args.action
    commands = transaction_commands(rows, action, backends, args.bootstrap_brew)
    if commands and not runner.dry_run and os.geteuid() == 0 and any(r["manager"] == "brew" for r in rows):
        raise RuntimeError("Run Homebrew operations as your normal user.")
    if args.bootstrap_brew and any(r["manager"] == "brew" for r in rows) and not backends["brew"].available():
        provision_brew(catalog, runner, native, args.skip_prerequisites)
        backends = adapters(runner, native)
        rows = inspect(catalog, selection, backends, native)
        commands = transaction_commands(rows, action, backends)
    for command in commands:
        runner.run(command)
    if not runner.dry_run:
        if commands:
            rows = inspect(catalog, selection, backends, native)
            display(rows)
        problems = version_problems(catalog, rows, backends)
        for problem in problems:
            print(problem, file=sys.stderr)
        return int(bool(problems) or any(r["missing"] or r["conflicts"] for r in rows))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
