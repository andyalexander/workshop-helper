"""Root scanning and the index (spec §2.5, §2.6, §2.3 step 5)."""

from pathlib import Path

from workshop_helper.discovery import Index, build_index
from workshop_helper.roots import Root

DOC_MANIFEST = """
[applet]
type        = "documentation"
name        = "Thread pitch"
description = "Pitch and tap-drill reference."
author      = "andy"
tags        = ["fastener", "thread"]
"""

CALC_MANIFEST = """
[applet]
type = "calculator"
name = "Pipe-bender setback"
"""


def _root(path: Path, name: str = "own") -> Root:
    path.mkdir(parents=True, exist_ok=True)
    return Root(name=name, path=path, is_own=name == "own")


def _documentation(root: Root, applet_id: str, body: str = "# Thread pitch\n") -> Path:
    folder = root.path / applet_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.toml").write_text(DOC_MANIFEST)
    (folder / "content.md").write_text(body)
    return folder


def _calculator(root: Root, applet_id: str) -> Path:
    folder = root.path / applet_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.toml").write_text(CALC_MANIFEST)
    (folder / "applet.py").write_text("raise AssertionError('never imported')\n")
    return folder


def test_summary_line_matches_spec_format() -> None:
    assert Index().summary_line() == "Loaded 0 Applets; 0 failed."


def test_summary_line_counts_skipped_roots_only_when_there_are_some() -> None:
    assert Index(skipped_roots=2).summary_line().endswith("2 Roots skipped.")
    assert Index(skipped_roots=1).summary_line().endswith("1 Root skipped.")


def test_missing_root_path_is_skipped_and_counted(tmp_path: Path) -> None:
    """A missing or unreadable Root is skipped, never raised (spec §2.5)."""
    index = build_index([Root(name="gone", path=tmp_path / "does-not-exist")])
    assert index.applets == []
    assert index.failed == 0
    assert index.skipped_roots == 1


def test_a_folder_with_a_manifest_is_an_applet(tmp_path: Path) -> None:
    root = _root(tmp_path / "own")
    _documentation(root, "thread-pitch")

    (applet,) = build_index([root]).applets

    assert applet.id == "thread-pitch"
    assert applet.root == root
    assert applet.type == "documentation"
    assert applet.name == "Thread pitch"
    assert applet.description == "Pitch and tap-drill reference."
    assert applet.author == "andy"
    assert applet.tags == ("fastener", "thread")
    assert applet.path == root.path / "thread-pitch"


def test_a_folder_without_a_manifest_never_appears(tmp_path: Path) -> None:
    """Not an Applet, so not a card and not an error either (spec §2.5, §10.4)."""
    root = _root(tmp_path / "own")
    (root.path / "notes").mkdir()
    (root.path / "notes" / "content.md").write_text("stray\n")
    (root.path / "loose-file.md").write_text("stray\n")

    index = build_index([root])

    assert index.applets == []
    assert index.failed == 0


def test_documentation_applets_carry_the_content_body(tmp_path: Path) -> None:
    """#2's full-text fallback needs the body, so the Host reads it (spec §2.6)."""
    root = _root(tmp_path / "own")
    _documentation(root, "thread-pitch", body="# Pitch\n\nM8 is 1.25mm coarse.\n")

    (applet,) = build_index([root]).applets

    assert applet.body is not None
    assert "M8 is 1.25mm coarse." in applet.body


def test_calculator_applets_have_no_body_and_are_not_imported(tmp_path: Path) -> None:
    """Scanning a calculator must not execute it (spec §2.6, §7.2)."""
    root = _root(tmp_path / "own")
    _calculator(root, "pipe-bender")

    (applet,) = build_index([root]).applets

    assert applet.type == "calculator"
    assert applet.body is None


def test_documentation_without_content_is_a_discovery_fault(tmp_path: Path) -> None:
    root = _root(tmp_path / "own")
    folder = root.path / "empty-doc"
    folder.mkdir()
    (folder / "manifest.toml").write_text(DOC_MANIFEST)

    index = build_index([root])

    assert index.applets == []
    assert index.failed == 1


def test_calculator_without_applet_py_is_a_discovery_fault(tmp_path: Path) -> None:
    root = _root(tmp_path / "own")
    folder = root.path / "codeless-calc"
    folder.mkdir()
    (folder / "manifest.toml").write_text(CALC_MANIFEST)

    index = build_index([root])

    assert index.applets == []
    assert index.failed == 1


def test_a_malformed_manifest_counts_as_failed(tmp_path: Path) -> None:
    root = _root(tmp_path / "own")
    folder = root.path / "broken"
    folder.mkdir()
    (folder / "manifest.toml").write_text('[applet]\ntype = "widget"\n')

    index = build_index([root])

    assert index.applets == []
    assert index.failed == 1
    assert index.summary_line() == "Loaded 0 Applets; 1 failed."


def test_roots_are_scanned_in_tier_order_and_the_higher_tier_wins(
    tmp_path: Path,
) -> None:
    """Own beats built-in beats foreign (spec §2.5, §2.7)."""
    own = _root(tmp_path / "own", name="own")
    foreign = _root(tmp_path / "theirs", name="mate-collection")
    _documentation(own, "thread-pitch", body="mine\n")
    _documentation(foreign, "thread-pitch", body="theirs\n")
    _documentation(foreign, "spanner-sizes")

    index = build_index([own, foreign])

    assert [(a.id, a.root.name) for a in index.applets] == [
        ("thread-pitch", "own"),
        ("spanner-sizes", "mate-collection"),
    ]
    assert index.applets[0].body == "mine\n"


def test_applets_are_ordered_by_id_within_a_root(tmp_path: Path) -> None:
    root = _root(tmp_path / "own")
    for applet_id in ("thread-pitch", "annealing", "spanner-sizes"):
        _documentation(root, applet_id)

    index = build_index([root])

    assert [a.id for a in index.applets] == [
        "annealing",
        "spanner-sizes",
        "thread-pitch",
    ]


def test_index_looks_applets_up_by_id(tmp_path: Path) -> None:
    root = _root(tmp_path / "own")
    _documentation(root, "thread-pitch")

    index = build_index([root])

    found = index.applet("thread-pitch")
    assert found is not None and found.id == "thread-pitch"
    assert index.applet("nothing-here") is None
