"""The Manifest (spec §4.1, §4.2, §4.3).

``manifest.toml`` is the author's file and the Host only ever reads it
(ADR-0007), with the stdlib's ``tomllib`` — which cannot write TOML, so the
read-only rule holds by construction.

Every failure here is one fault: the Manifest did not yield metadata. It is
raised as :class:`ManifestError` carrying a human-readable reason, and discovery
turns that reason into a greyed card (§10.1).

The Manifest declares **structure, never logic** (§1.1), so this module reads
declarations and checks them against themselves. It does not build a form — that
is :mod:`workshop_helper.form` — but the *rules* a value is checked against live
here, in :func:`constraint_violation`, and are applied to the author's ``default``
and to the user's typed value alike. One rule, one place: a default the Host
accepts and the same figure rejected in the form is the bug that split rule
invites (#33).
"""

import math
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import NoReturn, TypeGuard, cast

from workshop_utils import Cell

MANIFEST_FILENAME = "manifest.toml"
DOCUMENTATION = "documentation"
CALCULATOR = "calculator"
# Closed set: adding a type is a change to the Host (ADR-0005, spec §3).
APPLET_TYPES = frozenset({DOCUMENTATION, CALCULATOR})

NUMBER = "number"
CHOICE = "choice"
BOOL = "bool"
# Also closed: `text` and `pattern` were cut in #24 (spec §4.3).
INPUT_KINDS = frozenset({NUMBER, CHOICE, BOOL})

CALIBRATION_KEY = "calibration"
INPUTS_KEY = "inputs"
OUTPUTS_KEY = "outputs"
MODES_KEY = "modes"
DEFAULT_MODE_KEY = "default_mode"
KEYED_BY_KEY = "keyed_by"
VALUES_KEY = "values"

# The name the Host owns for the derived mode selector. An Input of this name
# would submit under the same key, so declaring one is refused (§4.5).
MODE = "mode"

# An unrecognised key inside a table is rejected, not ignored, because of TOML's
# own scoping rule (§4.5): a top-level `outputs` written *after* a table header
# parses as a key of that table. That is valid TOML and a silently wrong
# document, and this check is the only thing that turns it into a named fault
# rather than a mysteriously absent Output list.
#
# `[applet]` is in the list because it is the **first** table header in every
# Manifest, which makes it the likeliest table for a stray top-level key to fall
# into — the spec names the other three because they are where an author is
# writing when they think of one, not because `[applet]` is safe.
APPLET_KEYS = frozenset({"type", "name", "description", "author", "tags"})
INPUT_KEYS = frozenset(
    {"kind", "label", "unit", "default", "min", "max", "step", "choices"}
)
OUTPUT_KEYS = frozenset({"name", "label", "unit", "primary"})
MODE_KEYS = frozenset({"label", INPUTS_KEY, OUTPUTS_KEY})
CALIBRATION_KEYS = frozenset({KEYED_BY_KEY, VALUES_KEY})

# The same defence where the keys are the author's own: a calibration field may
# be called anything, so the swallowed top-level scalars are named instead.
TOP_LEVEL_SCALARS = frozenset({DEFAULT_MODE_KEY, OUTPUTS_KEY})

# Grid arithmetic is float arithmetic: 0.1 + 0.2 must land on a 0.1 grid.
GRID_TOLERANCE = 1e-9


class ManifestError(Exception):
    """A Manifest is missing, unparseable, or incomplete (spec §10.1)."""


@dataclass(frozen=True)
class Input:
    """One declared Input: a named value a calculator needs in order to compute.

    Every Input is required by definition — there is no ``required`` field
    (§4.3). ``unit`` is a display label and nothing else (§4.4, ADR-0006).
    """

    name: str
    kind: str
    label: str
    unit: str | None = None
    default: str | float | bool | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class Output:
    """One declared Output: a name ``compute()`` must return a value under.

    The Applet returns raw values; the label, the unit and *which one is large*
    are declared here and applied by the Host (§4.5, §6).
    """

    name: str
    label: str
    unit: str | None = None
    primary: bool = False


