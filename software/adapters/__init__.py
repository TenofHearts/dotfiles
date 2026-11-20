from .apt import Apt
from .dnf import Dnf
from .pacman import Aur, Pacman
from .brew import Brew, find_brew

ADAPTERS = {"apt": Apt, "dnf": Dnf, "pacman": Pacman, "aur": Aur, "brew": Brew}
