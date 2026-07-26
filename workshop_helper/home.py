"""Host home directory and configuration (spec §2.4).

One folder, no XDG split: ``~/.workshop-helper/`` unless ``WORKSHOP_HELPER_HOME``
overrides it. ``config.toml`` is hand-authored and read-only to the Host; it owns
exactly one thing — the ordered list of *foreign* Root paths. TOML is read with
the stdlib ``tomllib`` by construction (``tomlkit`` is not a dependency).
"""

import os
import tomllib
from collections.abc import Mapping
from pathlib import Path

HOME_ENV_VAR = "WORKSHOP_HELPER_HOME"
DEFAULT_HOME = Path("~/.workshop-helper")
CONFIG_FILENAME = "config.toml"


def resolve_home(env: Mapping[str, str] | None = None) -> Path:
    """Resolve the Host home directory, honouring ``WORKSHOP_HELPER_HOME``."""
    env = os.environ if env is None else env
    override = env.get(HOME_ENV_VAR)
    home = Path(override) if override else DEFAULT_HOME
    return home.expanduser()


def load_config_roots(home: Path) -> list[Path]:
    """Read the foreign Root paths from ``config.toml``.

    A missing ``config.toml`` — or one without a ``roots`` key — yields an empty
    list, not an error. Paths keep config order and are ``~``-expanded.
    """
    config_path = home / CONFIG_FILENAME
    if not config_path.is_file():
        return []
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)
    roots = config.get("roots", [])
    return [Path(root).expanduser() for root in roots]