@dataclass(frozen=True)
class Mode:
    """One named shape of a calculator: its own Inputs and its own Outputs (§4.5).

    A mode changes **what exists**; an Input changes what a thing *is* (§1.4). So
    ``inputs`` is a subset of the pool, referenced by name — a shared Input is
    genuinely one Input, with one kind, one unit and one set of rules, in every
    mode that uses it — and ``outputs`` is declared here, in display order, with
    the primary this mode names.

    A single-mode calculator has one of these too, anonymous and never rendered:
    the degenerate case is the *absence of a section*, not a second code path.
    """

    name: str
    label: str
    inputs: tuple[Input, ...] = ()
    outputs: tuple[Output, ...] = ()


@dataclass(frozen=True)
class Calibration:
    """Measurements of the user's own kit, and which Input selects between them.

    ``values`` is a table per key when ``keyed_by`` names a `choice` Input, and a
    single unnamed row when it does not — so :meth:`resolve` has one shape to
    walk and ``compute()`` receives a flat dict either way (§5.4).
    """

    values: Mapping[str, Mapping[str, Cell]]
    keyed_by: str | None = None

    def resolve(self, inputs: Mapping[str, Cell]) -> dict[str, Cell]:
        """The slice for the selected key, flattened for ``compute()`` (§5.4).

        This cannot raise: §5.3's rule 3 matched the key set to the choice set at
        discovery, in both directions, so the selected value is a key here.
        Making the Applet index it instead would hand back the ``KeyError`` path
        that validation had just eliminated.
        """
        if self.keyed_by is None:
            return dict(self.values[""])
        return dict(self.values[str(inputs[self.keyed_by])])


@dataclass(frozen=True)
class Manifest:
    """An Applet's declaration about itself.

    ``author`` is optional free text for the error blame line (§10.3); it is not
    an identity and means nothing to the Host beyond display.

    ``inputs`` is the whole pool; ``outputs`` is the single-mode calculator's
    top-level list and is empty whenever ``modes`` is not, because the two are
    mutually exclusive ways of saying the same thing (§4.5, §4.6).
    """

    type: str
    name: str
    description: str | None = None
    author: str | None = None
    tags: tuple[str, ...] = ()
    inputs: tuple[Input, ...] = ()
    outputs: tuple[Output, ...] = ()
    modes: tuple[Mode, ...] = ()
    default_mode: str = ""
    calibration: Calibration | None = None


def read_manifest(path: Path) -> Manifest:
    """Read and validate the Manifest at ``path``."""
    document = _load(path)
    applet = _applet_section(document)
    _reject_unknown_keys(applet, APPLET_KEYS, "[applet]")

    type_ = _required_string(applet, "type")
    if type_ not in APPLET_TYPES:
        raise ManifestError(f"unknown Applet type {type_!r}")
    if type_ == DOCUMENTATION:
        # Malformed, not ignored (#15, §3.1). A documentation Applet has no
        # compute(): nothing would receive an Input, nothing would produce an
        # Output, and interpolating calibration into content.md would be a
        # template language (§1.1). Each of these declares something that cannot
        # happen, so each is a mistake worth naming.
        for key in (CALIBRATION_KEY, INPUTS_KEY, OUTPUTS_KEY, MODES_KEY):
            if key in document:
                raise ManifestError(
                    f"{key!r} is not allowed on a {DOCUMENTATION} Applet"
                )

    inputs = _inputs(document)
    modes = _modes(document, inputs) if type_ == CALCULATOR else ()
    return Manifest(
        type=type_,
        name=_required_string(applet, "name"),
        description=_optional_string(applet, "description"),
        author=_optional_string(applet, "author"),
        tags=_tags(applet),
        inputs=inputs,
        outputs=_outputs(document) if type_ == CALCULATOR and not modes else (),
        modes=modes,
        default_mode=_default_mode(document, modes),
        calibration=_calibration(document, inputs, modes),
    )


