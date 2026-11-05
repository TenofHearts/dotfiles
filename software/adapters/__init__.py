from .apt import Apt
from .dnf import Dnf
from .pacman import Pacman
from .brew import Brew, find_brew

ADAPTERS = {"apt": Apt, "dnf": Dnf, "pacman": Pacman, "brew": Brew}
