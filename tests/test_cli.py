"""The launch command (spec §2.3): CLI-only port, delegation to serve."""

from workshop_helper import cli, lifecycle
from workshop_helper.discovery import Index


def test_parse_args_defaults_to_the_fixed_port() -> None:
    assert cli.parse_args([]).port == lifecycle.DEFAULT_PORT


def test_parse_args_port_override() -> None:
    assert cli.parse_args(["--port", "9000"]).port == 9000


def test_main_builds_the_index_and_serves_on_the_given_port(monkeypatch) -> None:
    calls: list[tuple[Index, int]] = []
    monkeypatch.setattr(
        cli, "serve", lambda index, port: calls.append((index, port)) or 0
    )

    code = cli.main(["--port", "9000"])

    assert code == 0
    (index, port) = calls[0]
    assert isinstance(index, Index)
    assert port == 9000
