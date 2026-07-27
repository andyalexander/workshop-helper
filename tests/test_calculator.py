"""The calculator page, the round-trip, and compute-time faults on it.

Spec §2.8, §4.3, §4.6, §6, §10.2.
"""

import sys
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from conftest import client_for
from flask.testing import FlaskClient

from workshop_helper.discovery import Applet, Index
from workshop_helper.loader import module_name
from workshop_helper.manifest import Input, Output
from workshop_helper.roots import Root

HTMX = {"HX-Request": "true"}

DOUBLER = """
from workshop_utils import Result


def compute(inputs):
    return Result(outputs={"answer": inputs["angle"] * 2, "note": "checked"})
"""

ANGLE = Input(
    name="angle", kind="number", label="Bend angle", unit="°", min=0, max=180, step=1
)
OUTPUTS = (
    Output(name="answer", label="Answer", unit="mm", primary=True),
    Output(name="note", label="Note"),
)


@pytest.fixture(autouse=True)
def _clean_modules() -> Iterator[None]:
    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        del sys.modules[name]


def _calculator(
    tmp_path: Path,
    source: str = DOUBLER,
    inputs: tuple[Input, ...] = (ANGLE,),
    applet_id: str = "doubler",
) -> Applet:
    folder = tmp_path / applet_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "applet.py").write_text(source)
    return Applet(
        id=applet_id,
        root=Root(name="built-in", path=tmp_path),
        path=folder,
        type="calculator",
        name="Doubler",
        author="andy",
        inputs=inputs,
        outputs=OUTPUTS,
    )


def _client(tmp_path: Path, **kwargs: object) -> FlaskClient:
    return client_for(Index(applets=[_calculator(tmp_path, **kwargs)]))  # type: ignore[arg-type]


# --- The form (§4.3) ---------------------------------------------------------


def test_the_form_renders_every_declared_kind(tmp_path: Path) -> None:
    inputs = (
        ANGLE,
        Input(
            name="size",
            kind="choice",
            label="Pipe size",
            choices=("15mm", "22mm"),
            default="15mm",
        ),
        Input(name="metric_only", kind="bool", label="Metric only", default=False),
    )

    body = _client(tmp_path, inputs=inputs).get("/a/doubler").get_data(as_text=True)

    assert 'type="number"' in body and 'name="angle"' in body
    assert 'min="0"' in body and 'max="180"' in body and 'step="1"' in body
    assert "Bend angle" in body and "°" in body
    assert '<select id="in-size" name="size">' in body
    assert "<option selected>15mm</option>" in body and "22mm" in body
    assert 'type="checkbox"' in body and 'name="metric_only"' in body


def test_a_number_without_a_step_accepts_any_measurement(tmp_path: Path) -> None:
    """A bare number input would otherwise insist on integers."""
    unstepped = Input(name="angle", kind="number", label="Bend angle")

    body = (
        _client(tmp_path, inputs=(unstepped,)).get("/a/doubler").get_data(as_text=True)
    )

    assert 'step="any"' in body


def test_the_form_posts_on_its_own_and_htmx_only_upgrades_it(tmp_path: Path) -> None:
    body = _client(tmp_path).get("/a/doubler").get_data(as_text=True)

    assert 'method="post"' in body
    assert 'action="/a/doubler/compute"' in body
    assert 'hx-post="/a/doubler/compute"' in body
    assert 'hx-target="#result"' in body


# --- Compute-on-open (§4.6) --------------------------------------------------


def test_an_undefaulted_input_means_no_result_on_open(tmp_path: Path) -> None:
    body = _client(tmp_path).get("/a/doubler").get_data(as_text=True)

    assert "Fill in the Inputs" in body
    assert "Answer" not in body


def test_a_fully_defaulted_applet_computes_on_open(tmp_path: Path) -> None:
    defaulted = Input(
        name="angle", kind="number", label="Bend angle", min=0, max=180, default=45
    )

    body = (
        _client(tmp_path, inputs=(defaulted,)).get("/a/doubler").get_data(as_text=True)
    )

    assert "Answer" in body and "90" in body


def test_a_zero_input_static_calculator_computes_on_open(tmp_path: Path) -> None:
    """The static calculator is the degenerate case, not a separate thing (§4.6)."""
    source = (
        "from workshop_utils import Result\n\n\n"
        "def compute(inputs):\n"
        "    return Result(outputs={'answer': 42, 'note': 'static'})\n"
    )

    body = (
        _client(tmp_path, source=source, inputs=())
        .get("/a/doubler")
        .get_data(as_text=True)
    )

    assert "42" in body
    assert "<form" in body  # still a form, with a Compute button and no fields


# --- The Result (§6) ---------------------------------------------------------


def test_the_host_labels_units_and_ranks_the_outputs(tmp_path: Path) -> None:
    body = (
        _client(tmp_path)
        .post("/a/doubler/compute", data={"angle": "21"})
        .get_data(as_text=True)
    )

    assert 'class="output primary"' in body
    assert "Answer" in body and "42" in body and "mm" in body
    assert "Note" in body and "checked" in body


