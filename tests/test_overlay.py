"""The Overlay: save-as-defaults, calibration overrides, and the drop rule.

Spec §8, §8.1, §8.2, §5.5, §9, §4.6, §10.4; ADR-0007.

The Host never writes a Manifest, so every test here that asserts an override
took effect is also asserting the author's file was left alone — checked once,
directly, in ``test_no_manifest_is_ever_written``.
"""

import json
import os
import sys
import threading
import time
from collections.abc import Iterator
from html import unescape
from pathlib import Path

import pytest
from conftest import client_for
from flask.testing import FlaskClient

from workshop_helper.discovery import Applet, build_index
from workshop_helper.manifest import read_manifest
from workshop_helper.overlay import (
    OVERLAY_FILENAME,
    UNREADABLE_SUFFIX,
    Overlay,
    overlaid,
)
from workshop_helper.roots import Root

BENDER = """
default_mode = "single_bend"

[applet]
type = "calculator"
name = "Bender"

[inputs.size]
kind    = "choice"
label   = "Pipe size"
choices = ["15mm", "22mm"]
default = "15mm"

[inputs.angle]
kind    = "number"
label   = "Bend angle"
min     = 1
max     = 90
step    = 1
default = 45

[inputs.offset]
kind   = "number"
label  = "Step"
min    = 1

[calibration]
keyed_by = "size"

[calibration.values.15mm]
r_centreline = 70.0

[calibration.values.22mm]
r_centreline = 110.0

[modes.single_bend]
label   = "Single bend"
inputs  = ["size", "angle"]
outputs = [{ name = "radius", label = "Radius", unit = "mm" }]

[modes.step]
label   = "Step"
inputs  = ["size", "angle", "offset"]
outputs = [{ name = "radius", label = "Radius", unit = "mm" }]
"""

ECHOES = """
from workshop_utils import Result


def compute(mode, inputs, calibration):
    return Result(outputs={"radius": calibration["r_centreline"]})
"""

# The two-Input Applet §4.6 is about: nothing computes until the user supplies
# `angle`, and a saved default is what changes that.
PARTIAL = """
outputs = [{ name = "doubled", label = "Doubled" }]

[applet]
type = "calculator"
name = "Partial"

[inputs.angle]
kind  = "number"
label = "Bend angle"
min   = 1
max   = 90
"""

DOUBLES = """
from workshop_utils import Result


def compute(inputs):
    return Result(outputs={"doubled": inputs["angle"] * 2})
"""

# A calibration field name is the author's own free text (§5.2), so it may hold
# the very character the attributes carrying it are quoted with (#47).
QUOTED = """
outputs = [{ name = "radius", label = "Radius", unit = "mm" }]

[applet]
type = "calculator"
name = "Bender"

[calibration.values]
'r"centreline' = 70.0
"""

QUOTES = """
from workshop_utils import Result


def compute(inputs, calibration):
    return Result(outputs={"radius": calibration['r"centreline']})
"""


@pytest.fixture(autouse=True)
def _clean_modules() -> Iterator[None]:
    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        del sys.modules[name]


@pytest.fixture
def overlay(tmp_path: Path) -> Overlay:
    return Overlay(tmp_path / "home" / OVERLAY_FILENAME)


def _applet(
    tmp_path: Path, manifest: str = BENDER, source: str = ECHOES, name: str = "bender"
) -> Path:
    folder = tmp_path / "root" / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.toml").write_text(manifest)
    (folder / "applet.py").write_text(source)
    return folder


def _client(tmp_path: Path, overlay: Overlay, **kwargs: str) -> FlaskClient:
    _applet(tmp_path, **kwargs)
    index = build_index([Root(name="built-in", path=tmp_path / "root")])
    return client_for(index, overlay)


def _indexed(tmp_path: Path, **kwargs: str) -> Applet:
    _applet(tmp_path, **kwargs)
    return build_index([Root(name="built-in", path=tmp_path / "root")]).applets[0]


# --- The file: Host-owned, JSON, and never a Manifest (§8, ADR-0007) ---------


def test_saved_overrides_persist_to_overlay_json(overlay: Overlay) -> None:
    """JSON, written with the stdlib, in a file the Host wholly owns."""
    overlay.save_defaults("bender", {"angle": 30.0})

    assert overlay.path.name == OVERLAY_FILENAME
    assert json.loads(overlay.path.read_text()) == {
        "bender": {"defaults": {"angle": 30.0}}
    }


