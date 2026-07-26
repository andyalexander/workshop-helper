"""Root scanning, the index, and the discovery-time fault taxonomy.

Spec §2.5, §2.6, §2.7, §2.3 step 5, §10.1, §10.4.
"""

from pathlib import Path

import pytest

from workshop_helper.discovery import Fault, Index, build_index
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
    return Root(name=name, path=path)


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


def test_a_broken_higher_tier_applet_still_claims_its_id(tmp_path: Path) -> None:
    """Precedence is by tier, not by health (spec §2.7).

    Otherwise a foreign Root captures a built-in id by shipping a broken twin of
    its name — the collision the tier rule exists to close. Both folders fault:
    the winner is malformed, the loser is shadowed by it.
    """
    builtin = _root(tmp_path / "builtin", name="built-in")
    foreign = _root(tmp_path / "theirs", name="mate-collection")
    broken = builtin.path / "thread-pitch"
    broken.mkdir()
    (broken / "manifest.toml").write_text('[applet]\ntype = "widget"\n')
    _documentation(foreign, "thread-pitch")

    index = build_index([builtin, foreign])

    assert index.applets == []
    assert [(f.root.name, f.reason) for f in index.faults] == [
        ("built-in", "unknown Applet type 'widget'"),
        ("mate-collection", "shadowed by Root 'built-in'"),
    ]


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


# --- The discovery-time fault taxonomy (§10.1) -------------------------------

BAD_DEFAULT_MANIFEST = """
[applet]
type   = "calculator"
name   = "Pipe-bender setback"
author = "andy"

[inputs.size]
kind    = "choice"
label   = "Pipe size"
choices = ["15mm", "22mm"]
default = "28mm"
"""

CALIBRATED_DOC_MANIFEST = """
[applet]
type   = "documentation"
name   = "Thread pitch"
author = "andy"

[calibration.values]
r_centreline = 70.0
"""


def _broken(root: Root, applet_id: str, manifest: str, **files: str) -> Path:
    folder = root.path / applet_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.toml").write_text(manifest)
    for name, text in files.items():
        (folder / name.replace("_", ".")).write_text(text)
    return folder


@pytest.mark.parametrize(
    ("applet_id", "manifest", "files", "because"),
    [
        ("unparseable", "not = valid = toml", {}, "malformed manifest.toml"),
        (
            "incomplete",
            '[applet]\ntype = "documentation"\n',
            {"content_md": "#\n"},
            "incomplete manifest.toml",
        ),
        (
            "widgety",
            '[applet]\ntype = "widget"\nname = "W"\n',
            {},
            "unknown Applet type",
        ),
        ("bodyless", DOC_MANIFEST, {}, "missing content.md"),
        ("codeless", CALC_MANIFEST, {}, "missing applet.py"),
        (
            "bad-default",
            BAD_DEFAULT_MANIFEST,
            {"applet_py": "\n"},
            "invalid author default",
        ),
        (
            "calibrated-doc",
            CALIBRATED_DOC_MANIFEST,
            {"content_md": "#\n"},
            "[calibration] on a documentation Applet",
        ),
    ],
)
def test_every_discovery_time_fault_yields_one_greyed_card(
    tmp_path: Path,
    applet_id: str,
    manifest: str,
    files: dict[str, str],
    because: str,
) -> None:
    root = _root(tmp_path / "own")
    _broken(root, applet_id, manifest, **files)

    index = build_index([root])

    assert index.applets == []
    (fault,) = index.faults
    assert fault.id == applet_id
    assert fault.root == root
    assert fault.reason  # something to put in Details, always
    assert index.failed == 1


def test_a_fault_stays_searchable_by_folder_name(tmp_path: Path) -> None:
    """The only handle left when there is no name to search (spec §10.1)."""
    root = _root(tmp_path / "own")
    _broken(root, "thread-pitch", "not = valid = toml")

    (fault,) = build_index([root]).faults

    assert fault.name is None
    assert fault.display_name == "thread-pitch"
    assert "thread-pitch" in fault.search_text


def test_a_fault_uses_what_of_the_manifest_did_parse(tmp_path: Path) -> None:
    """A named Applet is named on its greyed card; only the reason is new."""
    root = _root(tmp_path / "own", name="mate-collection")
    _broken(root, "thread-pitch", DOC_MANIFEST)  # no content.md

    (fault,) = build_index([root]).faults

    assert fault.display_name == "Thread pitch"
    assert fault.author == "andy"
    assert fault.surface.blame == (
        "Thread pitch — from Root 'mate-collection', by andy"
    )
    assert fault.surface.details == fault.reason


