"""Resolve declarative application IDs before executing any package transactions."""
from collections import defaultdict
from pathlib import Path
import json
import re
import shlex

from .adapters import ADAPTERS, find_brew

PROVIDERS = ("native", "brew")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+._@/-]*$")


def read_toml(path):
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            raise RuntimeError("Software management requires Python 3.11+, or Python 3.8+ "
                               "with tomli installed. Dotfile linking has no TOML dependency.") from None
    with path.open("rb") as stream:
        return tomllib.load(stream)


def native_manager(path=Path("/etc/os-release")):
    values = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            parts = shlex.split(value)
            values[key] = " ".join(parts)
    identities = [values.get("ID", "")] + values.get("ID_LIKE", "").split()
    for identity in identities:
        if identity in ("debian", "ubuntu", "linuxmint", "pop"):
            return "apt"
        if identity in ("fedora", "rhel", "centos", "rocky", "almalinux"):
            return "dnf"
        if identity in ("arch", "manjaro", "endeavouros"):
            return "pacman"
    return None


class Catalog:
    def __init__(self, manifest, packages):
        self.manifest = manifest
        self.packages = packages["packages"]
        self.groups = manifest["groups"]
        self.settings = manifest.get("software", {})
        self.default = manifest.get("defaults", {}).get("provider", "native")
        for name, settings in self.settings.items():
            minimum = settings.get("minimum_version")
            if minimum and not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", minimum):
                raise ValueError("Invalid minimum_version for " + name)
            if minimum and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", settings.get("command", name)):
                raise ValueError("Invalid version command for " + name)
        if self.default not in PROVIDERS:
            raise ValueError("Default provider must be native or brew")

    def select(self, names=(), groups=(), provider=None, native=None):
        selected = list(names)
        if not names and not groups:
            groups = self.manifest.get("defaults", {}).get("groups", list(self.groups))
        for group in groups:
            if group not in self.groups:
                raise ValueError("Unknown software group: " + group)
            selected.extend(self.groups[group])
        result = []
        for name in dict.fromkeys(selected):
            if name not in self.packages:
                raise ValueError("Unknown application: " + name)
            chosen = provider or self.settings.get(name, {}).get("provider", self.default)
            if chosen not in PROVIDERS:
                raise ValueError("Unknown provider for " + name + ": " + str(chosen))
            manager = native if chosen == "native" else "brew"
            if not manager:
                raise ValueError("Unknown native package manager. Use --native-manager or --provider brew.")
            result.append((name, manager, self.resolve(name, manager)))
        return result

    def resolve(self, name, manager):
        mapping = self.packages[name]
        packages = mapping.get(manager, mapping.get("default"))
        if not isinstance(packages, list) or not packages:
            raise ValueError("No {} mapping for {}. Add an explicit mapping or select another provider."
                             .format(manager, name))
        if any(not isinstance(p, str) or not NAME.fullmatch(p) for p in packages):
            raise ValueError("Invalid package name in mapping for " + name)
        return packages

    def brewfile(self, selection):
        packages = dict.fromkeys(p for _, manager, values in selection if manager == "brew" for p in values)
        return "# Generated from software/manifest.toml and software/packages.toml.\n" + "".join(
            "brew " + json.dumps(package) + "\n" for package in packages)


def adapters(runner, native):
    result = {"brew": ADAPTERS["brew"](runner, find_brew())}
    if native:
        result[native] = ADAPTERS[native](runner)
    return result


def inspect(catalog, selection, backends, native):
    """Read only package databases. Cache shared package queries within the plan."""
    cache = {}

    def installed(manager, package):
        key = (manager, package)
        if key not in cache:
            backend = backends[manager]
            cache[key] = backend.available() and backend.installed(package)
        return cache[key]

    rows = []
    for name, manager, packages in selection:
        missing = [p for p in packages if not installed(manager, p)]
        other = native if manager == "brew" else "brew"
        conflicts = []
        if other and backends[other].available():
            mapping = catalog.packages[name]
            other_packages = mapping.get(other, mapping.get("default", []))
            conflicts = [p for p in other_packages if installed(other, p)]
        rows.append(dict(name=name, manager=manager, packages=packages,
                         missing=missing, other=other, conflicts=conflicts))
    return rows


def display(rows):
    for row in rows:
        status = "MISSING" if row["missing"] else "OK"
        detail = ""
        if row["conflicts"]:
            status = "CONFLICT"
            detail = " (also installed through {}: {})".format(row["other"], ", ".join(row["conflicts"]))
        print("{} {} [{}: {}]{}".format(status, row["name"], row["manager"],
                                       ", ".join(row["packages"]), detail))


def transaction_commands(rows, action, backends, allow_missing_brew=False):
    # Fail the entire plan before any writes if a provider conflict or unsupported
    # operation exists. Native/Brew installs are never silently migrated.
    conflicts = [r["name"] for r in rows if r["conflicts"]]
    if conflicts:
        raise RuntimeError("Provider conflicts: {}. Keep the existing provider in the manifest, "
                           "or remove its packages yourself before switching.".format(", ".join(conflicts)))
    grouped = defaultdict(list)
    for row in rows:
        if action == "update" and row["missing"]:
            raise RuntimeError(row["name"] + " is missing; run install first")
        grouped[row["manager"]].extend(row["packages"] if action == "update" else row["missing"])
    commands = []
    for manager, packages in grouped.items():
        if not packages:
            continue
        backend = backends[manager]
        if not backend.available() and not backend.runner.dry_run and not (manager == "brew" and allow_missing_brew):
            hint = " Run ./bootstrap.sh to install Homebrew first." if manager == "brew" else ""
            raise RuntimeError("Package manager is unavailable: " + manager + "." + hint)
        commands.extend(backend.commands(action, list(dict.fromkeys(packages))))
    return commands


def version_problems(catalog, rows, backends):
    problems = []
    for row in rows:
        settings = catalog.settings.get(row["name"], {})
        minimum = settings.get("minimum_version")
        if not minimum or row["missing"]:
            continue
        command = settings.get("command", row["name"])
        if row["manager"] == "brew":
            # Check the selected provider's binary even if PATH prefers another.
            result = backends["brew"].runner.query([backends["brew"].executable, "--prefix"])
            if result.returncode:
                raise RuntimeError("Unable to locate Homebrew prefix")
            executable = str(Path(result.stdout.strip()) / "bin" / command)
        else:
            executable = str(Path("/usr/bin") / command)
        if not Path(executable).is_file():
            problems.append(row["name"] + ": executable missing: " + executable)
            continue
        result = backends[row["manager"]].runner.query([executable, "--version"])
        match = re.search(r"(?<![\d.])(\d+)\.(\d+)(?:\.(\d+))?", result.stdout)
        required = tuple(int(part) for part in minimum.split("."))
        actual = tuple(int(part or 0) for part in match.groups()) if match else ()
        if result.returncode or not match or actual < required:
            problems.append("{} requires >= {}; selected provider reports {}. Update it or choose "
                            "another provider.".format(row["name"], minimum, match.group(0) if match else "unknown"))
    return problems