def read_identity(path: Path) -> tuple[str | None, str | None]:
    """Read ``(name, author)`` for a blame line, tolerantly (§10.3).

    Called *because* something is already wrong, so it answers a different
    question from :func:`read_manifest` and must never raise: a validation
    failure anywhere in the file would otherwise strip the blame line of exactly
    the blame it exists to carry. Anything unusable degrades to ``None`` and the
    caller falls back — to the folder name, and to the Root.
    """
    try:
        applet = _applet_section(_load(path))
    except ManifestError:
        return None, None
    return _display_string(applet, "name"), _display_string(applet, "author")


def _display_string(applet: dict[str, object], key: str) -> str | None:
    """Read a key for display only: unusable is indistinguishable from absent."""
    value = applet.get(key)
    return value if isinstance(value, str) and value else None


def _load(path: Path) -> dict[str, object]:
    """Parse the whole TOML document, or raise with why it could not be read."""
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except OSError as error:
        raise ManifestError(
            f"{MANIFEST_FILENAME} could not be read: {error}"
        ) from error
    except tomllib.TOMLDecodeError as error:
        raise ManifestError(
            f"{MANIFEST_FILENAME} is not valid TOML: {error}"
        ) from error


def _applet_section(document: dict[str, object]) -> dict[str, object]:
    """Pull out the `[applet]` table, raising if it is not there."""
    applet = document.get("applet")
    if not isinstance(applet, dict):
        raise ManifestError("no [applet] section")
    return applet


def _required_string(
    applet: dict[str, object], key: str, where: str = "[applet]"
) -> str:
    """Read a key the Host cannot render the Applet without."""
    value = applet.get(key)
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{where} needs a non-empty string {key!r}")
    return value


def _optional_string(applet: dict[str, object], key: str) -> str | None:
    """Read a key that may be absent — but must be a string when present."""
    value = applet.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ManifestError(f"[applet] {key!r} must be a string")
    return value


def _tags(applet: dict[str, object]) -> tuple[str, ...]:
    """Normalise the tag list at scan: lowercase, trim, collapse runs (§4.2).

    That is the whole rule and it is the semantic ceiling — no kebab-casing, no
    stemming, no synonyms. Two tags that normalise alike are one tag, and a tag
    that normalises to nothing is dropped: both are consequences of the rule,
    since a facet cannot be listed twice and cannot be labelled with nothing.
    """
    tags = applet.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise ManifestError("[applet] tags must be a list of strings")
    normalised = (" ".join(tag.lower().split()) for tag in tags)
    return tuple(dict.fromkeys(tag for tag in normalised if tag))


def _inputs(document: dict[str, object]) -> tuple[Input, ...]:
    """Read the `[inputs.*]` pool in authored order (§4.3).

    Every Input the Applet can use is declared exactly once here, whatever modes
    reference it.
    """
    pool = document.get(INPUTS_KEY, {})
    if not isinstance(pool, dict):
        raise ManifestError(f"[{INPUTS_KEY}.*] must be a table per Input")
    return tuple(_input(name, declaration) for name, declaration in pool.items())


def _modes(document: dict[str, object], inputs: tuple[Input, ...]) -> tuple[Mode, ...]:
    """Read the `[modes.*]` sections, wiring each to the Input pool (§4.5).

    Absent is the ordinary case and not a fault: **simplicity is the absence of
    the section**, and the caller reads a top-level `outputs` list instead.
    """
    declared = document.get(MODES_KEY)
    if declared is None:
        return ()
    if not isinstance(declared, dict) or not declared:
        raise ManifestError(f"[{MODES_KEY}.*] must be a table per mode")
    if OUTPUTS_KEY in document:
        raise ManifestError(
            f"a calculator with [{MODES_KEY}] declares {OUTPUTS_KEY} per mode, "
            "not at the top level"
        )

    pool = {declaration.name: declaration for declaration in inputs}
    if MODE in pool:
        # The selector is derived from the modes themselves, so a second source
        # of truth is refused rather than allowed to drift out of sync (§4.5).
        raise ManifestError(
            f"the {MODE} selector is derived; there is no {MODE!r} Input to declare"
        )
    return tuple(_mode(name, body, pool) for name, body in declared.items())


