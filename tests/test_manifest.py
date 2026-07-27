"""Reading a Manifest (spec §4.1, §4.2, §4.3, §3, §10.1).

A Manifest either yields metadata or raises. Which greyed card each raise
produces is discovery's business (``test_discovery.py``).
"""

from pathlib import Path

import pytest

from workshop_helper.manifest import (
    APPLET_TYPES,
    INPUT_KINDS,
    ManifestError,
    read_identity,
    read_manifest,
)

COMPLETE = """
outputs = [
  { name = "setback", label = "Setback", unit = "mm", primary = true },
  { name = "gain", label = "Gain", unit = "mm" },
]

[applet]
type        = "calculator"
name        = "Pipe-bender setback"
description = "Setback and offset marks for a lever pipe bender."
author      = "andy"
tags        = ["plumbing", "copper", "pipe-bending"]
"""

# The smallest complete calculator head: top-level `outputs` first, per §4.5's
# ordering rule, then `[applet]`.
CALCULATOR_HEAD = (
    'outputs = [{ name = "answer", label = "Answer" }]\n'
    '[applet]\ntype = "calculator"\nname = "T"\n'
)

MINIMAL = """
[applet]
type = "documentation"
name = "Thread pitch"
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "manifest.toml"
    path.write_text(text)
    return path


def test_applet_types_are_the_closed_set() -> None:
    """Adding a type is a change to the Host, not to a Manifest (ADR-0005)."""
    assert APPLET_TYPES == frozenset({"documentation", "calculator"})


def test_reads_every_declared_field(tmp_path: Path) -> None:
    manifest = read_manifest(_write(tmp_path, COMPLETE))
    assert manifest.type == "calculator"
    assert manifest.name == "Pipe-bender setback"
    assert manifest.description == "Setback and offset marks for a lever pipe bender."
    assert manifest.author == "andy"
    assert manifest.tags == ("plumbing", "copper", "pipe-bending")


def test_optional_fields_degrade_to_none_and_empty(tmp_path: Path) -> None:
    manifest = read_manifest(_write(tmp_path, MINIMAL))
    assert manifest.description is None
    assert manifest.author is None
    assert manifest.tags == ()


@pytest.mark.parametrize(
    ("text", "because"),
    [
        ("not = valid = toml", "unparseable TOML"),
        ('name = "no section"', "no [applet] section"),
        ('[applet]\nname = "Nameless type"', "no type"),
        ('[applet]\ntype = "documentation"', "no name"),
        ('[applet]\ntype = "widget"\nname = "Unknown"', "unknown type"),
        ('[applet]\ntype = "documentation"\nname = 7', "non-string name"),
        (
            '[applet]\ntype = "documentation"\nname = "T"\ntags = "copper"',
            "tags not a list",
        ),
        ('[applet]\ntype = "documentation"\nname = "T"\ntags = [1]', "non-string tag"),
    ],
)
def test_malformed_manifests_raise(tmp_path: Path, text: str, because: str) -> None:
    with pytest.raises(ManifestError):
        read_manifest(_write(tmp_path, text))


def test_a_missing_manifest_raises(tmp_path: Path) -> None:
    with pytest.raises(ManifestError):
        read_manifest(tmp_path / "manifest.toml")


# --- Identity for the blame line (§10.3) ------------------------------------


def test_identity_is_read_even_when_validation_would_fail(tmp_path: Path) -> None:
    """The blame line needs a name and author *because* something else broke."""
    path = _write(
        tmp_path,
        '[applet]\ntype = "documentation"\nname = "Annealing"\nauthor = "dave"\n'
        "[calibration.values]\nr = 1.0\n",
    )

    with pytest.raises(ManifestError):
        read_manifest(path)
    assert read_identity(path) == ("Annealing", "dave")


@pytest.mark.parametrize(
    ("text", "because"),
    [
        ("not = valid = toml", "unparseable"),
        ('name = "no section"', "no [applet] section"),
        ('[applet]\ntype = "documentation"', "no name declared"),
        ('[applet]\ntype = "documentation"\nname = 7', "name is not a string"),
        ('[applet]\ntype = "documentation"\nname = ""', "name is empty"),
    ],
)
def test_identity_degrades_to_nothing_rather_than_raising(
    tmp_path: Path, text: str, because: str
) -> None:
    """Reading for display never raises — there is a fault to render already."""
    assert read_identity(_write(tmp_path, text)) == (None, None)


def test_a_bad_author_does_not_cost_the_name(tmp_path: Path) -> None:
    identity = read_identity(
        _write(tmp_path, '[applet]\ntype = "documentation"\nname = "T"\nauthor = 7\n')
    )

    assert identity == ("T", None)


def test_input_kinds_are_the_closed_set() -> None:
    """`text` and `pattern` were cut in #24 (spec §4.3)."""
    assert INPUT_KINDS == frozenset({"number", "choice", "bool"})