def test_the_primary_output_is_the_one_the_manifest_names(tmp_path: Path) -> None:
    outputs = (
        Output(name="answer", label="Answer", unit="mm"),
        Output(name="note", label="Note", primary=True),
    )
    index = Index(applets=[replace(_calculator(tmp_path), outputs=outputs)])

    body = (
        client_for(index)
        .post("/a/doubler/compute", data={"angle": "21"})
        .get_data(as_text=True)
    )

    headline = body[body.index('class="output primary"') :][:120]
    assert "Note" in headline and "Answer" not in headline


# --- The round-trip (§2.8) ---------------------------------------------------


def test_htmx_gets_the_result_fragment_and_not_a_page(tmp_path: Path) -> None:
    body = (
        _client(tmp_path)
        .post("/a/doubler/compute", data={"angle": "21"}, headers=HTMX)
        .get_data(as_text=True)
    )

    assert "<html" not in body
    assert "42" in body


def test_the_same_post_without_htmx_answers_with_the_whole_page(tmp_path: Path) -> None:
    """The form works with JavaScript disabled — htmx is the upgrade (§2.8)."""
    body = (
        _client(tmp_path)
        .post("/a/doubler/compute", data={"angle": "21"})
        .get_data(as_text=True)
    )

    assert "<html" in body
    assert "42" in body
    assert 'value="21"' in body  # and the form comes back filled in


def test_the_swapped_fragment_brings_the_form_with_it_out_of_band(
    tmp_path: Path,
) -> None:
    """How a field's own error reaches the field while htmx swaps the Result."""
    body = (
        _client(tmp_path)
        .post("/a/doubler/compute", data={"angle": "200"}, headers=HTMX)
        .get_data(as_text=True)
    )

    assert 'hx-swap-oob="true"' in body
    assert "Bend angle must be 180 or less" in body


# --- The hard gate (§4.3) ----------------------------------------------------


def test_an_invalid_value_never_reaches_compute(tmp_path: Path) -> None:
    """`compute()` here raises if it is ever called at all."""
    exploding = "def compute(inputs):\n    raise AssertionError('compute() ran')\n"

    body = (
        _client(tmp_path, source=exploding)
        .post("/a/doubler/compute", data={"angle": "200"})
        .get_data(as_text=True)
    )

    assert "compute() ran" not in body
    assert "must be 180 or less" in body


def test_a_missing_input_is_a_refusal_not_a_none(tmp_path: Path) -> None:
    exploding = "def compute(inputs):\n    raise AssertionError('compute() ran')\n"

    body = (
        _client(tmp_path, source=exploding)
        .post("/a/doubler/compute", data={})
        .get_data(as_text=True)
    )

    assert "compute() ran" not in body
    assert "needs a value" in body


# --- Compute-time faults on the Applet page (§10.2) --------------------------


@pytest.mark.parametrize(
    ("source", "shown"),
    [
        ("import nonexistent_library\n", "ModuleNotFoundError"),
        ("raise RuntimeError('boom at import')\n", "boom at import"),
        (
            "def compute(inputs):\n    return 1 / 0\n",
            "ZeroDivisionError",
        ),
        (
            (
                "from workshop_utils import Result\n\n\n"
                "def compute(inputs):\n    return Result(outputs={'setback': 1})\n"
            ),
            "wrong Outputs",
        ),
    ],
)
def test_a_compute_time_fault_renders_on_the_applet_page(
    tmp_path: Path, source: str, shown: str
) -> None:
    body = (
        _client(tmp_path, source=source)
        .post("/a/doubler/compute", data={"angle": "21"})
        .get_data(as_text=True)
    )

    assert "Doubler — from Root &#39;built-in&#39;, by andy" in body
    assert "<details>" in body
    assert shown in body


def test_a_faulty_applet_still_shows_its_form(tmp_path: Path) -> None:
    """The page is the Applet's, not the error's: fix the value and try again."""
    body = (
        _client(tmp_path, source="raise RuntimeError('boom')\n")
        .post("/a/doubler/compute", data={"angle": "21"})
        .get_data(as_text=True)
    )

    assert 'name="angle"' in body


def test_nothing_is_imported_when_a_calculator_is_merely_listed(
    tmp_path: Path,
) -> None:
    """Browse must not run Applet code (§2.6, ADR-0004)."""
    _client(tmp_path, source="raise AssertionError('imported at scan')\n").get("/")

    assert module_name("doubler") not in sys.modules


def test_a_calculator_serves_no_assets(tmp_path: Path) -> None:
    """Its folder is Python, and `applet.py` is not a page asset."""
    assert _client(tmp_path).get("/a/doubler/assets/applet.py").status_code == 404


def test_compute_is_not_a_documentation_route(tmp_path: Path) -> None:
    doc = Applet(
        id="thread-pitch",
        root=Root(name="built-in", path=tmp_path),
        path=tmp_path,
        type="documentation",
        name="Thread pitch",
        body="# Thread pitch\n",
    )

    response = client_for(Index(applets=[doc])).post("/a/thread-pitch/compute", data={})

    assert response.status_code == 404