def _mode(name: str, body: object, pool: dict[str, Input]) -> Mode:
    """Read and self-check one `[modes.<name>]` section."""
    where = f"[{MODES_KEY}.{name}]"
    if not isinstance(body, dict):
        raise ManifestError(f"{where} must be a table")
    _reject_unknown_keys(body, MODE_KEYS, where)
    return Mode(
        name=name,
        label=_required_string(body, "label", where),
        inputs=_mode_inputs(body, pool, where),
        outputs=_output_list(body.get(OUTPUTS_KEY), where),
    )


def _mode_inputs(
    body: dict[str, object], pool: dict[str, Input], where: str
) -> tuple[Input, ...]:
    """Resolve a mode's Input names against the pool, in the order it lists them.

    A name with nothing behind it is a fault and not an empty field: the mode is
    asking for a value the form has no way to collect. Zero Inputs is fine — that
    is the static calculator (§4.6).
    """
    named = body.get(INPUTS_KEY, [])
    if not isinstance(named, list) or not all(isinstance(n, str) for n in named):
        raise ManifestError(f"{where} {INPUTS_KEY!r} must be a list of Input names")
    unknown = [name for name in named if name not in pool]
    if unknown:
        raise ManifestError(f"{where} names {unknown[0]!r}, which is not an Input")
    if len(set(named)) != len(named):
        raise ManifestError(f"{where} names the same Input twice")
    return tuple(pool[name] for name in named)


def _outputs(document: dict[str, object]) -> tuple[Output, ...]:
    """Read the top-level `outputs` list of a single-mode calculator (§4.6)."""
    return _output_list(document.get(OUTPUTS_KEY), where="a calculator")


def _output_list(declared: object, where: str) -> tuple[Output, ...]:
    """Read one Output list — a mode's, or a single-mode calculator's (§4.5).

    Both are the same declaration in two places, so they are one rule: a
    non-empty list, no name twice, and exactly one primary. Declaring no Outputs
    would render a form that can never show a Result, which is incomplete rather
    than minimal.
    """
    if not isinstance(declared, list) or not declared:
        raise ManifestError(f"{where} needs a non-empty {OUTPUTS_KEY!r} list")
    outputs = tuple(_output(entry, where) for entry in declared)

    names = [output.name for output in outputs]
    duplicated = {name for name in names if names.count(name) > 1}
    if duplicated:
        raise ManifestError(f"{where} declares {duplicated.pop()!r} twice")
    return _with_primary(outputs, where)


def _with_primary(outputs: tuple[Output, ...], where: str) -> tuple[Output, ...]:
    """Settle which Output the Host renders large (§4.5).

    Exactly one is primary. A lone Output is it without saying so: there is
    nothing for the flag to choose between, and requiring it would be ceremony
    (§1.7). Two primaries, or none among several, is a headline the author has
    not chosen — the Host will not choose it for them. Each mode names its own,
    which is why the headline changes between modes.
    """
    primary = [output for output in outputs if output.primary]
    if len(primary) > 1:
        raise ManifestError(f"{where} declares more than one primary Output")
    if not primary:
        lone, *rest = outputs
        if rest:
            raise ManifestError(f"{where} declares no primary Output")
        return (replace(lone, primary=True),)
    return outputs


