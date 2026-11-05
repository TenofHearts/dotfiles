"""Command execution and the small package-manager interface."""
import os
import shlex
import shutil
import subprocess


class Runner:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.env = dict(os.environ, HOMEBREW_NO_AUTO_UPDATE="1",
                        HOMEBREW_NO_INSTALL_UPGRADE="1")

    def query(self, args):
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=self.env)
        if result.returncode not in (0, 1):
            raise RuntimeError("Query failed: {}\n{}".format(shlex.join(args), result.stderr.strip()))
        return result

    def run(self, args):
        print("+ " + shlex.join(args), flush=True)
        if not self.dry_run:
            subprocess.run(args, check=True, env=self.env)


class Adapter:
    executable = ""

    def __init__(self, runner, executable=None):
        self.runner = runner
        self.executable = executable or self.executable

    def available(self):
        return shutil.which(self.executable) is not None

    def installed(self, package):
        raise NotImplementedError

    def commands(self, action, packages):
        raise NotImplementedError

    def privileged(self, args):
        return args if os.geteuid() == 0 else ["sudo"] + args