# --- Tags (§4.2) ------------------------------------------------------------


def test_tags_are_normalised_at_scan(tmp_path: Path) -> None:
    """Lowercase, trim, collapse whitespace runs — and nothing more (§4.2)."""
    manifest = read_manifest(
        _write(
            tmp_path,
            '[applet]\ntype = "documentation"\nname = "T"\n'
            'tags = ["  Copper ", "PIPE\tBENDING", "hand   tools"]\n',
        )
    )
    assert manifest.tags == ("copper", "pipe bending", "hand tools")


def test_tag_normalisation_stops_at_the_mechanical_rules(tmp_path: Path) -> None:
    """No kebab-casing, no stemming, no synonyms (§4.2)."""
    manifest = read_manifest(
        _write(
            tmp_path,
            '[applet]\ntype = "documentation"\nname = "T"\n'
            'tags = ["pipe-bending", "fasteners", "imp"]\n',
        )
    )
    assert manifest.tags == ("pipe-bending", "fasteners", "imp")


def test_tags_that_normalise_alike_collapse_to_one_facet(tmp_path: Path) -> None:
    """A facet cannot be present twice; empties cannot be a facet label at all."""
    manifest = read_manifest(
        _write(
            tmp_path,
            '[applet]\ntype = "documentation"\nname = "T"\n'
            'tags = ["Copper", "copper", "  ", "brass"]\n',
        )
    )
    assert manifest.tags == ("copper", "brass")


# --- `[calibration]` on a documentation Applet (§3.1) -----------------------


def test_calibration_on_a_documentation_applet_is_malformed(tmp_path: Path) -> None:
    """Malformed, not ignored (#15) — there is no `compute()` to receive it."""
    with pytest.raises(ManifestError, match="calibration"):
        read_manifest(
            _write(
                tmp_path,
                '[applet]\ntype = "documentation"\nname = "T"\n'
                "[calibration.values]\nr_centreline = 70.0\n",
            )
        )


def test_calibration_on_a_calculator_is_left_to_its_own_ticket(
    tmp_path: Path,
) -> None:
    """The four §5.3 rules ship with `pipe-bender` (#36); presence is not a fault."""
    manifest = read_manifest(
        _write(
            tmp_path,
            CALCULATOR_HEAD + "[calibration.values]\nr_centreline = 70.0\n",
        )
    )
    assert manifest.type == "calculator"


# --- Inputs and the author's `default` (§4.3) -------------------------------

INPUTS = """
outputs = [{ name = "setback", label = "Setback", unit = "mm" }]

[applet]
type = "calculator"
name = "Pipe-bender setback"

[inputs.size]
kind    = "choice"
label   = "Pipe size"
choices = ["15mm", "22mm"]
default = "15mm"

[inputs.angle]
kind    = "number"
label   = "Bend angle"
unit    = "°"
min     = 0
max     = 180
step    = 1
default = 90

[inputs.metric_only]
kind    = "bool"
label   = "Metric only"
default = false
"""


def test_reads_the_declared_inputs_in_authored_order(tmp_path: Path) -> None:
    manifest = read_manifest(_write(tmp_path, INPUTS))

    assert [i.name for i in manifest.inputs] == ["size", "angle", "metric_only"]
    size, angle, metric_only = manifest.inputs
    assert (size.kind, size.label, size.choices) == (
        "choice",
        "Pipe size",
        ("15mm", "22mm"),
    )
    assert size.default == "15mm"
    assert (angle.kind, angle.unit, angle.min, angle.max, angle.step) == (
        "number",
        "°",
        0,
        180,
        1,
    )
    assert angle.default == 90
    assert metric_only.kind == "bool"
    assert metric_only.default is False


