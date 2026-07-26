"""The Manifest (spec §4.1, §4.2, §4.3).

``manifest.toml`` is the author's file and the Host only ever reads it
(ADR-0007), with the stdlib's ``tomllib`` — which cannot write TOML, so the
read-only rule holds by construction.

Every failure here is one fault: the Manifest did not yield metadata. It is
raised as :class:`ManifestError` carrying a human-readable reason, and discovery
turns that reason into a greyed card (§10.1).

The Manifest declares **structure, never logic** (§1.1), so this module reads
declarations and checks them against themselves. It does not build a form and it
does not validate a *user's* value — that is #35's static validation, gated
behind the same declarations.
"""

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


def read_manifest(path: Path) -> Manifest:
    """Read and validate the Manifest at ``path``."""
    document = _load(path)
    applet = _applet_section(document)

    type_ = _required_string(applet, "type")
    if type_ not in APPLET_TYPES:
        raise ManifestError(f"unknown Applet type {type_!r}")
    if type_ == DOCUMENTATION and CALIBRATION_KEY in document:
        # Malformed, not ignored (#15, §3.1): a documentation Applet has no
        # compute() to receive calibration, and interpolating it into content.md
        # would be a template language (§1.1).
        raise ManifestError(
            f"[{CALIBRATION_KEY}] is not allowed on a {DOCUMENTATION} Applet"
        )

    return Manifest(
        type=type_,
        name=_required_string(applet, "name"),
        description=_optional_string(applet, "description"),
        author=_optional_string(applet, "author"),
        tags=_tags(applet),
        inputs=_inputs(document),
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


def _input(name: str, declaration: object) -> Input:
    """Read and self-check one `[inputs.<name>]` declaration."""
    where = f"[{INPUTS_KEY}.{name}]"
    if not isinstance(declaration, dict):
        raise ManifestError(f"{where} must be a table")

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
    if declared.min is not None and value < declared.min:
        _reject_default(where, value, f"is below min {declared.min}")
    if declared.max is not None and value > declared.max:
        _reject_default(where, value, f"is above max {declared.max}")
    # `step = 1` means integer (§4.3). Checking a default against a finer grid
    # needs an anchor the spec does not fix, so it waits for #35's static
    # validation, which has to answer that question for user values anyway.
    if declared.step == 1 and value != int(value):
        _reject_default(where, value, "must be a whole number when step = 1")
    return value


def _reject_default(where: str, value: object, reason: str) -> NoReturn:
    """Raise the one fault an invalid author `default` is (§10.1)."""
    raise ManifestError(f"{where} default {value!r} {reason}")


def _is_number(value: object) -> TypeGuard[float]:
    """Whether ``value`` is a TOML number. ``bool`` is not one, despite `int`."""
    return isinstance(value, int | float) and not isinstance(value, bool)
