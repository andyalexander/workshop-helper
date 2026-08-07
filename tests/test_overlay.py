"""The Overlay: save-as-defaults, calibration overrides, and the drop rule.

Spec §8, §8.1, §8.2, §5.5, §9, §4.6, §10.4; ADR-0007.

The Host never writes a Manifest, so every test here that asserts an override
took effect is also asserting the author's file was left alone — checked once,
directly, in ``test_no_manifest_is_ever_written``.
"""

import json
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import client_for
from flask.testing import FlaskClient

from workshop_helper.discovery import Applet, build_index
from workshop_helper.manifest import read_manifest
from workshop_helper.overlay import OVERLAY_FILENAME, Overlay, overlaid
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