def _default_mode(document: dict[str, object], modes: tuple[Mode, ...]) -> str:
    """Which mode is active when the Applet opens (§4.5).

    A top-level scalar, and therefore one of the two keys the ordering rule can
    swallow — which is why an unrecognised key inside `[inputs.*]`, `[modes.*]`
    and `[calibration.values.*]` is refused rather than ignored. Absent, it is
    the first mode declared; present, it must name one.
    """
    declared = document.get(DEFAULT_MODE_KEY)
    if not modes:
        return ""
    if declared is None:
        return modes[0].name
    if declared not in {mode.name for mode in modes}:
        raise ManifestError(f"{DEFAULT_MODE_KEY} {declared!r} is not a declared mode")
    return str(declared)


def _calibration(
    document: dict[str, object], inputs: tuple[Input, ...], modes: tuple[Mode, ...]
) -> Calibration | None:
    """Read `[calibration]` and enforce §5.3's four discovery rules.

    **The Host branches on `keyed_by`'s presence, never on the shape of what
    follows** — so `[calibration]` admits two keys and nothing else, and a
    typo'd `keyd_by` is a named fault rather than a table silently read as flat.
    """
    section = document.get(CALIBRATION_KEY)
    if section is None:
        return None
    if not isinstance(section, dict):
        raise ManifestError(f"[{CALIBRATION_KEY}] must be a table")
    _reject_unknown_keys(section, CALIBRATION_KEYS, f"[{CALIBRATION_KEY}]")

    values = section.get(VALUES_KEY)
    if not isinstance(values, dict) or not values:
        raise ManifestError(
            f"[{CALIBRATION_KEY}.{VALUES_KEY}] must be a non-empty table"
        )
    if KEYED_BY_KEY not in section:
        where = f"[{CALIBRATION_KEY}.{VALUES_KEY}]"
        return Calibration(values={"": _fields(values, where)})

    keyed_by = _required_string(section, KEYED_BY_KEY, f"[{CALIBRATION_KEY}]")
    _keyed_by_selects(keyed_by, inputs, modes, set(values))
    table = {
        key: _fields(row, f"[{CALIBRATION_KEY}.{VALUES_KEY}.{key}]")
        for key, row in values.items()
    }
    # Rule 4: rectangular. A ragged table makes the *shape* of the resolved dict
    # depend on which key the user selected — a KeyError that fires only for the
    # person who owns the other bender, and never once in the author's testing.
    if len({frozenset(row) for row in table.values()}) > 1:
        raise ManifestError(
            f"[{CALIBRATION_KEY}.{VALUES_KEY}.*] must carry the same fields "
            "under every key"
        )
    return Calibration(values=table, keyed_by=keyed_by)


def _keyed_by_selects(
    keyed_by: str, inputs: tuple[Input, ...], modes: tuple[Mode, ...], keys: set[str]
) -> None:
    """Check that `keyed_by` really does select a slice (§5.3 rules 1–3).

    Rule 3 — the key set equals the choice set **in both directions** — is where
    §1.2 lands in the schema: you cannot offer `28mm` in the choices and leave its
    calibration blank. Either you have measured it or it is not a choice.

    A mode that omits the keying Input is refused for the same reason the Host
    resolves the slice at all (§5.4): with nothing selecting a row there is no
    slice to hand ``compute()``, and the Applet would fail in that mode alone.
    """
    declared = next((i for i in inputs if i.name == keyed_by), None)
    if declared is None:
        raise ManifestError(f"{KEYED_BY_KEY} {keyed_by!r} is not an Input")
    if declared.kind != CHOICE:
        raise ManifestError(f"{KEYED_BY_KEY} {keyed_by!r} is not a {CHOICE} Input")

    choices = set(declared.choices)
    missing = sorted(choices - keys) + sorted(keys - choices)
    if missing:
        raise ManifestError(
            f"[{CALIBRATION_KEY}.{VALUES_KEY}.*] and the {keyed_by!r} choices "
            f"disagree about {missing[0]!r}"
        )
    for mode in modes:
        if declared not in mode.inputs:
            raise ManifestError(
                f"[{MODES_KEY}.{mode.name}] must use {keyed_by!r}, which selects "
                "the calibration"
            )


