"""Optional Homebrew provisioning; normal software commands require existing managers."""
from pathlib import Path
import os
import tempfile
import urllib.request

from .adapters import find_brew
from .manager import adapters, inspect, transaction_commands

INSTALLER = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"


def provision_brew(catalog, runner, native, skip_prerequisites=False):
    if not runner.dry_run and os.geteuid() == 0:
        raise RuntimeError("Install Homebrew as your normal user; its installer requests sudo when needed.")
    if not skip_prerequisites:
        prerequisites = catalog.select(
            ["build-tools", "procps", "curl", "file", "git", "ca-certificates"],
            provider="native", native=native)
        backends = adapters(runner, native)
        rows = inspect(catalog, prerequisites, backends, native)
        for command in transaction_commands(rows, "install", backends):
            runner.run(command)
    print("Download Homebrew installer: " + INSTALLER, flush=True)
    if runner.dry_run:
        print("+ bash <downloaded Homebrew installer>")
        return None
    with tempfile.TemporaryDirectory(prefix="dotfiles-brew-") as directory:
        path = Path(directory) / "install.sh"
        with urllib.request.urlopen(INSTALLER, timeout=60) as response:
            path.write_bytes(response.read())
        runner.run(["bash", str(path)])
    found = find_brew()
    if not found:
        raise RuntimeError("Homebrew was not found after installation. Follow the installer's next steps.")
    return found
