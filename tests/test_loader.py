"""Lazy import, the compute call, and compute-time faults (spec §7.2, §10.2)."""

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from workshop_helper.discovery import Applet
from workshop_helper.loader import AppletFault, module_name, run_compute
from workshop_helper.manifest import Mode, Output
from workshop_helper.roots import Root
from workshop_utils import Result

ANSWER = Mode(
    name="",
    label="",
    outputs=(Output(name="answer", label="Answer", primary=True),),
)

WORKING = """
from workshop_utils import Result


def compute(inputs):
    return Result(outputs={"answer": inputs["x"] * 2})
"""


@pytest.fixture(autouse=True)
def _clean_modules() -> Iterator[None]:
    """Applets live in `sys.modules`; a test must not leave one there."""
    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        del sys.modules[name]


def _applet(tmp_path: Path, source: str, applet_id: str = "doubler") -> Applet:
    folder = tmp_path / applet_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "applet.py").write_text(source)
    return Applet(
        id=applet_id,
        root=Root(name="built-in", path=tmp_path),
        path=folder,
        type="calculator",
        name="Doubler",
    )


def test_compute_receives_the_validated_inputs_and_returns_a_result(
    tmp_path: Path,
) -> None:
    result = run_compute(_applet(tmp_path, WORKING), ANSWER, {"x": 4.0})

    assert result == Result(outputs={"answer": 8.0})


def test_the_module_is_named_by_the_applet_id(tmp_path: Path) -> None:
    """Two Roots' `helpers.py` cannot become one `sys.modules` entry (§7.2)."""
    run_compute(_applet(tmp_path, WORKING), ANSWER, {"x": 1.0})

    assert module_name("doubler") in sys.modules


def test_an_applet_may_import_its_own_submodules(tmp_path: Path) -> None:
    """Applets are multi-file packages (§7.2) — relative imports, not `sys.path`."""
    applet = _applet(
        tmp_path,
        "from workshop_utils import Result\n"
        "from .helpers import twice\n\n\n"
        "def compute(inputs):\n"
        '    return Result(outputs={"answer": twice(inputs["x"])})\n',
    )
    (applet.path / "helpers.py").write_text("def twice(n):\n    return n * 2\n")

    assert run_compute(applet, ANSWER, {"x": 3.0}).outputs == {"answer": 6.0}


def test_two_applets_keep_their_own_same_named_helpers(tmp_path: Path) -> None:
    """The collision §7.2 exists to close, exercised rather than asserted."""
    source = (
        "from workshop_utils import Result\n"
        "from .helpers import factor\n\n\n"
        "def compute(inputs):\n"
        '    return Result(outputs={"answer": inputs["x"] * factor})\n'
    )
    mine = _applet(tmp_path / "own", source, applet_id="mine")
    (mine.path / "helpers.py").write_text("factor = 2\n")
    theirs = _applet(tmp_path / "mate", source, applet_id="theirs")
    (theirs.path / "helpers.py").write_text("factor = 10\n")

    assert run_compute(mine, ANSWER, {"x": 1.0}).outputs == {"answer": 2.0}
    assert run_compute(theirs, ANSWER, {"x": 1.0}).outputs == {"answer": 10.0}


def test_an_applet_id_cannot_displace_a_host_module(tmp_path: Path) -> None:
    """`sys.modules` is shared with the Host: a folder named `math` is not it."""
    run_compute(_applet(tmp_path, WORKING, applet_id="math"), ANSWER, {"x": 1.0})

    assert sys.modules["math"].__name__ == "math"


def test_nothing_is_imported_until_something_is_run(tmp_path: Path) -> None:
    """Building the Applet record must not execute it (§2.6, ADR-0004)."""
    _applet(tmp_path, "raise AssertionError('imported at scan')\n")

    assert module_name("doubler") not in sys.modules


# --- Compute-time faults (§10.2) ---------------------------------------------


@pytest.mark.parametrize(
    ("source", "summary", "because"),
    [
        ("import nonexistent_library\n", "on import", "ImportError from lazy import"),
        ("raise RuntimeError('boom')\n", "on import", "a raise at import time"),
        (
            "def compute(inputs):\n    return 1 / 0\n",
            "raised ZeroDivisionError",
            "compute() crashing",
        ),
        (
            "def compute(inputs):\n    return {'answer': 1}\n",
            "not a Result",
            "returning something that is not a Result",
        ),
        (
            (
                "from workshop_utils import Result\n\n\n"
                "def compute(inputs):\n    return Result(outputs={'setback': 1})\n"
            ),
            "wrong Outputs",
            "Output names that do not match the Manifest",
        ),
        ("answer = 42\n", "defines no compute()", "no compute() at all"),
        ("compute = 42\n", "defines no compute()", "a compute() that is not callable"),
    ],
)
def test_a_compute_time_fault_carries_a_summary_and_details(
    tmp_path: Path, source: str, summary: str, because: str
) -> None:
    with pytest.raises(AppletFault) as raised:
        run_compute(_applet(tmp_path, source), ANSWER, {"x": 1.0})

    assert summary in raised.value.summary
    assert raised.value.details


def test_a_crash_keeps_its_traceback_for_the_details_disclosure(
    tmp_path: Path,
) -> None:
    """It is your own machine; Details carries the whole thing (§10.3)."""
    with pytest.raises(AppletFault) as raised:
        run_compute(
            _applet(tmp_path, "def compute(inputs):\n    return 1 / 0\n"), ANSWER, {}
        )

    assert "ZeroDivisionError" in raised.value.details
    assert "Traceback" in raised.value.details


def test_a_missing_output_is_named_as_precisely_as_an_unexpected_one(
    tmp_path: Path,
) -> None:
    source = (
        "from workshop_utils import Result\n\n\n"
        "def compute(inputs):\n    return Result(outputs={'answer': 1, 'extra': 2})\n"
    )

    with pytest.raises(AppletFault) as raised:
        run_compute(_applet(tmp_path, source), ANSWER, {})

    assert "answer, extra" in raised.value.details


def test_a_broken_import_is_not_cached_as_a_half_applet(tmp_path: Path) -> None:
    """Fix the file, reopen the page, get a real second attempt."""
    applet = _applet(tmp_path, "raise RuntimeError('boom')\n")
    with pytest.raises(AppletFault):
        run_compute(applet, ANSWER, {"x": 1.0})

    (applet.path / "applet.py").write_text(WORKING)

    assert run_compute(applet, ANSWER, {"x": 2.0}).outputs == {"answer": 4.0}
