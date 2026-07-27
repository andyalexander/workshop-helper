"""The `pipe-bender` worked example (spec §11.2).

The kitchen sink: modes, `keyed_by` calibration, the four-argument
`compute(mode, inputs, calibration)`, `InvalidInput`, and the graphic — the only
Applet in the project that reaches any of them.

The numbers below are the bench-verified fixtures from `pipe-bender-setback.md`
§6 and `pipe-bender-offset.md` §7, recomputed on the calibrated formers (`R_c` =
70mm and 110mm). They are not round numbers chosen for a test: they are what
this tool is for, and the whole reason the Applet exists is that the figures in
circulation are wrong in ways that are invisible at the one angle anybody
demonstrates.
"""

import sys
from collections.abc import Iterator
from math import pi

import pytest
from conftest import client_for
from flask.testing import FlaskClient

from workshop_helper.discovery import Applet, Index, build_index
from workshop_helper.loader import run_compute
from workshop_helper.roots import BUILTIN_ROOT_NAME, BUILTIN_ROOT_PATH, Root
from workshop_utils import Cell, InvalidInput, Result

BUILTIN = Root(name=BUILTIN_ROOT_NAME, path=BUILTIN_ROOT_PATH)
SINGLE_BEND = "single_bend"
STEP = "step"
TOLERANCE_MM = 0.01


@pytest.fixture(autouse=True)
def _clean_modules() -> Iterator[None]:
    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        del sys.modules[name]


def _index() -> Index:
    return build_index([BUILTIN])


def _bender() -> Applet:
    applet = _index().applet("pipe-bender")
    assert applet is not None
    return applet


def _client() -> FlaskClient:
    return client_for(_index())


def _run(mode: str, **inputs: Cell) -> Result:
    applet = _bender()
    assert applet.calibration is not None
    return run_compute(
        applet, applet.mode(mode), inputs, applet.calibration.resolve(inputs)
    )


# --- The domain content it commits to (§11.2) --------------------------------


@pytest.mark.parametrize(
    ("size", "angle", "setback"),
    [
        # At 90°, tan(45°) = 1, so the setback *is* the centreline radius — which
        # is what makes one measurement at 90° calibrate the whole angle range.
        ("15mm", 90.0, 70.0),
        ("22mm", 90.0, 110.0),
        ("15mm", 45.0, 28.99),
        ("22mm", 45.0, 45.56),
        ("15mm", 30.0, 18.76),
    ],
)
def test_setback_is_the_centreline_radius_times_tan_half_the_angle(
    size: str, angle: float, setback: float
) -> None:
    result = _run(SINGLE_BEND, size=size, angle=angle)

    assert result.outputs["setback"] == pytest.approx(setback, abs=TOLERANCE_MM)


def test_the_former_radius_is_calibration_and_both_rows_are_measured() -> None:
    """15mm = 70.0 and 22mm = 110.0, measured to the centreline (#17, #22)."""
    calibration = _bender().calibration

    assert calibration is not None
    assert calibration.keyed_by == "size"
    assert calibration.values == {
        "15mm": {"r_centreline": 70.0},
        "22mm": {"r_centreline": 110.0},
    }


def test_28mm_is_not_offered() -> None:
    """Nobody has measured one, and §1.2 forbids deriving it from the other two."""
    size = next(i for i in _bender().inputs if i.name == "size")

    assert size.choices == ("15mm", "22mm")


@pytest.mark.parametrize(
    ("size", "angle", "offset", "marks", "gain", "min_step"),
    [
        ("15mm", 30.0, 60.0, 119.14, 0.86, 18.76),
        ("15mm", 45.0, 100.0, 138.41, 3.01, 41.01),
        ("15mm", 60.0, 100.0, 107.94, 7.53, 70.00),
        ("22mm", 30.0, 80.0, 158.65, 1.35, 29.47),
        ("22mm", 45.0, 120.0, 164.97, 4.73, 64.44),
        ("22mm", 60.0, 150.0, 161.38, 11.83, 110.00),
    ],
)
def test_the_offset_fixtures_from_the_bench(
    size: str, angle: float, offset: float, marks: float, gain: float, min_step: float
) -> None:
    """One committed convention: both marks on straight pipe, `D·cosec θ − gain`."""
    outputs = _run(STEP, size=size, angle=angle, offset=offset).outputs

    assert outputs["mark_distance"] == pytest.approx(marks, abs=TOLERANCE_MM)
    assert outputs["gain"] == pytest.approx(gain, abs=TOLERANCE_MM)
    assert outputs["min_step"] == pytest.approx(min_step, abs=TOLERANCE_MM)


