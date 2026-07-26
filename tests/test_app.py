"""Routing, the render pipeline, and the greyed card (spec §2.8, §3.1, §10.1)."""

from pathlib import Path

import pytest
from conftest import client_for

from workshop_helper.discovery import Applet, Fault, Index
from workshop_helper.roots import Root

CONTENT = """# Thread pitch

M8 coarse is **1.25mm**.

![Thread form](thread-form.svg)
"""


def _documentation(tmp_path: Path) -> Applet:
    folder = tmp_path / "thread-pitch"
    folder.mkdir()
    (folder / "content.md").write_text(CONTENT)
    (folder / "thread-form.svg").write_text("<svg />")
    return Applet(
        id="thread-pitch",
        root=Root(name="built-in", path=tmp_path),
        path=folder,
        type="documentation",
        name="Thread pitch",
        description="Pitch and tap-drill reference.",
        tags=("fastener", "thread"),
        body=CONTENT,
    )


def _calculator(tmp_path: Path) -> Applet:
    return Applet(
        id="pipe-bender",
        root=Root(name="built-in", path=tmp_path),
        path=tmp_path / "pipe-bender",
        type="calculator",
        name="Pipe-bender setback",
    )


def test_browse_page_reports_an_empty_library() -> None:
    body = client_for(Index()).get("/").get_data(as_text=True)
    assert "Workshop Helper" in body
    assert "No Applets" in body


def test_browse_page_shows_a_card_per_loaded_applet(tmp_path: Path) -> None:
    index = Index(applets=[_documentation(tmp_path), _calculator(tmp_path)])

    body = client_for(index).get("/").get_data(as_text=True)

    assert "Thread pitch" in body
    assert "Pitch and tap-drill reference." in body
    assert "Pipe-bender setback" in body
    assert 'href="/a/thread-pitch"' in body
    assert "fastener" in body


def test_documentation_renders_its_content_as_markdown(tmp_path: Path) -> None:
    index = Index(applets=[_documentation(tmp_path)])

    response = client_for(index).get("/a/thread-pitch")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<h1>Thread pitch</h1>" in body
    assert "<strong>1.25mm</strong>" in body


def test_documentation_content_links_resolve_onto_the_assets_mount(
    tmp_path: Path,
) -> None:
    """The author writes a relative link; the Host scopes it (library-stack §3)."""
    index = Index(applets=[_documentation(tmp_path)])

    body = client_for(index).get("/a/thread-pitch").get_data(as_text=True)

    assert 'src="/a/thread-pitch/assets/thread-form.svg"' in body


def test_documentation_serves_the_folders_assets(tmp_path: Path) -> None:
    index = Index(applets=[_documentation(tmp_path)])

    response = client_for(index).get("/a/thread-pitch/assets/thread-form.svg")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "<svg />"


@pytest.mark.parametrize(
    "path",
    [
        "/a/thread-pitch/assets/nothing.png",
        "/a/thread-pitch/assets/../../secret.txt",
        "/a/nobody/assets/thread-form.svg",
    ],
)
def test_missing_or_escaping_asset_paths_are_not_found(
    tmp_path: Path, path: str
) -> None:
    (tmp_path / "secret.txt").write_text("private\n")
    index = Index(applets=[_documentation(tmp_path)])

    assert client_for(index).get(path).status_code == 404


def test_an_unknown_applet_id_is_not_found() -> None:
    assert client_for(Index()).get("/a/nobody").status_code == 404


def test_a_calculator_is_not_renderable_yet(tmp_path: Path) -> None:
    """Calculator rendering — form, lazy import, Result — arrives with #35."""
    index = Index(applets=[_calculator(tmp_path)])

    assert client_for(index).get("/a/pipe-bender").status_code == 501


# --- The greyed, un-openable card (§10.1, §10.3) ------------------------------


def _fault(
    tmp_path: Path,
    applet_id: str = "pipe-bender",
    reason: str = "missing applet.py",
    name: str | None = "Pipe-bender setback",
    author: str | None = "dave",
) -> Fault:
    return Fault(
        id=applet_id,
        root=Root(name="mate-collection", path=tmp_path),
        path=tmp_path / applet_id,
        reason=reason,
        name=name,
        author=author,
    )


def test_a_faulty_applet_gets_a_greyed_card(tmp_path: Path) -> None:
    body = client_for(Index(faults=[_fault(tmp_path)])).get("/").get_data(as_text=True)

    assert "faulty" in body
    assert "Pipe-bender setback" in body


def test_a_greyed_card_is_un_openable(tmp_path: Path) -> None:
    """No link out of it, and nothing behind the URL either (§10.1)."""
    client = client_for(Index(faults=[_fault(tmp_path)]))

    assert 'href="/a/pipe-bender"' not in client.get("/").get_data(as_text=True)
    assert client.get("/a/pipe-bender").status_code == 404


def test_a_greyed_card_shows_the_blame_line_over_collapsed_details(
    tmp_path: Path,
) -> None:
    body = client_for(Index(faults=[_fault(tmp_path)])).get("/").get_data(as_text=True)

    assert "Pipe-bender setback — from Root &#39;mate-collection&#39;, by dave" in body
    assert "<details>" in body  # collapsed: no `open` attribute
    assert "Details" in body
    assert "missing applet.py" in body


def test_a_greyed_card_falls_back_to_the_folder_name_and_the_root(
    tmp_path: Path,
) -> None:
    """When the Manifest will not parse, this is the whole card (§10.1, §10.3)."""
    fault = _fault(
        tmp_path,
        applet_id="thread-pitch",
        name=None,
        author=None,
        reason="manifest.toml is not valid TOML",
    )

    body = client_for(Index(faults=[fault])).get("/").get_data(as_text=True)

    assert (
        "thread-pitch — from Root &#39;mate-collection&#39;, by mate-collection" in body
    )


def test_faulty_cards_do_not_make_an_empty_library_look_stocked(
    tmp_path: Path,
) -> None:
    """Nothing loaded is still nothing loaded, but the fault must not vanish."""
    body = client_for(Index(faults=[_fault(tmp_path)])).get("/").get_data(as_text=True)

    assert "No Applets" in body
    assert "Pipe-bender setback" in body
