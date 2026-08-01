"""Calibration: discovery-time rules, resolution, and Manifest-determined arity.

Spec §5.2, §5.3, §5.4, §1.2, §10.1, §10.2.

Calibration is **data measured off the physical kit in the user's own workshop**,
and every rule here exists to stop a number that was never measured from looking
like one that was — or to stop the shape of the resolved dict depending on which
bender the user happens to own.
"""

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import client_for
from flask.testing import FlaskClient

from workshop_helper.discovery import build_index
from workshop_helper.manifest import ManifestError, read_manifest
from workshop_helper.roots import Root

KEYED = """
[applet]
type = "calculator"
name = "Bender"

[inputs.size]
kind    = "choice"
label   = "Pipe size"
choices = ["15mm", "22mm"]
default = "15mm"

[calibration]
keyed_by = "size"

[calibration.values.15mm]
r_centreline = 70.0

[calibration.values.22mm]
r_centreline = 110.0

[modes.single_bend]
label   = "Single bend"
inputs  = ["size"]
outputs = [{ name = "radius", label = "Radius", unit = "mm" }]
"""

UNKEYED = """
outputs = [{ name = "radius", label = "Radius", unit = "mm" }]

[applet]
type = "calculator"
name = "Bender"

[calibration.values]
backlash = 0.04
"""

ECHOES = """
from workshop_utils import Result


def compute(mode, inputs, calibration):
    return Result(outputs={"radius": calibration["r_centreline"]})
"""


@pytest.fixture(autouse=True)
def _clean_modules() -> Iterator[None]:
    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        del sys.modules[name]


