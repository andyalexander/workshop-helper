"""The built-in Root's worked examples (spec §11).

`thread-pitch` is the `documentation` worked example (§11.1): Manifest +
`content.md` + assets, **zero code**. It covers the documentation rendering
contract, markdown via `workshop_utils`, asset serving, and the content-body
indexing #2's full-text fallback depends on.
"""

from flask.testing import FlaskClient

from workshop_helper.app import create_app
from workshop_helper.discovery import Index, build_index
from workshop_helper.roots import BUILTIN_ROOT_NAME, BUILTIN_ROOT_PATH, Root

BUILTIN = Root(name=BUILTIN_ROOT_NAME, path=BUILTIN_ROOT_PATH)


def _index() -> Index:
    return build_index([BUILTIN])


def _client() -> FlaskClient:
    app = create_app(_index())
    app.config.update(TESTING=True)
    return app.test_client()


def test_the_builtin_root_loads_without_faults() -> None:
    index = _index()
    assert index.failed == 0
    assert index.skipped_roots == 0
    assert index.applets


def test_thread_pitch_is_indexed_with_its_content_body() -> None:
    applet = _index().applet("thread-pitch")

    assert applet is not None
    assert applet.type == "documentation"
    assert applet.name == "Thread pitch"
    assert applet.root.name == BUILTIN_ROOT_NAME
    assert "fastener" in applet.tags
    # The body is indexed, which is what makes full-text search possible (§2.6).
    assert applet.body is not None and "Whitworth" in applet.body


def test_thread_pitch_ships_zero_python() -> None:
    """Documentation Applets have no code at all (spec §3.1)."""
    folder = BUILTIN_ROOT_PATH / "thread-pitch"
    assert sorted(p.name for p in folder.iterdir()) == [
        "content.md",
        "manifest.toml",
        "thread-form.svg",
    ]


def test_thread_pitch_renders_as_its_reference_table() -> None:
    page = _client().get("/a/thread-pitch")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "<table>" in body
    assert "M8" in body


def test_thread_pitch_serves_the_asset_its_content_references() -> None:
    """The rendered page's own image URL must be one the Host actually serves."""
    page = _client().get("/a/thread-pitch").get_data(as_text=True)
    src = 'src="/a/thread-pitch/assets/thread-form.svg"'

    assert src in page
    assert _client().get("/a/thread-pitch/assets/thread-form.svg").status_code == 200


def test_thread_pitch_appears_on_the_browse_page() -> None:
    body = _client().get("/").get_data(as_text=True)

    assert 'href="/a/thread-pitch"' in body
    assert "Thread pitch" in body


def test_builtin_root_holds_only_applet_folders() -> None:
    """Every folder shipped in the built-in Root must be a real Applet (§2.5)."""
    folders = [p for p in BUILTIN_ROOT_PATH.iterdir() if p.is_dir()]
    assert folders
    for folder in folders:
        assert (folder / "manifest.toml").is_file(), folder
    assert len(folders) == len(_index().applets)
