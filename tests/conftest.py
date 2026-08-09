"""Shared test helpers."""

import tempfile
from pathlib import Path
from typing import Any

from flask.testing import FlaskClient
from werkzeug.datastructures import Headers

from workshop_helper.app import create_app
from workshop_helper.discovery import Index
from workshop_helper.overlay import OVERLAY_FILENAME, Overlay


class SameOriginClient(FlaskClient):
    """A client whose requests look like they came from the Host's own pages.

    The Host refuses any non-GET that cannot prove it is same-origin (#44), and
    a browser proves it with ``Sec-Fetch-Site``. Werkzeug sends no such header,
    so without this every POST in the suite would be exercising the gate rather
    than the route behind it. ``setdefault`` is what leaves a test free to say
    otherwise — which is how the gate itself is tested.
    """

    def open(self, *args: Any, **kwargs: Any) -> Any:
        headers = Headers(kwargs.get("headers") or {})
        headers.setdefault("Sec-Fetch-Site", "same-origin")
        kwargs["headers"] = headers
        return super().open(*args, **kwargs)


def client_for(
    index: Index, overlay: Overlay | None = None, same_origin: bool = True
) -> FlaskClient:
    """A test client over the Host, serving ``index``.

    The default Overlay is an empty one in a scratch directory: a test that says
    nothing about overrides is a test about the author's Applet, and must never
    be able to reach the real ``~/.workshop-helper/``.

    ``same_origin=False`` gives a client that sends no origin headers at all —
    the bare Werkzeug behaviour, which is what a curl or a pre-2020 browser
    looks like to the gate.
    """
    app = create_app(index, overlay or Overlay(_scratch_overlay()))
    app.config.update(TESTING=True)
    if same_origin:
        app.test_client_class = SameOriginClient
    return app.test_client()


def _scratch_overlay() -> Path:
    """A path in a fresh temporary directory, with no file at it."""
    return Path(tempfile.mkdtemp()) / OVERLAY_FILENAME
