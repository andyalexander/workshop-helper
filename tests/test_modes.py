"""Modes: the derived selector, per-mode Outputs, and the ordering rule.

Spec §4.5, §4.6, §1.4.

A mode changes **what exists**. So these tests are about two Inputs sets and two
Output sets living in one Applet without a second source of truth appearing —
there is no `mode` Input, no declared selector, and nothing for the two to
disagree about.
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

HTMX = {"HX-Request": "true"}

MODES = """
default_mode = "step"

[applet]
type = "calculator"
name = "Bender"

[inputs.angle]
kind    = "number"
label   = "Bend angle"
min     = 1
max     = 90
default = 45

[inputs.offset]
kind    = "number"
label   = "Step"
min     = 1
default = 100

[modes.single_bend]
label   = "Single bend"
inputs  = ["angle"]
outputs = [{ name = "setback", label = "Setback", unit = "mm" }]

[modes.step]
label   = "Step (offset)"
inputs  = ["angle", "offset"]
outputs = [
  { name = "marks", label = "Distance between marks", unit = "mm", primary = true },
  { name = "gain",  label = "Gain", unit = "mm" },
]
"""

BRANCHING = """
from workshop_utils import Result


def compute(mode, inputs):
    if mode == "single_bend":
        return Result(outputs={"setback": inputs["angle"]})
    return Result(outputs={"marks": inputs["offset"], "gain": inputs["angle"]})
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


def _client(
    tmp_path: Path, manifest: str = MODES, source: str = BRANCHING
) -> FlaskClient:
    folder = tmp_path / "bender"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.toml").write_text(manifest)
    (folder / "applet.py").write_text(source)
    return client_for(build_index([Root(name="built-in", path=tmp_path)]))


# --- What the Manifest declares (§4.5) ---------------------------------------


def test_each_mode_names_its_own_inputs_and_outputs(tmp_path: Path) -> None:
    modes = read_manifest(_manifest(tmp_path, MODES)).modes

    assert [mode.name for mode in modes] == ["single_bend", "step"]
    assert [i.name for i in modes[0].inputs] == ["angle"]
    assert [i.name for i in modes[1].inputs] == ["angle", "offset"]
    assert [o.name for o in modes[1].outputs] == ["marks", "gain"]


def test_a_shared_input_is_genuinely_one_input(tmp_path: Path) -> None:
    """Same kind, same unit, same validation, in every mode that uses it."""
    modes = read_manifest(_manifest(tmp_path, MODES)).modes

    assert modes[0].inputs[0] == modes[1].inputs[0]


def test_default_mode_names_the_mode_that_opens(tmp_path: Path) -> None:
    assert read_manifest(_manifest(tmp_path, MODES)).default_mode == "step"


def test_without_default_mode_the_first_declared_one_opens(tmp_path: Path) -> None:
    text = MODES.replace('default_mode = "step"\n', "")

    assert read_manifest(_manifest(tmp_path, text)).default_mode == "single_bend"


def test_each_mode_names_its_own_primary(tmp_path: Path) -> None:
    """The headline changes between modes because each mode chooses it."""
    modes = read_manifest(_manifest(tmp_path, MODES)).modes

    # A lone Output is the primary without saying so — no ceremony (§1.7).
    assert modes[0].outputs[0].primary
    assert [o.name for o in modes[1].outputs if o.primary] == ["marks"]


