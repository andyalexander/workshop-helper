"""The index and its one-line startup summary (spec §2.6, §2.3 step 5)."""

from pathlib import Path

from workshop_helper.discovery import Index, build_index


def test_walking_skeleton_loads_nothing() -> None:
    index = build_index([])
    assert index.applets == []
    assert index.failed == 0


def test_summary_line_matches_spec_format() -> None:
    assert Index(applets=[], failed=0).summary_line() == "Loaded 0 Applets; 0 failed."


def test_missing_root_path_is_not_an_error(tmp_path: Path) -> None:
    """A missing or unreadable Root is skipped, never raised (spec §2.5)."""
    index = build_index([tmp_path / "does-not-exist"])
    assert index.applets == []
    assert index.failed == 0
