"""The `thread-finder` worked example (spec §11.3, resolving #25 and #27).

The ranking is tested, the reference figures are not: a corrected transcription
must change an answer without changing a rule, and a test that pinned M8's tap
drill would make the outstanding bench spot-check a test failure rather than a
correction.
"""

import sys
from collections.abc import Iterator

import pytest
from conftest import client_for

from workshop_helper.discovery import Index, build_index
from workshop_helper.loader import run_compute
from workshop_helper.roots import BUILTIN_ROOT_NAME, BUILTIN_ROOT_PATH, Root
from workshop_utils import Group, Result, Row, Table

BUILTIN = Root(name=BUILTIN_ROOT_NAME, path=BUILTIN_ROOT_PATH)
MM = "mm"
TPI = "TPI"

SERIES, DESIGNATION, MAJOR, PITCH, FLANK, DRILL, PROVENANCE = range(7)


@pytest.fixture(autouse=True)
def _clean_modules() -> Iterator[None]:
    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        del sys.modules[name]


def _index() -> Index:
    return build_index([BUILTIN])


def _find(
    diameter: float,
    pitch: float,
    pitch_unit: str = MM,
    metric_only: bool = False,
) -> Result:
    applet = _index().applet("thread-finder")
    assert applet is not None
    return run_compute(
        applet,
        applet.mode(),
        {
            "diameter": diameter,
            "pitch": pitch,
            "pitch_unit": pitch_unit,
            "metric_only": metric_only,
        },
    )


def _table(result: Result) -> Table:
    assert result.table is not None
    return result.table


def _rows(result: Result) -> list[Row]:
    """Every row, tied or not — the ranking, flattened back out."""
    return [row for group in _table(result).groups() for row in group.rows]


def _designations(result: Result) -> list[str]:
    return [str(row.cells[DESIGNATION]) for row in _rows(result)]


def _tied(result: Result) -> list[Group]:
    """The groups the Applet declined to split."""
    return [group for group in _table(result).groups() if group.flag]


def test_the_manifest_loads_as_an_indexed_calculator() -> None:
    applet = _index().applet("thread-finder")

    assert applet is not None
    assert applet.type == "calculator"
    assert [i.name for i in applet.inputs] == [
        "diameter",
        "pitch",
        "pitch_unit",
        "metric_only",
    ]
    assert [o.name for o in applet.outputs] == ["pitch_mm", "candidates"]


def test_the_column_set_is_the_fixed_one() -> None:
    """Settled by #27; the Applet does not get to vary it per search."""
    assert _table(_find(8.0, 1.25)).columns == (
        "Series",
        "Designation",
        "Major Ø (mm)",
        "Pitch (mm)",
        "Flank angle (°)",
        "Tap drill (mm)",
        "Provenance",
    )


# --- Pitch-first, system-blind ranking (#27) ---------------------------------


def test_the_nearest_diameter_leads_among_pitch_matches() -> None:
    result = _find(diameter=8.1, pitch=1.25)

    assert _designations(result)[0] == "M8 × 1.25"


def test_pitch_gates_hard_rather_than_ranking_a_near_miss_low() -> None:
    """A wrong pitch is a wrong thread, not a worse candidate."""
    assert "M8 × 1.25" not in _designations(_find(diameter=8.0, pitch=1.0))


def test_a_pitch_nothing_matches_returns_no_candidates_and_no_table() -> None:
    result = _find(diameter=8.0, pitch=1.11)

    assert result.outputs["candidates"] == 0
    assert result.table is None


def test_diameter_orders_but_never_admits_the_wrong_pitch() -> None:
    """The confusion pitch-first exists to close: BSW 3/8" against M10."""
    designations = _designations(_find(diameter=9.6, pitch=25.4 / 16))

    assert '3/8" BSW' in designations
    assert not any(name.startswith("M10") for name in designations)


def test_the_search_is_system_blind() -> None:
    """One reading, every series — the whole point of an *unknown* fastener."""
    found = {str(row.cells[SERIES]) for row in _rows(_find(diameter=6.35, pitch=1.27))}

    assert {"UNC", "BSW"} <= found


# --- The reciprocal conversion (§4.4, #27) -----------------------------------


def test_tpi_converts_reciprocally_inside_compute() -> None:
    result = _find(diameter=6.35, pitch=20, pitch_unit=TPI)

    assert result.outputs["pitch_mm"] == pytest.approx(1.27)
    assert '1/4" BSW' in _designations(result)


def test_the_conversion_the_dual_unit_input_exists_to_prevent() -> None:
    """`25.4/20` hand-rounded to 1.3 is the noise `pitch_unit` removes (#27)."""
    hand_converted = _find(diameter=6.35, pitch=1.3)

    assert hand_converted.outputs["candidates"] == 0
    assert hand_converted.table is None
    assert _find(diameter=6.35, pitch=20, pitch_unit=TPI).table is not None


def test_the_normalised_pitch_is_the_headline() -> None:
    """Not a best match: a winner in the large type is the silent one (§11.3)."""
    applet = _index().applet("thread-finder")

    assert applet is not None
    (primary,) = [output for output in applet.outputs if output.primary]
    assert (primary.name, primary.unit) == ("pitch_mm", "mm")


# --- Declining honestly (§11.3) ----------------------------------------------


def test_the_quarter_inch_collision_is_a_flagged_tied_group() -> None:
    """1/4" UNC and 1/4" BSW are identical in both measurements (#25 §5.5)."""
    (group,) = [g for g in _tied(_find(6.35, 20, TPI)) if len(g.rows) > 1]
    tied = {str(row.cells[DESIGNATION]) for row in group.rows}

    assert {'1/4" BSW', "1/4-20 UNC"} <= tied
    assert "flank angle" in (group.flag or "")