def test_an_input_may_declare_no_default(tmp_path: Path) -> None:
    manifest = read_manifest(
        _write(
            tmp_path,
            CALCULATOR_HEAD + '[inputs.angle]\nkind = "number"\nlabel = "Bend angle"\n',
        )
    )
    (angle,) = manifest.inputs
    assert angle.default is None


@pytest.mark.parametrize(
    ("declaration", "because"),
    [
        ('kind = "text"\nlabel = "Note"', "kind outside the closed set"),
        ('label = "Note"', "no kind"),
        ('kind = "number"', "no label"),
        ('kind = "choice"\nlabel = "Size"', "choice without choices"),
        ('kind = "choice"\nlabel = "Size"\nchoices = []', "empty choices"),
        ('kind = "choice"\nlabel = "Size"\nchoices = "15mm"', "choices not a list"),
        ('kind = "number"\nlabel = "A"\nmin = "0"', "non-numeric min"),
    ],
)
def test_a_malformed_input_declaration_raises(
    tmp_path: Path, declaration: str, because: str
) -> None:
    with pytest.raises(ManifestError):
        read_manifest(
            _write(
                tmp_path,
                CALCULATOR_HEAD + f"[inputs.thing]\n{declaration}\n",
            )
        )


@pytest.mark.parametrize(
    ("declaration", "because"),
    [
        (
            'kind = "choice"\nlabel = "Size"\nchoices = ["15mm"]\ndefault = "28mm"',
            "not one of the choices",
        ),
        (
            'kind = "number"\nlabel = "A"\nmin = 0\nmax = 180\ndefault = 200',
            "above max",
        ),
        ('kind = "number"\nlabel = "A"\nmin = 0\ndefault = -1', "below min"),
        (
            'kind = "number"\nlabel = "A"\nstep = 1\ndefault = 90.5',
            "step = 1 means integer",
        ),
        (
            'kind = "number"\nlabel = "A"\nstep = 0.5\ndefault = 90.3',
            "off a finer grid — the case #33 deferred to this ticket",
        ),
        (
            'kind = "number"\nlabel = "A"\nmin = 0.1\nstep = 0.5\ndefault = 1.0',
            "on the 0-grid but not the min-anchored one",
        ),
        ('kind = "number"\nlabel = "A"\ndefault = "90"', "a string, not a number"),
        ('kind = "number"\nlabel = "A"\ndefault = true', "a bool, not a number"),
        ('kind = "bool"\nlabel = "A"\ndefault = "yes"', "not a bool"),
        ('kind = "choice"\nlabel = "A"\nchoices = ["x"]\ndefault = 1', "not a string"),
    ],
)
def test_an_invalid_author_default_is_a_malformed_manifest(
    tmp_path: Path, declaration: str, because: str
) -> None:
    """Not a silent fallback — the author writes once for everyone (§4.3)."""
    with pytest.raises(ManifestError, match="default"):
        read_manifest(
            _write(
                tmp_path,
                CALCULATOR_HEAD + f"[inputs.thing]\n{declaration}\n",
            )
        )


@pytest.mark.parametrize(
    "pool",
    [
        'inputs = "angle"',  # not a table at all
        "inputs = { angle = 1 }",  # a table, but not of tables
    ],
)
def test_the_inputs_pool_must_be_a_table_of_tables(tmp_path: Path, pool: str) -> None:
    """Top-level keys come first, per §4.5's ordering rule."""
    with pytest.raises(ManifestError):
        read_manifest(
            _write(
                tmp_path,
                f"{pool}\n" + CALCULATOR_HEAD,
            )
        )


@pytest.mark.parametrize(
    ("declaration", "grid"),
    [
        ("step = 0.5\ndefault = 90.5", "0.5 from 0"),
        ("min = 0.1\nstep = 0.5\ndefault = 1.1", "0.5 from the declared min"),
        ("min = 0\nmax = 180\nstep = 1\ndefault = 90", "whole numbers"),
        ("step = 0.05\ndefault = 1.15", "float arithmetic that must still land"),
    ],
)
def test_a_default_on_the_step_grid_is_accepted(
    tmp_path: Path, declaration: str, grid: str
) -> None:
    """The anchor is `min`, else 0 — the browser's own rule for a stepper."""
    manifest = read_manifest(
        _write(
            tmp_path,
            CALCULATOR_HEAD + f'[inputs.thing]\nkind = "number"\nlabel = "A"\n'
            f"{declaration}\n",
        )
    )

    assert manifest.inputs[0].default is not None


