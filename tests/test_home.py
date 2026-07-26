"""Host home resolution and config reading (spec §2.4)."""

from pathlib import Path

from workshop_helper.home import load_config_roots, resolve_home


def test_resolve_home_defaults_to_dot_workshop_helper() -> None:
    assert resolve_home(env={}) == Path.home() / ".workshop-helper"


def test_resolve_home_honours_env_override(tmp_path: Path) -> None:
    env = {"WORKSHOP_HELPER_HOME": str(tmp_path / "elsewhere")}
    assert resolve_home(env=env) == tmp_path / "elsewhere"


def test_resolve_home_expands_tilde_in_override() -> None:
    env = {"WORKSHOP_HELPER_HOME": "~/custom-home"}
    assert resolve_home(env=env) == Path.home() / "custom-home"


def test_missing_config_toml_is_fine(tmp_path: Path) -> None:
    """A missing config.toml is not an error (spec §2.3, §2.4)."""
    assert load_config_roots(tmp_path) == []


def test_config_without_roots_key_yields_empty(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text("# nothing here\n")
    assert load_config_roots(tmp_path) == []


def test_roots_are_read_and_tilde_expanded(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        "roots = [\n"
        '  "~/src/mate-collection/applets",\n'
        '  "/mnt/shared/workshop-applets",\n'
        "]\n"
    )
    assert load_config_roots(tmp_path) == [
        Path.home() / "src/mate-collection/applets",
        Path("/mnt/shared/workshop-applets"),
    ]
