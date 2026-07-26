"""Launch and lifecycle (spec §2.3).

The Host is a foreground process, never a daemon. It binds a fixed, non-obvious
port on ``127.0.0.1``; ``--port`` overrides it and there is deliberately no config
key for port. If the default port is busy, the most likely cause is that the Host
is already running, so opening the browser at it beats starting a second copy.
"""

import socket
import threading
import webbrowser

from flask import Flask

from workshop_helper.app import create_app
from workshop_helper.discovery import Index

DEFAULT_HOST = "127.0.0.1"
# The one free choice in the spec (§2.3): a fixed default in the high private
# range. Everything else about lifecycle is settled.
DEFAULT_PORT = 8731

# Give the foreground server a moment to bind before the browser connects.
_BROWSER_DELAY_SECONDS = 0.5


def port_is_available(port: int, host: str = DEFAULT_HOST) -> bool:
    """Return whether ``port`` can be bound on ``host`` right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def open_browser(host: str, port: int) -> None:
    """Open the user's default browser at the Host's URL."""
    webbrowser.open(f"http://{host}:{port}/")


def schedule_browser(host: str, port: int) -> None:
    """Open the browser once the about-to-block server has had time to bind.

    The timer is a daemon thread so it can never delay a clean Ctrl-C shutdown.
    """
    timer = threading.Timer(_BROWSER_DELAY_SECONDS, open_browser, args=(host, port))
    timer.daemon = True
    timer.start()


def run_server(app: Flask, host: str, port: int) -> None:
    """Run the foreground Flask server; blocks until Ctrl-C."""
    app.run(host=host, port=port)


def serve(index: Index, port: int, host: str = DEFAULT_HOST) -> int:
    """Launch the Host, or defer to an already-running copy on a busy port.

    A busy port is not a startup, so it prints exactly one line and defers; the
    startup summary (spec §2.3 step 5) is emitted only on the live path, right
    before binding.
    """
    if not port_is_available(port, host):
        open_browser(host, port)
        print(f"Workshop Helper already running on http://{host}:{port}/")
        return 0

    print(index.summary_line())
    app = create_app(index)
    print(f"Serving Workshop Helper on http://{host}:{port}/  (Ctrl-C to stop)")
    schedule_browser(host, port)
    run_server(app, host, port)
    return 0
