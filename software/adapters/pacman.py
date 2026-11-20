import os

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


class Aur(Adapter):
    executable = "paru"

    def commands(self, action, packages):
        if action == "update":
            raise RuntimeError("Update Arch and AUR packages together with paru -Syu separately.")
        if not self.runner.dry_run and os.geteuid() == 0:
            raise RuntimeError("Run AUR builds as your normal user.")
        return [[self.executable, "-S", "--aur", "--needed"] + packages]