@pytest.mark.parametrize(
    ("text", "because"),
    [
        (
            MODES.replace('default_mode = "step"', 'default_mode = "steps"'),
            "default_mode names no declared mode",
        ),
        (
            MODES.replace('inputs  = ["angle"]', 'inputs  = ["angel"]'),
            "a mode names an Input that does not exist",
        ),
        (
            MODES.replace('label   = "Single bend"\n', ""),
            "a mode with no label has nothing to put in the selector",
        ),
        (
            MODES.replace(
                'outputs = [{ name = "setback", label = "Setback", unit = "mm" }]',
                "outputs = []",
            ),
            "a mode that declares no Outputs can never show a Result",
        ),
        (
            MODES.replace(
                '{ name = "gain",  label = "Gain", unit = "mm" }',
                '{ name = "gain",  label = "Gain", unit = "mm", primary = true }',
            ),
            "two primaries in one mode is a headline nobody chose",
        ),
        (
            MODES.replace(
                '  { name = "marks", label = "Distance between marks", '
                'unit = "mm", primary = true },',
                '  { name = "marks", label = "Distance between marks", unit = "mm" },',
            ),
            "no primary among several is a headline nobody chose",
        ),
        (
            MODES + '\n[inputs.mode]\nkind = "choice"\nlabel = "Mode"\n'
            'choices = ["a"]\n',
            "the selector is derived; a `mode` Input is a second source of truth",
        ),
        (
            'outputs = [{ name = "x", label = "X" }]\n' + MODES,
            "top-level outputs alongside [modes] declares Outputs twice",
        ),
    ],
)
def test_a_broken_mode_declaration_is_a_malformed_manifest(
    tmp_path: Path, text: str, because: str
) -> None:
    with pytest.raises(ManifestError):
        read_manifest(_manifest(tmp_path, text))


def test_a_top_level_key_swallowed_by_a_mode_table_is_loud(tmp_path: Path) -> None:
    """§4.5's ordering rule: the misparse the author cannot see by reading."""
    text = MODES.replace('default_mode = "step"\n', "") + '\ndefault_mode = "step"\n'

    with pytest.raises(ManifestError) as raised:
        read_manifest(_manifest(tmp_path, text))

    assert "default_mode" in str(raised.value)


# --- The derived selector, and the round-trip (§4.5, §2.8) -------------------


def test_the_selector_is_rendered_from_the_declared_modes(tmp_path: Path) -> None:
    body = _client(tmp_path).get("/a/bender").get_data(as_text=True)

    assert 'name="mode"' in body
    assert '<option value="single_bend" >Single bend</option>' in body
    assert '<option value="step" selected>Step (offset)</option>' in body


def test_a_single_mode_calculator_renders_no_selector(tmp_path: Path) -> None:
    """Simplicity is the absence of the section (§4.6)."""
    single = (
        'outputs = [{ name = "setback", label = "Setback" }]\n'
        '[applet]\ntype = "calculator"\nname = "Bender"\n'
        '[inputs.angle]\nkind = "number"\nlabel = "Bend angle"\ndefault = 45\n'
    )
    source = (
        "from workshop_utils import Result\n\n\n"
        "def compute(inputs):\n"
        '    return Result(outputs={"setback": inputs["angle"]})\n'
    )

    body = (
        _client(tmp_path, manifest=single, source=source)
        .get("/a/bender")
        .get_data(as_text=True)
    )

    assert 'name="mode"' not in body
    assert "45" in body


def test_the_opening_mode_shows_its_own_fields_and_headline(tmp_path: Path) -> None:
    body = _client(tmp_path).get("/a/bender").get_data(as_text=True)

    assert 'name="offset"' in body
    assert "Distance between marks" in body
    assert "Setback" not in body


def test_compute_branches_on_the_mode_it_is_given(tmp_path: Path) -> None:
    body = (
        _client(tmp_path)
        .post("/a/bender/compute", data={"mode": "single_bend", "angle": "30"})
        .get_data(as_text=True)
    )

    assert "Setback" in body
    assert "Distance between marks" not in body


def test_changing_mode_keeps_the_shared_input_and_defaults_the_new_one(
    tmp_path: Path,
) -> None:
    """The form on screen carries the old mode's fields; the new one arrives absent."""
    body = (
        _client(tmp_path)
        .post(
            "/a/bender/compute",
            data={"mode": "step", "angle": "30"},
            headers=HTMX,
        )
        .get_data(as_text=True)
    )

    assert 'value="30"' in body  # the shared Input keeps what was typed
    assert 'value="100"' in body  # and `offset` opens on its declared default


def test_an_unknown_mode_falls_back_to_the_one_that_opens(tmp_path: Path) -> None:
    body = (
        _client(tmp_path)
        .post("/a/bender/compute", data={"mode": "hand-typed", "angle": "30"})
        .get_data(as_text=True)
    )

    assert "Distance between marks" in body
