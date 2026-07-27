"""The form, and the static validation that hard-gates compute() (spec §4.3)."""

import pytest

from workshop_helper.form import build_form, computes_on_open
from workshop_helper.manifest import Input

DIAMETER = Input(name="diameter", kind="number", label="Diameter", unit="mm", min=0.5)
ANGLE = Input(
    name="angle", kind="number", label="Bend angle", unit="°", min=0, max=180, step=1
)
SIZE = Input(
    name="size",
    kind="choice",
    label="Pipe size",
    choices=("15mm", "22mm"),
    default="15mm",
)
METRIC_ONLY = Input(name="metric_only", kind="bool", label="Metric only", default=False)


def test_a_form_on_open_shows_the_declared_defaults() -> None:
    form = build_form((SIZE, METRIC_ONLY), submitted=None)

    size, metric_only = form.fields
    assert size.raw == "15mm"
    assert metric_only.checked is False
    assert form.values == {"size": "15mm", "metric_only": False}


def test_an_input_with_no_default_leaves_its_field_empty_and_the_form_unvalued() -> (
    None
):
    """Nothing to compute with: `compute()` never sees a missing Input (§4.3)."""
    form = build_form((DIAMETER,), submitted=None)

    assert form.fields[0].raw == ""
    assert form.values is None
    assert form.errors == []  # not an error — the user has simply not typed yet


def test_submitted_values_are_parsed_to_their_declared_kinds() -> None:
    form = build_form(
        (DIAMETER, SIZE, METRIC_ONLY),
        submitted={"diameter": "8.5", "size": "22mm", "metric_only": "on"},
    )

    assert form.values == {"diameter": 8.5, "size": "22mm", "metric_only": True}


def test_an_unticked_checkbox_is_false_not_missing() -> None:
    """A browser sends nothing for an unticked box; the Input is still required."""
    form = build_form((METRIC_ONLY,), submitted={})

    assert form.values == {"metric_only": False}


@pytest.mark.parametrize(
    ("declared", "raw", "because"),
    [
        (ANGLE, "", "blank, and every Input is required"),
        (ANGLE, "   ", "whitespace is blank"),
        (ANGLE, "ninety", "not a number"),
        (ANGLE, "nan", "not a number the Host will pass on"),
        (ANGLE, "inf", "not a finite number"),
        (ANGLE, "-1", "below min"),
        (ANGLE, "181", "above max"),
        (ANGLE, "90.5", "off the step grid"),
        (SIZE, "28mm", "not one of the choices"),
        (SIZE, "", "blank"),
    ],
)
def test_an_invalid_value_stops_the_form_from_yielding_values(
    declared: Input, raw: str, because: str
) -> None:
    """This is the hard gate: no values means the route has nothing to run."""
    form = build_form((declared,), submitted={declared.name: raw})

    assert form.values is None
    assert form.errors == [declared.name]
    assert form.fields[0].error is not None


def test_an_invalid_value_is_shown_back_rather_than_swallowed() -> None:
    form = build_form((ANGLE,), submitted={"angle": "200"})

    assert form.fields[0].raw == "200"
    assert "180" in (form.fields[0].error or "")


def test_one_bad_field_does_not_hide_the_others_verdicts() -> None:
    form = build_form((ANGLE, SIZE), submitted={"angle": "200", "size": "28mm"})

    assert form.errors == ["angle", "size"]


def test_the_step_grid_is_anchored_the_same_way_as_the_authors_default() -> None:
    """One rule, applied twice — the trap #33 flagged for this ticket."""
    anchored = Input(name="x", kind="number", label="X", min=0.1, step=0.5)

    assert build_form((anchored,), submitted={"x": "0.6"}).values == {"x": 0.6}
    assert build_form((anchored,), submitted={"x": "1.0"}).values is None


def test_a_number_keeps_its_declared_precision_on_the_way_back() -> None:
    """What the user typed is what the form shows, not a reformatting of it."""
    form = build_form((DIAMETER,), submitted={"diameter": "8.50"})

    assert form.fields[0].raw == "8.50"
    assert form.values == {"diameter": 8.5}


@pytest.mark.parametrize(
    ("inputs", "on_open"),
    [
        ((), True),  # the static calculator: zero Inputs (§4.6)
        ((SIZE, METRIC_ONLY), True),
        ((SIZE, DIAMETER), False),
    ],
)
def test_compute_on_open_iff_every_input_has_a_default(
    inputs: tuple[Input, ...], on_open: bool
) -> None:
    assert computes_on_open(inputs) is on_open
