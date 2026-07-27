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
from dataclasses import dataclass, replace
from pathlib import Path
from typing import NoReturn, TypeGuard

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

# An unrecognised key inside `[inputs.*]` is rejected, not ignored, because of
# TOML's own scoping rule (§4.5): a top-level `outputs` written *after* the first
# table header parses as a key of that table. That is valid TOML and a silently
# wrong document, and this check is the only thing that turns it into a named
# fault rather than a mysteriously absent Output list.
INPUT_KEYS = frozenset(
    {"kind", "label", "unit", "default", "min", "max", "step", "choices"}
)
OUTPUT_KEYS = frozenset({"name", "label", "unit", "primary"})

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
class Manifest:
    """An Applet's declaration about itself.

    ``author`` is optional free text for the error blame line (§10.3); it is not
    an identity and means nothing to the Host beyond display.
    """

    type: str
    name: str
    description: str | None = None
    author: str | None = None
    tags: tuple[str, ...] = ()
    inputs: tuple[Input, ...] = ()
    outputs: tuple[Output, ...] = ()


def read_manifest(path: Path) -> Manifest:
    """Read and validate the Manifest at ``path``."""
    document = _load(path)
    applet = _applet_section(document)

    type_ = _required_string(applet, "type")
    if type_ not in APPLET_TYPES:
        raise ManifestError(f"unknown Applet type {type_!r}")
    if type_ == DOCUMENTATION:
        # Malformed, not ignored (#15, §3.1). A documentation Applet has no
        # compute(): nothing would receive an Input, nothing would produce an
        # Output, and interpolating calibration into content.md would be a
        # template language (§1.1). Each of these declares something that cannot
        # happen, so each is a mistake worth naming.
        for key in (CALIBRATION_KEY, INPUTS_KEY, OUTPUTS_KEY):
            if key in document:
                raise ManifestError(
                    f"{key!r} is not allowed on a {DOCUMENTATION} Applet"
                )

    return Manifest(
        type=type_,
        name=_required_string(applet, "name"),
        description=_optional_string(applet, "description"),
        author=_optional_string(applet, "author"),
        tags=_tags(applet),
        inputs=_inputs(document),
        outputs=_outputs(document) if type_ == CALCULATOR else (),
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


def _required_string(applet: dict[str, object], key: str) -> str:
    """Read a key the Host cannot render the Applet without."""
    value = applet.get(key)
    if not isinstance(value, str) or not value:
        raise ManifestError(f"[applet] needs a non-empty string {key!r}")
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
    reference it; wiring modes to this pool is #36.
    """
    pool = document.get(INPUTS_KEY, {})
    if not isinstance(pool, dict):
        raise ManifestError(f"[{INPUTS_KEY}.*] must be a table per Input")
    return tuple(_input(name, declaration) for name, declaration in pool.items())


def _outputs(document: dict[str, object]) -> tuple[Output, ...]:
    """Read the top-level `outputs` list of a single-mode calculator (§4.6).

    A calculator that declares no Outputs can render a form and never a Result,
    so an empty list is incomplete rather than minimal. Per-mode Outputs are #36;
    when they arrive, this becomes the no-`[modes]` branch of the same rule.
    """
    declared = document.get(OUTPUTS_KEY)
    if not isinstance(declared, list) or not declared:
        raise ManifestError(
            f"a {CALCULATOR} needs a non-empty top-level {OUTPUTS_KEY!r} list"
        )
    outputs = tuple(_output(entry) for entry in declared)

    names = [output.name for output in outputs]
    duplicated = {name for name in names if names.count(name) > 1}
    if duplicated:
        raise ManifestError(f"{OUTPUTS_KEY} declares {duplicated.pop()!r} twice")
    return _with_primary(outputs)


def _with_primary(outputs: tuple[Output, ...]) -> tuple[Output, ...]:
    """Settle which Output the Host renders large (§4.5).

    Exactly one is primary. A lone Output is it without saying so: there is
    nothing for the flag to choose between, and requiring it would be ceremony
    (§1.7). Two primaries, or none among several, is a headline the author has
    not chosen — the Host will not choose it for them.
    """
    primary = [output for output in outputs if output.primary]
    if len(primary) > 1:
        raise ManifestError(f"{OUTPUTS_KEY} declares more than one primary Output")
    if not primary:
        lone, *rest = outputs
        if rest:
            raise ManifestError(f"{OUTPUTS_KEY} declares no primary Output")
        return (replace(lone, primary=True),)
    return outputs


def _output(entry: object) -> Output:
    """Read and self-check one entry of the `outputs` list."""
    if not isinstance(entry, dict):
        raise ManifestError(f"each {OUTPUTS_KEY} entry must be a table")
    name = _required_string(entry, "name")
    where = f"{OUTPUTS_KEY} {name!r}"
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
        step=_optional_number(declaration, "step", where),
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

    if declared.kind == BOOL:
        if not isinstance(value, bool):
            _reject_default(where, value, "must be true or false")
        return value
    if declared.kind == CHOICE:
        if not isinstance(value, str):
            _reject_default(where, value, "must be a string")
        if value not in declared.choices:
            _reject_default(where, value, "is not one of the choices")
        return value
    return _number_default(value, declared, where)


def _number_default(value: object, declared: Input, where: str) -> float:
    """Check a `number` Input's default against its own bounds and step (§4.3)."""
    if not _is_number(value):
        _reject_default(where, value, "must be a number")
    violation = constraint_violation(declared, value)
    if violation is not None:
        _reject_default(where, value, violation)
    return value


def constraint_violation(declared: Input, value: float) -> str | None:
    """Why ``value`` is not admissible for ``declared``, or ``None`` if it is.

    The single rule for `min`/`max`/`step`, applied to the author's ``default``
    at scan and to the user's typed value before ``compute()`` runs (§4.3).

    **The `step` grid is anchored at `min`, else at 0** — the browser's own rule
    for ``<input type="number">``. Anchoring it anywhere else would let the
    stepper offer a value the Host then rejects, which is the same figure being
    valid in the widget and invalid in the Host. `step = 1` ⇒ integer falls out
    of this rule unchanged whenever `min` is itself whole.
    """
    if declared.min is not None and value < declared.min:
        return f"must be {declared.min} or more"
    if declared.max is not None and value > declared.max:
        return f"must be {declared.max} or less"
    if declared.step is None:
        return None
    if declared.step <= 0:
        raise ManifestError(f"step must be greater than zero, not {declared.step}")

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
