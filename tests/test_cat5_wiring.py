"""The `cat5-wiring` documentation Applet.

A static reference: Manifest + `content.md` + one SVG, **zero code**. The tests
that matter are the two a documentation Applet can silently get wrong — the pin
order itself, and whether the image the page points at is one the Host serves.
"""

from conftest import client_for
from flask.testing import FlaskClient

from workshop_helper.discovery import Index, build_index
from workshop_helper.roots import BUILTIN_ROOT_NAME, BUILTIN_ROOT_PATH, Root

BUILTIN = Root(name=BUILTIN_ROOT_NAME, path=BUILTIN_ROOT_PATH)
APPLET_ID = "cat5-wiring"


def _index() -> Index:
    return build_index([BUILTIN])


def _client() -> FlaskClient:
    return client_for(_index())


def test_cat5_wiring_is_indexed_as_documentation() -> None:
    applet = _index().applet(APPLET_ID)

    assert applet is not None
    assert applet.type == "documentation"
    assert applet.name == "Cat5 wiring colours"
    assert applet.root.name == BUILTIN_ROOT_NAME
    assert "network" in applet.tags
    # The body is indexed, which is what makes full-text search possible (§2.6).
    assert applet.body is not None and "T568B" in applet.body


def test_cat5_wiring_ships_zero_python() -> None:
    """Documentation Applets have no code at all (spec §3.1)."""
    folder = BUILTIN_ROOT_PATH / APPLET_ID
    assert sorted(p.name for p in folder.iterdir()) == [
        "cat5-pinout.svg",
        "content.md",
        "manifest.toml",
    ]


def test_both_standards_are_on_the_page() -> None:
    page = _client().get(f"/a/{APPLET_ID}")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "<table>" in body
    assert "T568A" in body and "T568B" in body


def test_the_pin_table_carries_the_standard_order() -> None:
    """The one thing a wiring reference cannot be wrong about.

    Pins 1, 2, 3 and 6 are the only ones that move between the standards, so
    those rows are the whole difference — and a mirrored or transposed table
    would still look plausible without them being checked.
    """
    body = _client().get(f"/a/{APPLET_ID}").get_data(as_text=True)
    rows = [
        "<td>1</td>\n<td>white/orange</td>\n<td>white/green</td>",
        "<td>2</td>\n<td>orange</td>\n<td>green</td>",
        "<td>3</td>\n<td>white/green</td>\n<td>white/orange</td>",
        "<td>6</td>\n<td>green</td>\n<td>orange</td>",
    ]
    for row in rows:
        assert row in body


def test_the_pairs_shared_by_both_standards_do_not_move() -> None:
    body = _client().get(f"/a/{APPLET_ID}").get_data(as_text=True)

    assert "<td>4</td>\n<td>blue</td>\n<td>blue</td>" in body
    assert "<td>5</td>\n<td>white/blue</td>\n<td>white/blue</td>" in body
    assert "<td>7</td>\n<td>white/brown</td>\n<td>white/brown</td>" in body
    assert "<td>8</td>\n<td>brown</td>\n<td>brown</td>" in body


def test_cat5_wiring_serves_the_diagram_its_content_references() -> None:
    """The rendered page's own image URL must be one the Host actually serves."""
    page = _client().get(f"/a/{APPLET_ID}").get_data(as_text=True)
    src = f'src="/a/{APPLET_ID}/assets/cat5-pinout.svg"'

    assert src in page
    assert _client().get(f"/a/{APPLET_ID}/assets/cat5-pinout.svg").status_code == 200


def test_cat5_wiring_appears_on_the_browse_page() -> None:
    body = _client().get("/").get_data(as_text=True)

    assert f'href="/a/{APPLET_ID}"' in body
    assert "Cat5 wiring colours" in body
