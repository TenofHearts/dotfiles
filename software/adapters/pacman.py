from .base import Adapter


class Pacman(Adapter):
    executable = "pacman"

    def installed(self, package):
        return self.runner.query([self.executable, "-Q", package]).returncode == 0

    def commands(self, action, packages):
        if action == "update":
            raise RuntimeError("Arch does not support partial upgrades. Run sudo pacman -Syu "
                               "separately, then rerun software check.")
        # Never refresh databases alone (-Sy). The user maintains system updates.
        return [self.privileged([self.executable, "-S", "--needed"] + packages)]