def test_the_13_ba_collision_is_a_flagged_tied_group() -> None:
    """13 BA and M1.2 are identical in both dimensions (#25 §5.4)."""
    tied = {
        str(row.cells[DESIGNATION])
        for group in _tied(_find(1.2, 0.25))
        for row in group.rows
    }

    assert {"13 BA", "M1.2 × 0.25"} <= tied


def test_two_collisions_in_one_ranking_stay_two_refusals() -> None:
    """13 BA/M1.2 and 14 BA/M1 read alike and are 0.2mm apart: not one group."""
    groups = _tied(_find(1.2, 0.25))

    assert len(groups) == 2
    assert all(len(group.rows) == 2 for group in groups)
    assert (
        len({round(float(str(group.rows[0].cells[MAJOR])), 3) for group in groups}) == 2
    )


def test_a_tied_group_never_hides_a_member_behind_a_winner() -> None:
    (group, *_) = _tied(_find(6.35, 20, TPI))

    assert len(group.rows) > 1


def test_a_lone_candidate_is_not_flagged_as_tied() -> None:
    """A flag is a refusal; an unambiguous answer is not one."""
    groups = _table(_find(diameter=59.6, pitch=25.4 / 11)).groups()
    (lone,) = [g for g in groups if str(g.rows[0].cells[DESIGNATION]) == "G 2"]

    assert lone.flag is None and len(lone.rows) == 1


# --- `metric_only`, the `bool` Input (§11.3) ---------------------------------


def test_metric_only_suppresses_the_imperial_series() -> None:
    """Suppression, not a different search: the gate and the order are untouched."""
    everything = {str(row.cells[SERIES]) for row in _rows(_find(6.35, 20, TPI))}
    suppressed = {
        str(row.cells[SERIES]) for row in _rows(_find(6.35, 20, TPI, metric_only=True))
    }

    assert {"UNC", "BSW"} <= everything
    assert suppressed and not suppressed & {"UNC", "UNF", "BSW", "BSF", "BA", "BSPP"}


def test_a_gauge_reading_admits_the_pitch_next_door_within_its_own_precision() -> None:
    """20 TPI is 1.27mm and M8 is 1.25 — the confusion is real, so both show."""
    designations = _designations(_find(diameter=8.0, pitch=20, pitch_unit=TPI))

    assert "M8 × 1.25" in designations


def test_metric_only_off_by_default_is_the_uk_mixed_unit_reality() -> None:
    applet = _index().applet("thread-finder")

    assert applet is not None
    (metric_only,) = [i for i in applet.inputs if i.name == "metric_only"]
    assert metric_only.default is False


# --- Provenance and the honest empty cell (#25 §3.4) -------------------------


def test_every_row_carries_its_own_provenance() -> None:
    rows = _rows(_find(diameter=6.35, pitch=20, pitch_unit=TPI))

    assert all(str(row.cells[PROVENANCE]).strip() for row in rows)


def test_dimensions_and_drills_are_sourced_separately_on_the_same_row() -> None:
    """Two documents describe one fastener; one column would bury that (#22)."""
    (m8,) = [
        row
        for row in _rows(_find(8.0, 1.25))
        if str(row.cells[DESIGNATION]) == "M8 × 1.25"
    ]

    assert "ISO 262" in str(m8.cells[PROVENANCE])
    assert "ISO 2306" in str(m8.cells[PROVENANCE])


def test_a_series_with_no_published_drill_emits_nothing_rather_than_a_formula() -> None:
    """`major − pitch` dressed as a lookup is the failure #25 exists to prevent."""
    (ba,) = [
        row for row in _rows(_find(1.2, 0.25)) if str(row.cells[DESIGNATION]) == "13 BA"
    ]

    assert ba.cells[DRILL] is None
    assert "no published drill" in str(ba.cells[PROVENANCE])


def test_the_pipe_series_ships_but_withholds_its_drill() -> None:
    """G 1/2 measures 20.955mm; excluded, the finder answers confidently wrong."""
    (g_half,) = [
        row
        for row in _rows(_find(20.9, 14, TPI))
        if str(row.cells[DESIGNATION]) == "G 1/2"
    ]

    assert g_half.cells[DRILL] is None
    assert "pipe thread" in str(g_half.cells[PROVENANCE])


def test_flank_angle_is_a_column_and_not_an_input() -> None:
    """Resolve-then-measure: promoting it would cost compute-on-open (§11.3)."""
    applet = _index().applet("thread-finder")

    assert applet is not None
    assert not any("angle" in i.name for i in applet.inputs)
    assert "Flank angle (°)" in _table(_find(8.0, 1.25)).columns


# --- On the page -------------------------------------------------------------


def test_the_page_computes_on_open() -> None:
    """Every Input is defaulted, so opening it is already an answer (§4.6)."""
    body = client_for(_index()).get("/a/thread-finder").get_data(as_text=True)

    assert "Fill in the Inputs" not in body
    assert "M6 × 1" in body  # the defaults: 6mm, 1mm pitch
    assert 'name="metric_only"' in body


def test_the_round_trip_renders_the_ranked_table_with_its_tied_group() -> None:
    body = (
        client_for(_index())
        .post(
            "/a/thread-finder/compute",
            data={"diameter": "6.35", "pitch": "20", "pitch_unit": "TPI"},
            headers={"HX-Request": "true"},
        )
        .get_data(as_text=True)
    )

    assert "<table" in body
    assert "1/4-20 UNC" in body
    assert "flank angle" in body
    assert "1.27" in body  # the normalised pitch, shown large
