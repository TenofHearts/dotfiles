from .base import Adapter


class Dnf(Adapter):
    executable = "dnf"

    def installed(self, package):
        return self.runner.query(["rpm", "-q", package]).returncode == 0

    def commands(self, action, packages):
        verb = "upgrade" if action == "update" else "install"
        return [self.privileged([self.executable, verb] + packages)]