def test_no_manifest_is_ever_written(tmp_path: Path, overlay: Overlay) -> None:
    """Every Root is read-only to the Host — no probing, no write-back (§8)."""
    folder = _applet(tmp_path)
    manifest = folder / "manifest.toml"
    before = manifest.read_bytes()
    client = _client(tmp_path, overlay)

    client.post("/a/bender/defaults", data={"mode": "single_bend", "angle": "30"})
    client.post(
        "/a/bender/calibration",
        data={
            "mode": "single_bend",
            "size": "22mm",
            "angle": "45",
            "cal:r_centreline": "108.5",
        },
    )

    assert manifest.read_bytes() == before


def test_an_input_and_a_calibration_field_of_one_name_do_not_collide(
    tmp_path: Path, overlay: Overlay
) -> None:
    """Namespaced by override kind, which is exactly what §8 promises."""
    overlay.save_defaults("bender", {"r_centreline": 1.0})
    overlay.save_calibration("bender", "15mm", {"r_centreline": 71.5})

    assert overlay.defaults("bender") == {"r_centreline": 1.0}
    assert overlay.calibration("bender") == {"15mm": {"r_centreline": 71.5}}


def test_entries_are_keyed_by_applet_id_alone(overlay: Overlay) -> None:
    """No provenance in the key: ids are already unique across the loaded set."""
    overlay.save_defaults("bender", {"angle": 30.0})
    overlay.save_defaults("finder", {"angle": 60.0})

    assert overlay.defaults("bender") == {"angle": 30.0}
    assert overlay.defaults("finder") == {"angle": 60.0}


def test_an_unreadable_or_corrupt_overlay_is_simply_no_overrides(
    tmp_path: Path,
) -> None:
    """Discardable by definition, so an unusable file is a pristine Host (§8.2)."""
    path = tmp_path / OVERLAY_FILENAME
    path.write_text("{ this is not json")

    assert Overlay(path).defaults("bender") == {}
    assert Overlay(tmp_path / "nothing-here.json").defaults("bender") == {}


# --- The write: atomic, and serialised within the process (#48) --------------


def _raises_oserror(*args: object, **kwargs: object) -> None:
    """Stand in for a full disk or a failing device at a chosen moment."""
    raise OSError("no space left on device")


# Both sides of the moment the new bytes become the file: `fsync` is before they
# are durable, `replace` is the publication itself. The old in-place write had
# already truncated the target before either.
FAILURE_POINTS = ["fsync", "replace"]


@pytest.mark.parametrize("breaks", FAILURE_POINTS)
def test_a_write_that_fails_partway_leaves_the_previous_file_intact(
    overlay: Overlay, monkeypatch: pytest.MonkeyPatch, breaks: str
) -> None:
    """The target is never truncated, so there is no torn state to read back.

    A partial file would not surface as an error — `_read` would take it for *no
    overrides at all*, and the next ordinary save would build on that `{}` and
    make the loss permanent. Calibration is measured off physical kit; it is not
    reconstructible from anything the Host holds.
    """
    overlay.save_defaults("bender", {"angle": 30.0})
    before = overlay.path.read_bytes()

    monkeypatch.setattr(os, breaks, _raises_oserror)
    with pytest.raises(OSError):
        overlay.save_defaults("bender", {"angle": 60.0})

    monkeypatch.undo()
    assert overlay.path.read_bytes() == before
    assert overlay.defaults("bender") == {"angle": 30.0}


@pytest.mark.parametrize("breaks", FAILURE_POINTS)
def test_a_failed_write_leaves_no_litter_beside_the_file(
    overlay: Overlay, monkeypatch: pytest.MonkeyPatch, breaks: str
) -> None:
    """The temp file is a sibling, so it must not outlive the attempt."""
    overlay.save_defaults("bender", {"angle": 30.0})

    monkeypatch.setattr(os, breaks, _raises_oserror)
    with pytest.raises(OSError):
        overlay.save_defaults("bender", {"angle": 60.0})

    monkeypatch.undo()
    assert [p.name for p in overlay.path.parent.iterdir()] == [OVERLAY_FILENAME]


