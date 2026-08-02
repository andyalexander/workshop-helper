"""Shared test helpers."""

import tempfile
from pathlib import Path

from flask.testing import FlaskClient

from workshop_helper.app import create_app
from workshop_helper.discovery import Index
from workshop_helper.overlay import OVERLAY_FILENAME, Overlay


def client_for(index: Index, overlay: Overlay | None = None) -> FlaskClient:
    """A test client over the Host, serving ``index``.

    The default Overlay is an empty one in a scratch directory: a test that says
    nothing about overrides is a test about the author's Applet, and must never
    be able to reach the real ``~/.workshop-helper/``.
    """
    app = create_app(index, overlay or Overlay(_scratch_overlay()))
    app.config.update(TESTING=True)
    return app.test_client()


def _scratch_overlay() -> Path:
    """A path in a fresh temporary directory, with no file at it."""
    return Path(tempfile.mkdtemp()) / OVERLAY_FILENAME