def _fields(row: object, where: str) -> dict[str, Cell]:
    """Read one calibration row: field names the author chose, scalar values.

    The names are the author's, so the ordering rule cannot be defended by an
    allow-list here (§4.5). The two top-level scalars that a stray key would have
    been are named instead — a `default_mode` that landed in this table is
    exactly the silent misparse the rule exists to catch.
    """
    if not isinstance(row, dict) or not row:
        raise ManifestError(f"{where} must be a non-empty table")
    fields: dict[str, Cell] = {}
    for name, value in row.items():
        if name in TOP_LEVEL_SCALARS:
            raise ManifestError(
                f"{where} has a {name!r} key — a top-level key written below a "
                "table header parses into that table (spec §4.5)"
            )
        if not isinstance(value, str | bool) and not _is_number(value):
            raise ManifestError(f"{where} {name!r} must be a number, string or bool")
        fields[name] = value
    return fields


def _output(entry: object, owner: str) -> Output:
    """Read and self-check one entry of an `outputs` list."""
    if not isinstance(entry, dict):
        raise ManifestError(f"each {owner} {OUTPUTS_KEY} entry must be a table")
    name = _required_string(entry, "name", owner)
    where = f"{owner} {OUTPUTS_KEY} {name!r}"
    _reject_unknown_keys(entry, OUTPUT_KEYS, where)

    primary = entry.get("primary", False)
    if not isinstance(primary, bool):
        raise ManifestError(f"{where} 'primary' must be true or false")
    return Output(
        name=name,
        label=_required_string(entry, "label"),
        unit=_optional_string(entry, "unit"),
        primary=primary,
    )


def _input(name: str, declaration: object) -> Input:
    """Read and self-check one `[inputs.<name>]` declaration."""
    where = f"[{INPUTS_KEY}.{name}]"
    if not isinstance(declaration, dict):
        raise ManifestError(f"{where} must be a table")
    _reject_unknown_keys(declaration, INPUT_KEYS, where)

    kind = _required_string(declaration, "kind")
    if kind not in INPUT_KINDS:
        raise ManifestError(f"{where} unknown Input kind {kind!r}")

    declared = Input(
        name=name,
        kind=kind,
        label=_required_string(declaration, "label"),
        unit=_optional_string(declaration, "unit"),
        min=_optional_number(declaration, "min", where),
        max=_optional_number(declaration, "max", where),
        step=_step(declaration, where),
        choices=_choices(declaration, kind, where),
    )
    return replace(declared, default=_default(declaration, declared, where))


def _choices(declaration: dict[str, object], kind: str, where: str) -> tuple[str, ...]:
    """Read `choices`, required and non-empty for a `choice` Input (§4.3)."""
    choices = declaration.get("choices")
    if kind != CHOICE:
        return ()
    if (
        not isinstance(choices, list)
        or not choices
        or not all(isinstance(choice, str) for choice in choices)
    ):
        raise ManifestError(f"{where} needs a non-empty list of string choices")
    return tuple(choices)


def _step(declaration: dict[str, object], where: str) -> float | None:
    """Read `step`, which is a grid and therefore has to be a positive number.

    Checked here at scan, not where the grid is applied: a Manifest the Host
    cannot validate against is a greyed card (§10.1), and leaving it to the first
    compute would turn an authoring mistake into a mid-request failure on a card
    that looked perfectly healthy.
    """
    step = _optional_number(declaration, "step", where)
    if step is not None and step <= 0:
        raise ManifestError(f"{where} step must be greater than zero, not {step}")
    return step


def _optional_number(
    declaration: dict[str, object], key: str, where: str
) -> float | None:
    """Read a numeric constraint that may be absent."""
    value = declaration.get(key)
    if value is None:
        return None
    if not _is_number(value):
        raise ManifestError(f"{where} {key!r} must be a number")
    return value