def _manifest(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "manifest.toml"
    path.write_text(text)
    return path


def _client(tmp_path: Path, manifest: str = KEYED, source: str = ECHOES) -> FlaskClient:
    folder = tmp_path / "bender"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.toml").write_text(manifest)
    (folder / "applet.py").write_text(source)
    return client_for(build_index([Root(name="built-in", path=tmp_path)]))


# --- The schema (§5.2) -------------------------------------------------------


def test_a_keyed_table_is_read_as_a_row_per_key(tmp_path: Path) -> None:
    calibration = read_manifest(_manifest(tmp_path, KEYED)).calibration

    assert calibration is not None
    assert calibration.keyed_by == "size"
    assert calibration.values["22mm"] == {"r_centreline": 110.0}


def test_an_unkeyed_table_is_flat_and_needs_no_input(tmp_path: Path) -> None:
    calibration = read_manifest(_manifest(tmp_path, UNKEYED)).calibration

    assert calibration is not None
    assert calibration.keyed_by is None
    assert calibration.resolve({}) == {"backlash": 0.04}


def test_a_typo_in_keyed_by_is_loud_rather_than_silently_flat(tmp_path: Path) -> None:
    """The Host branches on `keyed_by`'s *presence*, so a near-miss must not pass."""
    text = KEYED.replace("keyed_by =", "keyd_by =")

    with pytest.raises(ManifestError) as raised:
        read_manifest(_manifest(tmp_path, text))

    assert "keyd_by" in str(raised.value)


# --- The four discovery rules (§5.3) -----------------------------------------


@pytest.mark.parametrize(
    ("text", "because"),
    [
        (
            KEYED.replace('keyed_by = "size"', 'keyed_by = "former"'),
            "rule 1: keyed_by must name an existing Input",
        ),
        (
            KEYED.replace('kind    = "choice"', 'kind    = "number"').replace(
                'choices = ["15mm", "22mm"]\ndefault = "15mm"', "default = 15"
            ),
            "rule 2: it must be a choice Input",
        ),
        (
            KEYED.replace(
                'choices = ["15mm", "22mm"]', 'choices = ["15mm", "22mm", "28mm"]'
            ),
            "rule 3: a choice with no measured row is not a choice (§1.2)",
        ),
        (
            KEYED + "\n[calibration.values.28mm]\nr_centreline = 144.3\n",
            "rule 3 the other way: a row nothing can select",
        ),
        (
            KEYED.replace(
                "[calibration.values.22mm]\nr_centreline = 110.0",
                "[calibration.values.22mm]\nr_centreline = 110.0\nbacklash = 0.04",
            ),
            "rule 4: a ragged table makes the resolved shape depend on the user",
        ),
    ],
)
def test_a_calibration_rule_failure_is_a_malformed_manifest(
    tmp_path: Path, text: str, because: str
) -> None:
    with pytest.raises(ManifestError):
        read_manifest(_manifest(tmp_path, text))


def test_28mm_is_refused_in_both_directions_by_the_same_rule(tmp_path: Path) -> None:
    """You cannot offer a size you have not measured, or measure one you cannot pick."""
    text = KEYED.replace(
        'choices = ["15mm", "22mm"]', 'choices = ["15mm", "22mm", "28mm"]'
    )

    with pytest.raises(ManifestError) as raised:
        read_manifest(_manifest(tmp_path, text))

    assert "28mm" in str(raised.value)


def test_a_mode_that_cannot_select_a_row_is_refused(tmp_path: Path) -> None:
    """With nothing selecting a key there is no slice to resolve (§5.4)."""
    text = KEYED.replace('inputs  = ["size"]', "inputs  = []")

    with pytest.raises(ManifestError) as raised:
        read_manifest(_manifest(tmp_path, text))

    assert "size" in str(raised.value)


def test_a_top_level_key_swallowed_by_a_calibration_row_is_loud(tmp_path: Path) -> None:
    """§4.5's ordering rule, where the field names are the author's own.

    Rectangularity would catch this on a two-key table, so the row here is the
    only one — a single-former Applet is exactly where the ordering rule has no
    other defence, and it is still a named fault.
    """
    text = (
        KEYED.replace('choices = ["15mm", "22mm"]', 'choices = ["15mm"]')
        .replace("[calibration.values.22mm]\nr_centreline = 110.0\n", "")
        .replace(
            "r_centreline = 70.0", 'r_centreline = 70.0\ndefault_mode = "single_bend"'
        )
    )

    with pytest.raises(ManifestError) as raised:
        read_manifest(_manifest(tmp_path, text))

    assert "default_mode" in str(raised.value)


# --- Resolution and arity (§5.4) ---------------------------------------------


def test_the_host_resolves_the_slice_and_compute_receives_a_flat_dict(
    tmp_path: Path,
) -> None:
    body = (
        _client(tmp_path)
        .post("/a/bender/compute", data={"mode": "single_bend", "size": "22mm"})
        .get_data(as_text=True)
    )

    assert "110" in body


def test_the_selected_key_decides_the_slice(tmp_path: Path) -> None:
    body = (
        _client(tmp_path)
        .post("/a/bender/compute", data={"mode": "single_bend", "size": "15mm"})
        .get_data(as_text=True)
    )

    assert "70" in body


@pytest.mark.parametrize(
    ("source", "because"),
    [
        (
            (
                "from workshop_utils import Result\n\n\n"
                "def compute(inputs):\n    return Result(outputs={'radius': 1})\n"
            ),
            "the Manifest declared three arguments and got a function taking one",
        ),
        (
            (
                "from workshop_utils import Result\n\n\n"
                "def compute(mode, inputs, calibration, extra):\n"
                "    return Result(outputs={'radius': 1})\n"
            ),
            "and one taking four",
        ),
    ],
)
def test_an_arity_mismatch_is_a_malformed_applet_fault(
    tmp_path: Path, source: str, because: str
) -> None:
    body = (
        _client(tmp_path, source=source)
        .post("/a/bender/compute", data={"mode": "single_bend", "size": "15mm"})
        .get_data(as_text=True)
    )

    assert "compute(mode, inputs, calibration)" in body
    assert "<details>" in body


def test_an_uncalibrated_calculator_is_never_handed_an_empty_dict(
    tmp_path: Path,
) -> None:
    """No `[calibration]` means no argument — not `{}` (§4.6)."""
    plain = (
        'outputs = [{ name = "radius", label = "Radius" }]\n'
        '[applet]\ntype = "calculator"\nname = "Bender"\n'
        '[inputs.size]\nkind = "number"\nlabel = "Size"\ndefault = 15\n'
    )
    source = (
        "from workshop_utils import Result\n\n\n"
        "def compute(inputs):\n"
        '    return Result(outputs={"radius": inputs["size"]})\n'
    )

    body = (
        _client(tmp_path, manifest=plain, source=source)
        .get("/a/bender")
        .get_data(as_text=True)
    )

    assert "15" in body
    assert "<details>" not in body
