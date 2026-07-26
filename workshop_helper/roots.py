"""Root tiers and their names (spec §2.5).

An Applet belongs to exactly one Root, which is its provenance. The tiers are
**structural, not declared** — own, then the wheel's built-in Root, then each
foreign path in ``config.toml`` order. That order *is* #8's precedence rule.

Root names are display strings only; nothing keys off them. The spec fixes the
tier names by using them in prose ("Root 'X'"), but leaves foreign naming open,
so: a foreign Root is named by its folder, except when that folder carries the
convention name ``applets`` (§2.4), where the folder above it names the
collection — which is what makes ``~/src/mate-collection/applets`` read as
Root 'mate-collection' in §10.3's blame line.
"""

from dataclasses import dataclass
from pathlib import Path

APPLETS_DIRNAME = "applets"
BUILTIN_ROOT_PATH = Path(__file__).parent / APPLETS_DIRNAME
OWN_ROOT_NAME = "own"
BUILTIN_ROOT_NAME = "built-in"


@dataclass(frozen=True)
class Root:
    """A directory the Host scans for Applets.

    ``is_own`` marks the user's own Root, which the shell UI badges inline
    (spec §9). It is display-only; filtering stays global.
    """

    name: str
    path: Path
    is_own: bool = False


def foreign_root_name(path: Path) -> str:
    """Name a foreign Root from its path, seeing through an ``applets`` folder."""
    if path.name == APPLETS_DIRNAME and path.parent.name:
        return path.parent.name
    return path.name


def resolve_roots(home: Path, config_roots: list[Path]) -> list[Root]:
    """Assemble every Root in tier order: own, built-in, then foreigns.

    Paths are returned whether or not they exist — a missing Root is skipped at
    scan time, not here (spec §2.5).
    """
    return [
        Root(name=OWN_ROOT_NAME, path=home / APPLETS_DIRNAME, is_own=True),
        Root(name=BUILTIN_ROOT_NAME, path=BUILTIN_ROOT_PATH),
        *(Root(name=foreign_root_name(path), path=path) for path in config_roots),
    ]