@pytest.mark.parametrize("step", ["0", "-1"])
@pytest.mark.parametrize("default", ["\ndefault = 1", ""])
def test_a_step_of_zero_or_less_is_not_a_grid(
    tmp_path: Path, step: str, default: str
) -> None:
    """Refused at scan even with no `default` to check it against.

    Otherwise the card looks healthy and the grid only fails when someone types
    into it, turning an authoring mistake into a mid-request failure (§10.1).
    """
    with pytest.raises(ManifestError, match="step"):
        read_manifest(
            _write(
                tmp_path,
                CALCULATOR_HEAD + '[inputs.thing]\nkind = "number"\nlabel = "A"\n'
                f"step = {step}{default}\n",
            )
        )


# --- Outputs, and which one is large (§4.5, §4.6, §6) -----------------------


def test_reads_the_declared_outputs_in_display_order(tmp_path: Path) -> None:
    setback, gain = read_manifest(_write(tmp_path, COMPLETE)).outputs

    assert (setback.name, setback.label, setback.unit) == ("setback", "Setback", "mm")
    assert setback.primary is True
    assert (gain.name, gain.unit, gain.primary) == ("gain", "mm", False)


def test_a_lone_output_is_primary_without_saying_so(tmp_path: Path) -> None:
    """Nothing to choose between, so requiring the flag would be ceremony (§1.7)."""
    (only,) = read_manifest(_write(tmp_path, CALCULATOR_HEAD)).outputs

    assert only.primary is True


@pytest.mark.parametrize(
    ("outputs", "because"),
    [
        ("outputs = []", "no Outputs at all"),
        ('outputs = "setback"', "not a list"),
        ('outputs = [{ label = "Setback" }]', "no name"),
        ('outputs = [{ name = "setback" }]', "no label"),
        (
            'outputs = [{ name = "s", label = "S", primary = "yes" }]',
            "non-bool primary",
        ),
        (
            'outputs = [{ name = "s", label = "S" }, { name = "g", label = "G" }]',
            "several Outputs and no primary among them",
        ),
        (
            (
                'outputs = [{ name = "s", label = "S", primary = true },'
                ' { name = "g", label = "G", primary = true }]'
            ),
            "two headlines",
        ),
        (
            'outputs = [{ name = "s", label = "S" }, { name = "s", label = "Again" }]',
            "the same name twice",
        ),
        (
            'outputs = [{ name = "s", label = "S", units = "mm" }]',
            "a key this schema does not define",
        ),
    ],
)
def test_a_malformed_outputs_declaration_raises(
    tmp_path: Path, outputs: str, because: str
) -> None:
    with pytest.raises(ManifestError):
        read_manifest(
            _write(
                tmp_path,
                f'{outputs}\n[applet]\ntype = "calculator"\nname = "T"\n',
            )
        )


def test_a_calculator_without_outputs_is_malformed(tmp_path: Path) -> None:
    """It could render a form and never a Result, which is incomplete (§6)."""
    with pytest.raises(ManifestError, match="outputs"):
        read_manifest(_write(tmp_path, '[applet]\ntype = "calculator"\nname = "T"\n'))


def test_an_unknown_key_inside_an_input_is_rejected_not_ignored(
    tmp_path: Path,
) -> None:
    """The only defence against §4.5's silent misparse of a top-level key."""
    with pytest.raises(ManifestError, match="unknown key 'outputs'"):
        read_manifest(
            _write(
                tmp_path,
                '[applet]\ntype = "calculator"\nname = "T"\n'
                '[inputs.angle]\nkind = "number"\nlabel = "A"\n'
                'outputs = [{ name = "s", label = "S" }]\n',
            )
        )


@pytest.mark.parametrize("key", ["inputs", "outputs", "calibration"])
def test_a_documentation_applet_declares_no_compute_machinery(
    tmp_path: Path, key: str
) -> None:
    """It has no `compute()`, so each of these declares something impossible."""
    with pytest.raises(ManifestError, match=key):
        read_manifest(
            _write(
                tmp_path,
                '[applet]\ntype = "documentation"\nname = "T"\n'
                f'[{key}.thing]\nkind = "number"\nlabel = "A"\n',
            )
        )
