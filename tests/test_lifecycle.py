"""Launch and lifecycle (spec §2.3): fixed port, busy-port fallback, foreground."""

import socket
from pathlib import Path

import pytest

from workshop_helper import lifecycle
from workshop_helper.discovery import Index
from workshop_helper.overlay import OVERLAY_FILENAME, Overlay


def _overlay() -> Overlay:
    """An Overlay at a path nothing here reads or writes."""
    return Overlay(Path(OVERLAY_FILENAME))


def test_default_port_is_the_specs_free_choice() -> None:
    assert lifecycle.DEFAULT_PORT == 8731
    assert lifecycle.DEFAULT_HOST == "127.0.0.1"


def test_port_is_available_detects_a_bound_port() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as held:
        held.bind((lifecycle.DEFAULT_HOST, 0))
        held.listen()
        taken = held.getsockname()[1]
        assert lifecycle.port_is_available(taken) is False


def test_port_is_available_true_for_a_free_port() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((lifecycle.DEFAULT_HOST, 0))
    free = sock.getsockname()[1]
    sock.close()
    assert lifecycle.port_is_available(free) is True


def test_port_is_available_ignores_a_socket_left_in_time_wait() -> None:
    """A restart must not report the copy it just stopped as still running.

    Closing the server end of a connection leaves that port in ``TIME_WAIT`` for
    around a minute. The server binds with ``SO_REUSEADDR`` and would take the
    port happily, so a probe that refuses it is answering a stricter question
    than the one asked.
    """
    host = lifecycle.DEFAULT_HOST
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind((host, 0))
    listener.listen()
    port = listener.getsockname()[1]

    client = socket.create_connection((host, port))
    served, _ = listener.accept()
    # Closing the server end *first* is what leaves this port in TIME_WAIT —
    # exactly what a Ctrl-C on the Host does to every connection it was holding.
    served.close()
    client.close()
    listener.close()

    bare = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        bare.bind((host, port))
    except OSError:
        pass  # The state under test: a plain bind is refused.
    else:
        bare.close()
        pytest.skip("platform releases the port immediately; nothing to test")

    assert lifecycle.port_is_available(port) is True


def test_busy_port_opens_browser_and_exits_zero_without_serving(
    monkeypatch, capsys
) -> None:
    """A busy default port means the Host is already running (spec §2.3)."""
    opened: list[tuple[str, int]] = []
    served: list[object] = []
    monkeypatch.setattr(
        lifecycle, "port_is_available", lambda port, host=lifecycle.DEFAULT_HOST: False
    )
    monkeypatch.setattr(
        lifecycle, "open_browser", lambda host, port: opened.append((host, port))
    )
    monkeypatch.setattr(
        lifecycle, "run_server", lambda app, host, port: served.append(app)
    )

    code = lifecycle.serve(Index(), _overlay(), lifecycle.DEFAULT_PORT)

    out = capsys.readouterr().out
    assert code == 0
    assert opened == [(lifecycle.DEFAULT_HOST, lifecycle.DEFAULT_PORT)]
    assert served == []  # never starts a second copy
    assert "already running" in out.lower()
    # The busy path is not a startup: it prints exactly one line (spec §2.3 AC).
    assert out.strip().count("\n") == 0
    assert "Loaded" not in out


def test_free_port_serves_and_prints_the_startup_summary(monkeypatch, capsys) -> None:
    served: list[int] = []
    monkeypatch.setattr(
        lifecycle, "port_is_available", lambda port, host=lifecycle.DEFAULT_HOST: True
    )
    monkeypatch.setattr(lifecycle, "schedule_browser", lambda host, port: None)
    monkeypatch.setattr(
        lifecycle, "run_server", lambda app, host, port: served.append(port)
    )

    code = lifecycle.serve(Index(), _overlay(), 9999)

    out = capsys.readouterr().out
    assert code == 0
    assert served == [9999]
    assert "Loaded 0 Applets; 0 failed." in out  # summary lives on the live path
