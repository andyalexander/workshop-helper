"""Reading `[applet]` out of a Manifest (spec §4.1, §3, §10.1).

The fault *taxonomy* — which greyed card each failure produces — belongs to #33.
What is settled here is that a Manifest either yields metadata or raises.
"""

from pathlib import Path

import pytest

from workshop_helper.manifest import APPLET_TYPES, ManifestError, read_manifest

COMPLETE = """
[applet]
type        = "calculator"
name        = "Pipe-bender setback"
description = "Setback and offset marks for a lever pipe bender."
author      = "andy"
tags        = ["plumbing", "copper", "pipe-bending"]
"""

MINIMAL = """
[applet]
type = "documentation"
name = "Thread pitch"
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "manifest.toml"
    path.write_text(text)
    return path


def test_applet_types_are_the_closed_set() -> None:
    """Adding a type is a change to the Host, not to a Manifest (ADR-0005)."""
    assert APPLET_TYPES == frozenset({"documentation", "calculator"})


def test_reads_every_declared_field(tmp_path: Path) -> None:
    manifest = read_manifest(_write(tmp_path, COMPLETE))
    assert manifest.type == "calculator"
    assert manifest.name == "Pipe-bender setback"
    assert manifest.description == "Setback and offset marks for a lever pipe bender."
    assert manifest.author == "andy"
    assert manifest.tags == ("plumbing", "copper", "pipe-bending")


def test_optional_fields_degrade_to_none_and_empty(tmp_path: Path) -> None:
    manifest = read_manifest(_write(tmp_path, MINIMAL))
    assert manifest.description is None
    assert manifest.author is None
    assert manifest.tags == ()


@pytest.mark.parametrize(
    ("text", "because"),
    [
        ("not = valid = toml", "unparseable TOML"),
        ('name = "no section"', "no [applet] section"),
        ('[applet]\nname = "Nameless type"', "no type"),
        ('[applet]\ntype = "documentation"', "no name"),
        ('[applet]\ntype = "widget"\nname = "Unknown"', "unknown type"),
        ('[applet]\ntype = "documentation"\nname = 7', "non-string name"),
        (
            '[applet]\ntype = "documentation"\nname = "T"\ntags = "copper"',
            "tags not a list",
        ),
        ('[applet]\ntype = "documentation"\nname = "T"\ntags = [1]', "non-string tag"),
    ],
)
def test_malformed_manifests_raise(tmp_path: Path, text: str, because: str) -> None:
    with pytest.raises(ManifestError):
        read_manifest(_write(tmp_path, text))


def test_a_missing_manifest_raises(tmp_path: Path) -> None:
    with pytest.raises(ManifestError):
        read_manifest(tmp_path / "manifest.toml")
