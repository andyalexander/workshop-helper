"""The form built from the Inputs pool, and the gate in front of ``compute()``.

Spec §4.3, §4.6.

**Static validation hard-gates ``compute()``.** A :class:`Form` yields ``values``
only when every declared Input holds an admissible value, so a route has nothing
to run the Applet with until then. That is what makes §4.3's promise —
*"``compute()`` always receives every declared Input, already validated, never
``None``"* — a property of the type rather than a discipline the routes keep.

The rules themselves are not here. `min`/`max`/`step` live with the declaration
they belong to (:func:`~workshop_helper.manifest.constraint_violation`), because
the author's ``default`` is checked against exactly the same rule at scan (#33).
This module only turns strings from a browser into declared kinds, and remembers
what the user typed so an invalid value is shown back rather than swallowed.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace

from workshop_helper.manifest import BOOL, CHOICE, Input, constraint_violation
from workshop_utils import Cell, InvalidInput

REQUIRED = "needs a value"
NOT_A_NUMBER = "must be a number"
NOT_A_CHOICE = "is not one of the choices"


@dataclass(frozen=True)
class Field:
    """One Input as the form renders it: what to show, and what is wrong.

    ``raw`` is the string to put back in the widget and ``checked`` the
    equivalent for a checkbox. Both are display state; ``value`` is the parsed,
    validated thing ``compute()`` would receive.

    ``value`` is ``None`` **exactly when there is nothing to run** — a value the
    user got wrong, or one nobody has supplied yet. ``Cell`` admits ``None``, but
    no validated Input ever produces it: a number is a float, a choice is one of
    its own strings, and a checkbox is a bool.

    ``error`` is a fragment the Host completes with the Input's own label —
    *"Bend angle must be 180 or less"*. ``refusal`` is the Applet's own sentence,
    shown as written (§10.2), which is why it is a second field and not the same
    one: the Host has no business prefixing a message it did not compose.
    """

    declared: Input
    raw: str = ""
    checked: bool = False
    value: Cell | None = None
    error: str | None = None
    refusal: str | None = None


@dataclass(frozen=True)
class Form:
    """Every field of one Applet, and the verdict over all of them."""

    fields: tuple[Field, ...]

    @property
    def values(self) -> dict[str, Cell] | None:
        """The validated Inputs, or ``None`` when there is nothing to run.

        ``None`` covers both halves of "not ready": a value the user got wrong,
        and a value nobody has supplied yet on an Applet that does not compute on
        open. Neither is a state ``compute()`` may be reached from.
        """
        if any(field.value is None for field in self.fields):
            return None
        return {field.declared.name: field.value for field in self.fields}

    @property
    def supplied(self) -> dict[str, Cell]:
        """Every field holding an admissible value, whatever the verdict overall.

        What save-as-defaults saves (§8). The gate in front of ``compute()`` is
        not a gate in front of the Overlay: a half-filled form still has values
        worth keeping, and saving three of five Inputs is exactly how a
        partially-defaulted Applet becomes one that computes on open (§4.6).
        """
        return {f.declared.name: f.value for f in self.fields if f.value is not None}

    @property
    def errors(self) -> list[str]:
        """The names of the Inputs the user must fix, in declared order."""
        return [f.declared.name for f in self.fields if f.error is not None]


def computes_on_open(inputs: tuple[Input, ...]) -> bool:
    """Whether the Host computes a Result as soon as the Applet opens (§4.6).

    Iff every Input has a default — which makes the **static** calculator fall
    out of the general rule, zero Inputs being vacuously all-defaulted, rather
    than needing a path of its own.
    """
    return all(declared.default is not None for declared in inputs)


def build_form(inputs: tuple[Input, ...], submitted: Mapping[str, str] | None) -> Form:
    """Build the form, from the declared defaults or from what was submitted.

    ``submitted is None`` is the Applet being opened; a mapping is a compute
    round-trip, where a field left blank submits an empty string and is refused.

    **A key missing from the submission falls back to the declared default**, and
    that is what makes changing mode work: the form that was on screen carries
    the *old* mode's Inputs, so an Input only the new mode has arrives absent
    rather than blank. A shared Input keeps whatever the user had typed, because
    it is genuinely the same Input in both modes (§4.5).
    """
    return Form(tuple(_field(declared, submitted) for declared in inputs))


def refuse(form: Form, refusal: InvalidInput) -> Form:
    """Put an Applet's ``InvalidInput`` back against the fields it names (§10.2).

    The refusal renders exactly where a `min`/`max` failure would, because that
    is the whole point of it being field-targeted: the user is told which box to
    change, not handed a plausible wrong number.
    """
    named = set(refusal.inputs)
    return Form(
        tuple(
            replace(field, refusal=refusal.message)
            if field.declared.name in named
            else field
            for field in form.fields
        )
    )


def _field(declared: Input, submitted: Mapping[str, str] | None) -> Field:
    """Build one field, validating it if there is anything to validate."""
    if declared.kind == BOOL:
        return _bool_field(declared, submitted)
    if submitted is None or declared.name not in submitted:
        # `str`, never the Host's display formatting: this string goes back into
        # a box the user can press Compute on, and `figure`'s six significant
        # digits would quietly round a default before anything computed with it.
        raw = "" if declared.default is None else str(declared.default)
        return _validated(declared, raw) if raw else Field(declared)
    return _validated(declared, submitted[declared.name])


def _bool_field(declared: Input, submitted: Mapping[str, str] | None) -> Field:
    """A checkbox has no invalid state: it is ticked or it is not.

    An unticked box sends nothing at all, which is why absence here means
    ``False`` and not "missing" — the one place a missing key is not a refusal.
    """
    ticked = bool(declared.default) if submitted is None else declared.name in submitted
    return Field(declared, checked=ticked, value=ticked)


def _validated(declared: Input, raw: str) -> Field:
    """Check one submitted string against its own declaration."""
    text = raw.strip()
    if not text:
        return Field(declared, raw=raw, error=REQUIRED)
    if declared.kind == CHOICE:
        if text not in declared.choices:
            return Field(declared, raw=raw, error=NOT_A_CHOICE)
        return Field(declared, raw=raw, value=text)

    try:
        number = float(text)
    except ValueError:
        return Field(declared, raw=raw, error=NOT_A_NUMBER)
    if not math.isfinite(number):
        # `float` accepts "nan" and "inf"; no bound can then be checked, and an
        # Applet would receive a value no measurement produces.
        return Field(declared, raw=raw, error=NOT_A_NUMBER)

    violation = constraint_violation(declared, number)
    if violation is not None:
        return Field(declared, raw=raw, error=violation)
    return Field(declared, raw=raw, value=number)
