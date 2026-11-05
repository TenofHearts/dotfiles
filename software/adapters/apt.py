from .base import Adapter


class Apt(Adapter):
    executable = "apt-get"

    def installed(self, package):
        result = self.runner.query(["dpkg-query", "-W", "-f=${db:Status-Status}", package])
        return result.returncode == 0 and result.stdout.strip() == "installed"

    def commands(self, action, packages):
        args = [self.executable, "install"]
        if action == "update":
            args += ["--only-upgrade"]
        return [self.privileged([self.executable, "update"]),
                self.privileged(args + packages)]
