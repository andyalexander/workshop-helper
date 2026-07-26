"""The Manifest's `[applet]` section (spec §4.1).

``manifest.toml`` is the author's file and the Host only ever reads it
(ADR-0007), with the stdlib's ``tomllib`` — which cannot write TOML, so the
read-only rule holds by construction.

Every failure here is one fault: the Manifest did not yield metadata. It is
raised as :class:`ManifestError` carrying a human-readable reason, and the
caller decides what that means. Turning reasons into greyed cards is #33.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path

MANIFEST_FILENAME = "manifest.toml"
DOCUMENTATION = "documentation"
CALCULATOR = "calculator"
# Closed set: adding a type is a change to the Host (ADR-0005, spec §3).
APPLET_TYPES = frozenset({DOCUMENTATION, CALCULATOR})


class ManifestError(Exception):
    """A Manifest is missing, unparseable, or incomplete (spec §10.1)."""


@dataclass(frozen=True)
class Manifest:
    """An Applet's declaration about itself.

    ``author`` is optional free text for the error blame line (§10.3); it is not
    an identity and means nothing to the Host beyond display.
    """

    type: str
    name: str
    description: str | None = None
    author: str | None = None
    tags: tuple[str, ...] = ()


def read_manifest(path: Path) -> Manifest:
    """Read and validate the `[applet]` section of the Manifest at ``path``."""
    applet = _read_applet_section(path)

    type_ = _required_string(applet, "type")
    if type_ not in APPLET_TYPES:
        raise ManifestError(f"unknown Applet type {type_!r}")

    return Manifest(
        type=type_,
        name=_required_string(applet, "name"),
        description=_optional_string(applet, "description"),
        author=_optional_string(applet, "author"),
        tags=_tags(applet),
    )


def _read_applet_section(path: Path) -> dict[str, object]:
    """Load the Manifest's `[applet]` table, raising if it is not there."""
    try:
        with path.open("rb") as handle:
            document = tomllib.load(handle)
    except OSError as error:
        raise ManifestError(
            f"{MANIFEST_FILENAME} could not be read: {error}"
        ) from error
    except tomllib.TOMLDecodeError as error:
        raise ManifestError(
            f"{MANIFEST_FILENAME} is not valid TOML: {error}"
        ) from error

    applet = document.get("applet")
    if not isinstance(applet, dict):
        raise ManifestError("no [applet] section")
    return applet


def _required_string(applet: dict[str, object], key: str) -> str:
    """Read a key the Host cannot render the Applet without."""
    value = applet.get(key)
    if not isinstance(value, str) or not value:
        raise ManifestError(f"[applet] needs a non-empty string {key!r}")
    return value


def _optional_string(applet: dict[str, object], key: str) -> str | None:
    """Read a key that may be absent — but must be a string when present."""
    value = applet.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ManifestError(f"[applet] {key!r} must be a string")
    return value


def _tags(applet: dict[str, object]) -> tuple[str, ...]:
    """Read the tag list as authored. Normalisation happens at scan (§4.2, #33)."""
    tags = applet.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise ManifestError("[applet] tags must be a list of strings")
    return tuple(tags)
