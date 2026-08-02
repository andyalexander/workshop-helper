"""The launch command (spec §2.3): CLI-only port, delegation to serve."""

from workshop_helper import cli, lifecycle
from workshop_helper.discovery import Index
from workshop_helper.home import resolve_home
from workshop_helper.overlay import OVERLAY_FILENAME, Overlay


def test_parse_args_defaults_to_the_fixed_port() -> None:
    assert cli.parse_args([]).port == lifecycle.DEFAULT_PORT


def test_parse_args_port_override() -> None:
    assert cli.parse_args(["--port", "9000"]).port == 9000


def test_main_builds_the_index_and_serves_on_the_given_port(monkeypatch) -> None:
    calls: list[tuple[Index, Overlay, int]] = []
    monkeypatch.setattr(
        cli,
        "serve",
        lambda index, overlay, port: calls.append((index, overlay, port)) or 0,
    )

    code = cli.main(["--port", "9000"])

    assert code == 0
    (index, overlay, port) = calls[0]
    assert isinstance(index, Index)
    assert port == 9000
    # The Overlay is a separate file beside the hand-edited config, never a
    # section within it (ADR-0007).
    assert overlay.path.name == OVERLAY_FILENAME
    assert overlay.path.parent == resolve_home()
