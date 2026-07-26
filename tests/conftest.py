"""Shared test helpers."""

from flask.testing import FlaskClient

from workshop_helper.app import create_app
from workshop_helper.discovery import Index


def client_for(index: Index) -> FlaskClient:
    """A test client over the Host, serving ``index``."""
    app = create_app(index)
    app.config.update(TESTING=True)
    return app.test_client()