@pytest.mark.parametrize(
    ("angle", "transposed", "correct"),
    [(30.0, 1.2, 2.0), (60.0, 2.0, 1.155)],
)
def test_the_multiplier_is_not_the_transposed_one(
    angle: float, transposed: float, correct: float
) -> None:
    """The trade's 30°/60° multipliers are swapped, and this is the whole case.

    `1.2` is taught for 30° where `1/sin 30°` is `2` — a 31–64mm error against a
    ±2mm tolerance, and invisible at 45°, the fixed point of the swap and the one
    angle ever demonstrated.
    """
    step = 150.0
    marks = _run(STEP, size="15mm", angle=angle, offset=step).outputs["mark_distance"]
    assert isinstance(marks, float)
    multiplier = marks / step

    # Under the cosecant, and near it: the gap is the gain, which is emitted.
    assert multiplier == pytest.approx(correct, abs=0.06)
    assert abs(multiplier - transposed) > 0.5


def test_gain_is_emitted_as_a_number_rather_than_a_caveat() -> None:
    """Showing your working; §6.2 has no advisory channel and wants none."""
    outputs = _bender().mode(STEP).outputs

    assert [o.name for o in outputs if o.primary] == ["mark_distance"]
    assert "gain" in {o.name for o in outputs}


# --- The refusal, and the graphic (§10.2, §6.1, §1.5) ------------------------


def test_a_step_below_the_geometric_floor_is_refused_not_rounded() -> None:
    """Below `2·R_c·(1 − cos θ)` the arcs meet: the step is impossible, not tight."""
    with pytest.raises(InvalidInput) as raised:
        _run(STEP, size="22mm", angle=60.0, offset=50.0)

    assert raised.value.inputs == ("offset", "angle")
    assert "110mm" in raised.value.message


def test_the_floor_is_named_as_the_geometry_and_not_as_the_tool() -> None:
    """The owner's measured minimum is higher — 150mm here — and is not modelled.

    A number labelled *"smallest step"* that the bender cannot actually pull is a
    §1.5-shaped error: invisible in the figure, and a mis-cut pipe at the bench.
    """
    label = next(o for o in _bender().mode(STEP).outputs if o.name == "min_step").label

    assert label == "Smallest step the geometry allows"
    with pytest.raises(InvalidInput) as raised:
        _run(STEP, size="22mm", angle=60.0, offset=50.0)
    assert "the bender wants more" in raised.value.message


def test_the_smallest_possible_step_is_accepted() -> None:
    """The floor is a floor, not a gap — 110mm on the 22mm former at 60°.

    And it is where the two ways of writing the mark gap meet: with no straight
    left between the arcs, `D·cosec θ − gain` is exactly one arc length,
    `R_c·θ` = 110 × π/3.
    """
    result = _run(STEP, size="22mm", angle=60.0, offset=110.0)

    assert result.outputs["mark_distance"] == pytest.approx(
        110 * pi / 3, abs=TOLERANCE_MM
    )


@pytest.mark.parametrize("mode", [SINGLE_BEND, STEP])
def test_every_result_carries_its_own_svg(mode: str) -> None:
    graphic = _run(mode, size="15mm", angle=45.0, offset=100.0).graphic

    assert graphic is not None
    assert graphic.startswith("<svg") and graphic.endswith("</svg>")
    assert "<path" in graphic


def test_the_single_bend_graphic_names_the_point_it_measures_to() -> None:
    """The number has been wrong three times, and every time it was this (§1.5)."""
    graphic = _run(SINGLE_BEND, size="15mm", angle=90.0).graphic or ""

    assert "vertex of the two centrelines" in graphic
    assert "bend starts here" in graphic


def test_the_offset_graphic_carries_the_sequence() -> None:
    """Both marks on straight pipe, before either bend — the accepted cost's only
    safeguard, and a property no Output could carry."""
    graphic = _run(STEP, size="15mm", angle=45.0, offset=100.0).graphic or ""

    assert "straight pipe" in graphic
    assert ">1</text>" in graphic and ">2</text>" in graphic


# --- The whole thing, through the Host (§2.8, §4.5, §4.6) --------------------


def test_it_computes_on_open_in_its_default_mode() -> None:
    body = _client().get("/a/pipe-bender").get_data(as_text=True)

    assert "Single bend" in body
    assert "Setback" in body and "28.99" in body
    assert "<svg" in body


def test_switching_mode_changes_the_headline_and_the_fields() -> None:
    body = (
        _client()
        .post(
            "/a/pipe-bender/compute",
            data={"mode": STEP, "size": "15mm", "angle": "45"},
        )
        .get_data(as_text=True)
    )

    assert 'name="offset"' in body
    assert "Distance between marks" in body
    assert "138.41" in body


def test_an_impossible_step_lands_on_the_offset_field() -> None:
    body = (
        _client()
        .post(
            "/a/pipe-bender/compute",
            data={"mode": STEP, "size": "22mm", "angle": "60", "offset": "50"},
        )
        .get_data(as_text=True)
    )

    assert 'id="err-offset"' in body
    assert "not achievable" in body
    assert "<details>" not in body