def test_concurrent_saves_to_different_applets_lose_neither(
    overlay: Overlay, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Flask serves on threads, so the read-modify-write needs serialising.

    Widened deliberately: the window between reading the file and replacing it
    is small enough that an unserialised version passes this by luck most runs.
    """
    real_load = Overlay._loaded

    def _slow_load(self: Overlay) -> dict[str, object] | None:
        entries = real_load(self)
        time.sleep(0.005)
        return entries

    # `_loaded`, not `_read`: the write path is what needs widening, and it is
    # `_loaded` that `_store` calls.
    monkeypatch.setattr(Overlay, "_loaded", _slow_load)
    savers = [
        threading.Thread(target=overlay.save_defaults, args=(f"applet{n}", {"a": 1.0}))
        for n in range(8)
    ]
    for saver in savers:
        saver.start()
    for saver in savers:
        saver.join()

    monkeypatch.undo()
    assert all(overlay.defaults(f"applet{n}") == {"a": 1.0} for n in range(8))


def test_an_unreadable_file_is_moved_aside_rather_than_written_over(
    overlay: Overlay,
) -> None:
    """Reads stay tolerant, but the recovery path stops destroying the evidence.

    §8.2 licenses *the user* discarding this file. It does not license the Host
    discarding it on their behalf, silently, on the next ordinary save.
    """
    overlay.path.parent.mkdir(parents=True, exist_ok=True)
    overlay.path.write_text('{"bender": {"defaults": {"angle": 30.0}, corrupt')
    corrupt = overlay.path.read_bytes()

    overlay.save_defaults("finder", {"angle": 60.0})

    aside = overlay.path.with_name(overlay.path.name + UNREADABLE_SUFFIX)
    assert aside.read_bytes() == corrupt
    assert overlay.defaults("finder") == {"angle": 60.0}


def test_a_second_corruption_does_not_destroy_the_first_preserved_copy(
    overlay: Overlay,
) -> None:
    """`rename` replaces its target, so a fixed name would defeat the point."""
    overlay.path.parent.mkdir(parents=True, exist_ok=True)
    for damage in ("first damage", "second damage"):
        overlay.path.write_text(damage)
        overlay.save_defaults("finder", {"angle": 60.0})

    aside = sorted(
        path.read_text()
        for path in overlay.path.parent.iterdir()
        if UNREADABLE_SUFFIX in path.name
    )
    assert aside == ["first damage", "second damage"]


def test_a_file_that_cannot_be_read_at_all_is_not_treated_as_damage(
    overlay: Overlay, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing disk says nothing about the contents, so nothing is moved.

    Renaming on a transient `PermissionError` would take a perfectly good file
    out of use on the strength of an error that had not read a byte of it.
    """
    overlay.save_defaults("bender", {"angle": 30.0})
    before = overlay.path.read_bytes()

    def _refuses(*args: object, **kwargs: object) -> str:
        raise PermissionError("permission denied")

    monkeypatch.setattr(Path, "read_text", _refuses)
    with pytest.raises(OSError):
        overlay.save_defaults("bender", {"angle": 60.0})

    monkeypatch.undo()
    assert overlay.path.read_bytes() == before
    assert not any(UNREADABLE_SUFFIX in p.name for p in overlay.path.parent.iterdir())


# --- Saved input defaults (§8) -----------------------------------------------


def test_a_saved_default_populates_the_form(tmp_path: Path, overlay: Overlay) -> None:
    client = _client(tmp_path, overlay)

    client.post("/a/bender/defaults", data={"mode": "single_bend", "angle": "30"})

    body = client.get("/a/bender").get_data(as_text=True)
    assert 'name="angle"' in body
    assert 'value="30.0"' in body


def test_a_saved_default_is_a_default_for_compute_on_open(
    tmp_path: Path, overlay: Overlay
) -> None:
    """Compute-on-open is user-dependent, and this is what makes it so (§4.6)."""
    client = _client(tmp_path, overlay, manifest=PARTIAL, source=DOUBLES)

    assert "press Compute" in client.get("/a/bender").get_data(as_text=True)

    client.post("/a/bender/defaults", data={"angle": "21"})

    body = client.get("/a/bender").get_data(as_text=True)
    assert "press Compute" not in body
    assert "42" in body


def test_saving_keeps_the_valid_fields_of_a_half_filled_form(
    tmp_path: Path, overlay: Overlay
) -> None:
    """The gate in front of compute() is not a gate in front of the Overlay."""
    client = _client(tmp_path, overlay)

    client.post(
        "/a/bender/defaults",
        data={"mode": "step", "size": "22mm", "angle": "500", "offset": "120"},
    )

    assert overlay.defaults("bender") == {"size": "22mm", "offset": 120.0}


def test_saving_in_one_mode_keeps_the_other_modes_saved_defaults(
    tmp_path: Path, overlay: Overlay
) -> None:
    """The form carries one mode's Inputs; the Overlay holds the whole pool."""
    client = _client(tmp_path, overlay)

    client.post(
        "/a/bender/defaults",
        data={"mode": "step", "size": "15mm", "angle": "45", "offset": "120"},
    )
    client.post(
        "/a/bender/defaults",
        data={"mode": "single_bend", "size": "22mm", "angle": "30"},
    )

    assert overlay.defaults("bender") == {
        "size": "22mm",
        "angle": 30.0,
        "offset": 120.0,
    }


def test_the_strip_can_put_the_authors_defaults_back(
    tmp_path: Path, overlay: Overlay
) -> None:
    client = _client(tmp_path, overlay)
    client.post("/a/bender/defaults", data={"mode": "single_bend", "angle": "30"})

    client.post("/a/bender/defaults", data={"reset": "all"})

    assert overlay.defaults("bender") == {}
    assert 'value="45"' in client.get("/a/bender").get_data(as_text=True)


def test_a_reset_stays_in_the_mode_it_was_pressed_in(
    tmp_path: Path, overlay: Overlay
) -> None:
    """The reset is about the *values*, and the mode is not one of them (#45).

    A mode changes **what exists**, so falling back to `default_mode` here would
    change the shape of the form under someone who only asked for the author's
    figures back — different Inputs, different Outputs, and no word about it.
    """
    client = _client(tmp_path, overlay)
    client.post("/a/bender/defaults", data={"mode": "step", "angle": "30"})

    body = client.post(
        "/a/bender/defaults", data={"mode": "step", "reset": "all"}
    ).get_data(as_text=True)

    assert 'value="step" selected' in body
    # `offset` exists in `step` and not in `single_bend`, so its presence is the
    # form still having the shape the user was working in.
    assert 'name="offset"' in body


# --- The drop rule: invalid and orphaned entries (§8, §10.4) -----------------


@pytest.mark.parametrize(
    ("saved", "because"),
    [
        ({"angle": 500.0}, "the author narrowed `max` under a saved figure"),
        ({"angle": 45.5}, "the author's `step` no longer admits it"),
        ({"angle": "45"}, "a number Input, and this is a string"),
        ({"size": "28mm"}, "no longer one of the choices"),
        ({"size": 22.0}, "a choice Input, and this is a number"),
        ({"nosuch": 1.0}, "the author renamed or dropped the Input"),
    ],
)
def test_an_entry_that_no_longer_fits_is_dropped_silently(
    tmp_path: Path, overlay: Overlay, saved: dict[str, object], because: str
) -> None:
    """Nobody is at fault, so nothing is reported: the form shows what is in use."""
    overlay.save_defaults("bender", saved)  # type: ignore[arg-type]
    client = _client(tmp_path, overlay)

    body = client.get("/a/bender").get_data(as_text=True)

    assert client.get("/a/bender").status_code == 200
    assert "faulty" not in body
    assert 'value="45"' in body  # the author's default, unchanged
    assert 'value="500' not in body


def test_an_orphaned_entry_is_never_pruned(tmp_path: Path, overlay: Overlay) -> None:
    """A missing Applet is not evidence it is gone — its Root may be unmounted."""
    overlay.save_defaults("unmounted", {"angle": 30.0})
    client = _client(tmp_path, overlay)

    client.post("/a/bender/defaults", data={"mode": "single_bend", "angle": "30"})

    assert overlay.defaults("unmounted") == {"angle": 30.0}


# --- Calibration overrides (§8.1, §5.5) --------------------------------------


def test_a_calibration_override_reaches_compute(
    tmp_path: Path, overlay: Overlay
) -> None:
    overlay.save_calibration("bender", "22mm", {"r_centreline": 108.5})
    client = _client(tmp_path, overlay)

    body = client.post(
        "/a/bender/compute", data={"mode": "single_bend", "size": "22mm", "angle": "45"}
    ).get_data(as_text=True)

    assert "108.5" in body


def test_calibration_merges_field_by_field_not_slice_replacement(
    tmp_path: Path, overlay: Overlay
) -> None:
    """A field the author adds later must survive a stored row that predates it."""
    overlay.save_calibration("bender", "15mm", {"r_centreline": 71.5})
    grown = BENDER.replace(
        "[calibration.values.15mm]\nr_centreline = 70.0",
        "[calibration.values.15mm]\nr_centreline = 70.0\nbacklash = 0.04",
    ).replace(
        "[calibration.values.22mm]\nr_centreline = 110.0",
        "[calibration.values.22mm]\nr_centreline = 110.0\nbacklash = 0.04",
    )
    applet = _indexed(tmp_path, manifest=grown)

    merged = overlaid(applet, overlay).calibration

    assert merged is not None
    assert merged.values["15mm"] == {"r_centreline": 71.5, "backlash": 0.04}


def test_a_precise_measurement_survives_the_round_trip_to_the_box(
    tmp_path: Path, overlay: Overlay
) -> None:
    """The box a value is read back out of must round-trip it exactly.

    The Host's display formatting writes six significant figures, which is right
    for a Result and wrong here: pressing Save without touching the field would
    otherwise store `108.568` as though somebody had measured it.
    """
    precise = BENDER.replace("r_centreline = 110.0", "r_centreline = 108.5678901")
    client = _client(tmp_path, overlay, manifest=precise)
    data = {"mode": "single_bend", "size": "22mm", "angle": "45"}

    shown = client.post("/a/bender/compute", data=data).get_data(as_text=True)
    assert 'value="108.5678901"' in shown

    # Saving an untouched field stores nothing: it still equals the author's.
    client.post(
        "/a/bender/calibration", data={**data, "cal:r_centreline": "108.5678901"}
    )
    assert overlay.calibration("bender") == {}


def test_a_calibration_override_is_stored_sparse(
    tmp_path: Path, overlay: Overlay
) -> None:
    """Only what differs from the author, so an untouched field is never pinned."""
    client = _client(tmp_path, overlay)

    client.post(
        "/a/bender/calibration",
        data={
            "mode": "single_bend",
            "size": "15mm",
            "angle": "45",
            "cal:r_centreline": "70.0",
        },
    )
    assert overlay.calibration("bender") == {}

    client.post(
        "/a/bender/calibration",
        data={
            "mode": "single_bend",
            "size": "15mm",
            "angle": "45",
            "cal:r_centreline": "71.5",
        },
    )
    assert overlay.calibration("bender") == {"15mm": {"r_centreline": 71.5}}


@pytest.mark.parametrize(
    ("raw", "because"),
    [
        ("71,5", "a European decimal comma — the commonest way to mistype a figure"),
        ("7l.5", "a letter for a digit"),
        ("inf", "parses as a float, but is not a measurement"),
        ("", "the box emptied: Reset clears a correction, a blank box does not"),
    ],
)
def test_an_unreadable_calibration_box_keeps_the_figure_in_use(
    tmp_path: Path, overlay: Overlay, raw: str, because: str
) -> None:
    """A typo must not delete the bench measurement it was typed over.

    Sparseness (§8.1) and the Overlay's silence (§10.4) both encode as an absent
    key, so a field whose parse failed has to fall back to the figure **in use**
    rather than be left out of the row that replaces it. Left out, it is not
    "unchanged" — it is deleted, and the measurement is gone with no message and
    no undo.
    """
    client = _client(tmp_path, overlay)
    data = {"mode": "single_bend", "size": "15mm", "angle": "45"}

    client.post("/a/bender/calibration", data={**data, "cal:r_centreline": "71.5"})
    assert overlay.calibration("bender") == {"15mm": {"r_centreline": 71.5}}

    shown = client.post(
        "/a/bender/calibration", data={**data, "cal:r_centreline": raw}
    ).get_data(as_text=True)

    assert overlay.calibration("bender") == {"15mm": {"r_centreline": 71.5}}, because
    # §10.4's silence is only honest if the claim it makes is true: the box has
    # to come back showing the figure that is still in force, not the author's.
    assert 'value="71.5"' in shown


@pytest.mark.parametrize(
    ("saved", "because"),
    [
        ({"28mm": {"r_centreline": 99.0}}, "orphaned key: the author dropped the size"),
        ({"15mm": {"r_outside": 99.0}}, "the author renamed the field"),
        ({"15mm": {"r_centreline": "seventy"}}, "the author's field is a number"),
    ],
)
def test_an_invalid_calibration_entry_is_dropped_silently(
    tmp_path: Path, overlay: Overlay, saved: dict[str, dict[str, object]], because: str
) -> None:
    overlay.save_calibration("bender", *next(iter(saved.items())))  # type: ignore[arg-type]
    applet = _indexed(tmp_path)

    merged = overlaid(applet, overlay).calibration

    assert merged is not None
    assert merged.values == {
        "15mm": {"r_centreline": 70.0},
        "22mm": {"r_centreline": 110.0},
    }


def test_a_dropped_entry_leaves_the_rows_rectangular(
    tmp_path: Path, overlay: Overlay
) -> None:
    """§5.3's rule 4 must survive whatever is in the file: shape is the author's."""
    overlay.save_calibration("bender", "15mm", {"backlash": 0.04})
    applet = _indexed(tmp_path)

    merged = overlaid(applet, overlay).calibration

    assert merged is not None
    assert {frozenset(row) for row in merged.values.values()} == {
        frozenset({"r_centreline"})
    }


# --- The Calibration UI (§5.5) and the strip (§9) ----------------------------


def test_the_calibration_disclosure_shows_the_active_key_only(
    tmp_path: Path, overlay: Overlay
) -> None:
    client = _client(tmp_path, overlay)

    body = client.post(
        "/a/bender/compute", data={"mode": "single_bend", "size": "22mm", "angle": "45"}
    ).get_data(as_text=True)

    assert "22mm" in body
    assert 'value="110.0"' in body  # the 22mm slice
    assert 'value="70.0"' not in body  # not the 15mm one


def test_the_disclosure_is_collapsed_and_offers_reset_to_the_author(
    tmp_path: Path, overlay: Overlay
) -> None:
    body = _client(tmp_path, overlay).get("/a/bender").get_data(as_text=True)

    assert '<details class="calibration">' in body  # collapsed: no `open`
    assert "Reset to the author's value" in body


def test_the_disclosure_carries_no_explanatory_prose(
    tmp_path: Path, overlay: Overlay
) -> None:
    """The affordance already says it; a sentence can be wrong where a box cannot."""
    body = _client(tmp_path, overlay).get("/a/bender").get_data(as_text=True)

    assert (
        "<p>"
        not in body.split('<details class="calibration">')[1].split("</details>")[0]
    )


def test_reset_restores_one_field_and_leaves_the_others(
    tmp_path: Path, overlay: Overlay
) -> None:
    overlay.save_calibration("bender", "15mm", {"r_centreline": 71.5})
    overlay.save_calibration("bender", "22mm", {"r_centreline": 108.5})
    client = _client(tmp_path, overlay)

    client.post(
        "/a/bender/calibration",
        data={
            "mode": "single_bend",
            "size": "15mm",
            "angle": "45",
            "reset": "r_centreline",
        },
    )

    assert overlay.calibration("bender") == {"22mm": {"r_centreline": 108.5}}


def test_a_save_that_cannot_resolve_its_key_is_a_refused_request(
    tmp_path: Path, overlay: Overlay
) -> None:
    """A 200 that stored nothing is the one answer this must not give (#46).

    The Host's own form cannot produce this: `keyed_by` is checked at scan to be
    a `choice` whose choices are exactly the calibration keys, and the select
    renders no blank option. So an unresolvable key means the request did not
    come from the disclosure, and the honest answer is that it was malformed —
    not a re-rendered page that looks like a save.
    """
    client = _client(tmp_path, overlay)

    answer = client.post(
        "/a/bender/calibration",
        data={
            "mode": "single_bend",
            "size": "28mm",  # not one of the author's choices, so no slice
            "angle": "45",
            "cal:r_centreline": "108.5",
        },
    )

    assert answer.status_code == 400
    assert overlay.calibration("bender") == {}


def test_hx_vals_is_json_whatever_the_author_named_the_field(
    tmp_path: Path, overlay: Overlay
) -> None:
    """A JSON attribute wants a JSON serialiser, not the HTML escaper (#47).

    Hand-interpolated, a `"` in the name is escaped to `&#34;`, the HTML parser
    turns it back into a real quote inside the attribute, and htmx is handed
    malformed JSON it can only discard.
    """
    client = _client(tmp_path, overlay, manifest=QUOTED, source=QUOTES)

    body = client.get("/a/bender").get_data(as_text=True)

    # The disclosure's own button: the save-as-defaults strip above it carries an
    # `hx-vals` too, and that one is built from Host constants alone.
    disclosure = body.split('<details class="calibration">')[1]
    vals = disclosure.split("hx-vals='")[1].split("'")[0]
    # Through the HTML parser first: the attribute is what the browser hands
    # htmx, entities already resolved.
    assert json.loads(unescape(vals)) == {"reset": 'r"centreline'}


def test_a_field_named_with_a_quote_still_resets(
    tmp_path: Path, overlay: Overlay
) -> None:
    """The behaviour the JSON attribute exists to drive, end to end (#47)."""
    overlay.save_calibration("bender", "", {'r"centreline': 71.5})
    client = _client(tmp_path, overlay, manifest=QUOTED, source=QUOTES)

    client.post("/a/bender/calibration", data={"reset": 'r"centreline'})

    assert overlay.calibration("bender") == {}


def test_a_cross_origin_post_never_reaches_the_store(
    tmp_path: Path, overlay: Overlay
) -> None:
    """The gate is in front of the write, not merely in front of the page (#44).

    Calibration is measured off the physical kit and comes back out as marks on
    a pipe, so a silently rewritten `r_centreline` is wrong work at the bench
    with nothing on screen to suggest it.
    """
    client = _client(tmp_path, overlay)
    correction = {
        "mode": "single_bend",
        "size": "22mm",
        "angle": "45",
        "cal:r_centreline": "1.0",
    }

    refused = client.post(
        "/a/bender/calibration",
        data=correction,
        headers={"Sec-Fetch-Site": "cross-site"},
    )

    assert refused.status_code == 403
    assert overlay.calibration("bender") == {}
    # The same post from the Host's own page is the one that lands.
    client.post("/a/bender/calibration", data=correction)
    assert overlay.calibration("bender") == {"22mm": {"r_centreline": 1.0}}


def test_the_save_as_defaults_strip_sits_under_the_inputs(
    tmp_path: Path, overlay: Overlay
) -> None:
    """The same place on every calculator (§9) — including one with no modes."""
    for manifest, source in ((BENDER, ECHOES), (PARTIAL, DOUBLES)):
        client = _client(tmp_path, overlay, manifest=manifest, source=source)

        body = client.get("/a/bender").get_data(as_text=True)

        # The Inputs form specifically: the sidebar's filter form (#34) is the
        # first form on the page, and the strip belongs to neither of the others.
        form = body.split('id="inputs"')[1].split("</form>")[0]
        assert "Save as defaults" in form
        assert form.index("Compute") < form.index("Save as defaults")


def test_a_calculator_without_calibration_shows_no_disclosure(
    tmp_path: Path, overlay: Overlay
) -> None:
    """The degenerate case is the *absence of a section*, not an empty one (§4.6)."""
    client = _client(tmp_path, overlay, manifest=PARTIAL, source=DOUBLES)

    body = client.get("/a/bender").get_data(as_text=True)

    assert "calibration" not in body
    assert "Save as defaults" in body


# --- The discardable invariant (§8.2) ----------------------------------------


def test_deleting_the_overlay_returns_the_host_to_a_pristine_state(
    tmp_path: Path, overlay: Overlay
) -> None:
    """Nothing the Host cannot reconstruct from Manifests lives only here."""
    client = _client(tmp_path, overlay)
    client.post(
        "/a/bender/defaults",
        data={"mode": "single_bend", "size": "22mm", "angle": "30"},
    )
    client.post(
        "/a/bender/calibration",
        data={
            "mode": "single_bend",
            "size": "22mm",
            "angle": "30",
            "cal:r_centreline": "108.5",
        },
    )
    corrected = client.get("/a/bender").get_data(as_text=True)
    assert 'value="30.0"' in corrected
    assert "108.5" in corrected

    overlay.path.unlink()

    # No restart: the file is re-read on every lookup, so the invariant holds
    # while the Host is running.
    pristine = client.get("/a/bender").get_data(as_text=True)
    authored = read_manifest(tmp_path / "root" / "bender" / "manifest.toml")
    assert 'value="45"' in pristine
    assert "108.5" not in pristine
    assert authored.calibration is not None
    assert authored.calibration.values["22mm"] == {"r_centreline": 110.0}
