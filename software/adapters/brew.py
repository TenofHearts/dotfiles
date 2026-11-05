from pathlib import Path
import shutil
from .base import Adapter


def find_brew():
    found = shutil.which("brew")
    if found:
        return found
    for path in (Path("/home/linuxbrew/.linuxbrew/bin/brew"),
                 Path.home() / ".linuxbrew/bin/brew"):
        if path.is_file() and path.stat().st_mode & 0o111:
            return str(path)
    return None


class Brew(Adapter):
    executable = "brew"

    def installed(self, package):
        if not self.available():
            return False
        result = self.runner.query([self.executable, "list", "--formula", "--versions", package])
        return result.returncode == 0 and bool(result.stdout.strip())

    def commands(self, action, packages):
        if action == "update":
            return [[self.executable, "update"], [self.executable, "upgrade", "--formula"] + packages]
        return [[self.executable, "install", "--formula"] + packages]