def _default(
    declaration: dict[str, object], declared: Input, where: str
) -> str | float | bool | None:
    """Read the author's `default`, checked against this Input's constraints.

    An invalid `default` is a malformed Manifest, never a silent fallback: the
    author writes once for everyone and can be told. (Contrast the Overlay,
    where the *user's* invalid value is dropped in silence — §8, §10.4.)
    """
    value = declaration.get("default")
    if value is None:
        return None
    violation = default_violation(declared, value)
    if violation is not None:
        _reject_default(where, value, violation)
    # Narrowed by the check above: every branch of `default_violation` that
    # returns None has already established the kind.
    return cast(str | float | bool, value)


def default_violation(declared: Input, value: object) -> str | None:
    """Why ``value`` is not admissible as ``declared``'s default, or ``None``.

    One rule, two callers with opposite manners. The **author's** `default` is
    checked at scan and an unusable one is a greyed card (§10.1); the **user's**
    Overlay value is checked at read and an unusable one is dropped in silence,
    with nobody at fault (§8, §10.4). Same question, so it is asked in one place
    — a value the Host would refuse from a Manifest is not one it should quietly
    accept from `overlay.json` merely because the file is its own.
    """
    if declared.kind == BOOL:
        return None if isinstance(value, bool) else "must be true or false"
    if declared.kind == CHOICE:
        if not isinstance(value, str):
            return "must be a string"
        if value not in declared.choices:
            return "is not one of the choices"
        return None
    # `nan` and `inf` are numbers TOML and JSON can both express and no
    # measurement produces; no bound can be checked against them either.
    if not _is_number(value) or not math.isfinite(value):
        return "must be a number"
    return constraint_violation(declared, value)


def constraint_violation(declared: Input, value: float) -> str | None:
    """Why ``value`` is not admissible for ``declared``, or ``None`` if it is.

    The single rule for `min`/`max`/`step`, applied to the author's ``default``
    at scan and to the user's typed value before ``compute()`` runs (§4.3).

    **The `step` grid is anchored at `min`, else at 0** — the browser's own rule
    for ``<input type="number">``. Anchoring it anywhere else would let the
    stepper offer a value the Host then rejects, which is the same figure being
    valid in the widget and invalid in the Host. `step = 1` ⇒ integer falls out
    of this rule unchanged whenever `min` is itself whole.

    ``declared`` has been through :func:`read_manifest`, so `step` is a positive
    number or absent. This never raises: it reports on a *value*, and a Manifest
    the Host cannot work with was refused at scan.
    """
    if declared.min is not None and value < declared.min:
        return f"must be {declared.min} or more"
    if declared.max is not None and value > declared.max:
        return f"must be {declared.max} or less"
    if declared.step is None:
        return None

    anchor = declared.min if declared.min is not None else 0
    if _on_grid(value, declared.step, anchor):
        return None
    if declared.step == 1 and anchor == int(anchor):
        return "must be a whole number, because step = 1 means integer"
    return f"must be a multiple of {declared.step} from {anchor}"


def _on_grid(value: float, step: float, anchor: float) -> bool:
    """Whether ``value`` sits on the ``step`` grid anchored at ``anchor``."""
    steps = (value - anchor) / step
    return math.isclose(steps, round(steps), abs_tol=GRID_TOLERANCE)


def _reject_unknown_keys(
    declaration: dict[str, object], allowed: frozenset[str], where: str
) -> None:
    """Refuse a key this schema does not define (§4.5's ordering rule)."""
    unknown = sorted(set(declaration) - allowed)
    if unknown:
        raise ManifestError(f"{where} has an unknown key {unknown[0]!r}")


def _reject_default(where: str, value: object, reason: str) -> NoReturn:
    """Raise the one fault an invalid author `default` is (§10.1)."""
    raise ManifestError(f"{where} default {value!r} {reason}")


def _is_number(value: object) -> TypeGuard[float]:
    """Whether ``value`` is a TOML number. ``bool`` is not one, despite `int`."""
    return isinstance(value, int | float) and not isinstance(value, bool)
