"""Root tiers and their names (spec §2.5)."""

from pathlib import Path

from workshop_helper.roots import BUILTIN_ROOT_PATH, Root, resolve_roots


def test_tier_order_is_own_then_builtin_then_foreign(tmp_path: Path) -> None:
    roots = resolve_roots(tmp_path / "home", [Path("/mnt/a"), Path("/mnt/b")])
    assert [root.path for root in roots] == [
        tmp_path / "home" / "applets",
        BUILTIN_ROOT_PATH,
        Path("/mnt/a"),
        Path("/mnt/b"),
    ]


def test_own_and_builtin_roots_are_named_by_tier(tmp_path: Path) -> None:
    own, builtin = resolve_roots(tmp_path, [])[:2]
    assert own.name == "own"
    assert builtin.name == "built-in"


def test_only_the_own_root_is_flagged_as_own(tmp_path: Path) -> None:
    own, builtin, foreign = resolve_roots(tmp_path, [Path("/mnt/a")])
    assert own.is_own is True
    assert builtin.is_own is False
    assert foreign.is_own is False


def test_builtin_root_ships_inside_the_package() -> None:
    """The built-in Root lives in the wheel, not on the user's disk (spec §2.5)."""
    assert BUILTIN_ROOT_PATH.is_dir()
    assert BUILTIN_ROOT_PATH.parent.name == "workshop_helper"


def test_foreign_root_is_named_by_its_folder() -> None:
    foreign = resolve_roots(Path("/home"), [Path("/mnt/shared/workshop-applets")])[-1]
    assert foreign.name == "workshop-applets"


def test_foreign_root_named_applets_takes_its_parents_name() -> None:
    """``.../mate-collection/applets`` reads as Root 'mate-collection' (spec §10.3)."""
    foreign = resolve_roots(Path("/home"), [Path("/src/mate-collection/applets")])[-1]
    assert foreign.name == "mate-collection"


def test_roots_are_hashable_so_applets_can_carry_their_provenance() -> None:
    assert Root(name="own", path=Path("/a"), is_own=True) == Root(
        name="own", path=Path("/a"), is_own=True
    )