@pytest.mark.parametrize(
    ("applet_id", "manifest", "files"),
    [
        ("bodyless", DOC_MANIFEST, {}),
        ("bad-default", BAD_DEFAULT_MANIFEST, {"applet_py": "\n"}),
        ("calibrated-doc", CALIBRATED_DOC_MANIFEST, {"content_md": "#\n"}),
    ],
)
def test_a_fault_is_blamed_on_the_author_whenever_applet_parsed(
    tmp_path: Path, applet_id: str, manifest: str, files: dict[str, str]
) -> None:
    """Whichever rule failed, `[applet]` still says whose Applet this is (§10.3).

    Losing the author to a validation failure elsewhere in the file would strip
    the blame line of exactly the blame it exists to carry — which is how these
    three read before the identity was read separately from the validation.
    """
    root = _root(tmp_path / "own", name="mate-collection")
    _broken(root, applet_id, manifest, **files)

    (fault,) = build_index([root]).faults

    assert fault.name is not None
    assert fault.author == "andy"
    assert ", by andy" in fault.surface.blame


def test_a_shadowed_applet_is_greyed_and_names_the_root_that_won(
    tmp_path: Path,
) -> None:
    """The winner loads; the loser is greyed with the notice (spec §2.7)."""
    own = _root(tmp_path / "own", name="own")
    foreign = _root(tmp_path / "theirs", name="mate-collection")
    _documentation(own, "thread-pitch", body="mine\n")
    _documentation(foreign, "thread-pitch", body="theirs\n")

    index = build_index([own, foreign])

    assert [(a.id, a.root.name) for a in index.applets] == [("thread-pitch", "own")]
    (fault,) = index.faults
    assert fault.id == "thread-pitch"
    assert fault.root == foreign
    assert fault.reason == "shadowed by Root 'own'"
    # The loser's own Manifest still parsed, so its card reads as its author left it.
    assert fault.surface.blame == (
        "Thread pitch — from Root 'mate-collection', by andy"
    )


def test_a_shadowed_applet_with_a_broken_manifest_reports_the_shadowing(
    tmp_path: Path,
) -> None:
    """One fault per folder: shadowing is the reason it will never be opened."""
    own = _root(tmp_path / "own", name="own")
    foreign = _root(tmp_path / "theirs", name="mate-collection")
    _documentation(own, "thread-pitch")
    _broken(foreign, "thread-pitch", "not = valid = toml")

    (fault,) = build_index([own, foreign]).faults

    assert fault.reason == "shadowed by Root 'own'"
    assert fault.display_name == "thread-pitch"


def test_faults_are_not_applets(tmp_path: Path) -> None:
    """A greyed card is un-openable, so nothing can look one up as an Applet."""
    root = _root(tmp_path / "own")
    _broken(root, "broken", "not = valid = toml")

    index = build_index([root])

    assert index.applet("broken") is None


def test_the_failed_count_is_the_faults(tmp_path: Path) -> None:
    root = _root(tmp_path / "own")
    _broken(root, "one", "not = valid = toml")
    _broken(root, "two", "not = valid = toml")

    index = build_index([root])

    assert index.failed == 2
    assert index.summary_line() == "Loaded 0 Applets; 2 failed."


def test_tags_reach_the_index_normalised(tmp_path: Path) -> None:
    """Normalisation happens at scan, so the index holds facet-ready tags (§4.2)."""
    root = _root(tmp_path / "own")
    folder = root.path / "thread-pitch"
    folder.mkdir()
    (folder / "manifest.toml").write_text(
        '[applet]\ntype = "documentation"\nname = "T"\ntags = ["  Copper", "HAND  TOOLS"]\n'
    )
    (folder / "content.md").write_text("#\n")

    (applet,) = build_index([root]).applets

    assert applet.tags == ("copper", "hand tools")


def test_a_fault_record_is_self_describing() -> None:
    """A Fault needs no Index to render: id, provenance, reason (spec §10.1)."""
    fault = Fault(
        id="broken",
        root=Root(name="own", path=Path("/nowhere")),
        path=Path("/nowhere/broken"),
        reason="no [applet] section",
    )

    assert fault.display_name == "broken"
    assert fault.surface.blame == "broken — from Root 'own', by own"
