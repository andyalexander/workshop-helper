"""The browse surface (spec §2.8): an empty page for the walking skeleton."""

from workshop_helper.app import create_app
from workshop_helper.discovery import Index


def _client():
    app = create_app(Index(applets=[], failed=0))
    app.config.update(TESTING=True)
    return app.test_client()


def test_browse_page_serves_ok() -> None:
    response = _client().get("/")
    assert response.status_code == 200


def test_browse_page_reports_empty_library() -> None:
    body = _client().get("/").get_data(as_text=True)
    assert "Workshop Helper" in body
    assert "No Applets" in body
