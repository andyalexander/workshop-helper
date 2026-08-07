"""The Overlay: the Host-owned file of user overrides (spec §8, ADR-0007).

**The Host never writes a Manifest.** Every value the user overrides — a saved
input default, a corrected calibration figure beside it — goes to
``overlay.json``, keyed by Applet id and namespaced by override kind, and is
merged back over the author's declaration at read time by :func:`overlaid`.
**Every Root is read-only to the Host**; there is no writability probing here
because there is nothing to probe for.

Two asymmetries carry the design:

- **A Manifest is authored once for everyone; the Overlay is one person's
  correction.** So an author's invalid `default` is a greyed card and the same
  figure stored here is dropped in silence, with nobody at fault and nothing
  reported (§10.4). The rule both are checked against is one function,
  :func:`~workshop_helper.manifest.default_violation`.
- **Calibration merges field by field, never by slice** (§8.1), and is stored
  **sparse** — only what differs from the author. Slice replacement would strip
  a user's correction the day the author adds a second field to that row; a
  dense store would silently pin every *other* field to the value it had when
  they last pressed Save.

Both land on the **discardable invariant** (§8.2): deleting ``overlay.json``
returns the Host to a pristine state. Nothing here is migrated or versioned —
the drop rule *is* the migration strategy — and nothing the Host cannot
reconstruct from Manifests lives only in this file. The file is re-read on every
lookup rather than cached, which is what makes that invariant observable while
the Host is running: delete it and the next page is pristine.
"""

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from workshop_helper.discovery import Applet
from workshop_helper.form import Form
from workshop_helper.manifest import Calibration, Input, default_violation
from workshop_utils import Cell

OVERLAY_FILENAME = "overlay.json"

# The override kinds. Namespaced so an Input and a calibration field of the same
# name never collide — an Applet may legitimately have both (§8).
DEFAULTS = "defaults"
CALIBRATION = "calibration"

# The key an unkeyed calibration's single row is stored under, matching the
# Manifest's own flattening (§5.4) so one shape is merged either way.
UNKEYED = ""

# Calibration fields post under their own prefix for the same reason the Overlay
# namespaces them: the form carries Inputs and calibration fields together, and
# `r_centreline` may be both.
FIELD_PREFIX = "cal:"


class Overlay:
    """Every user override, read from and written to one JSON file.

    JSON because the file is machine-written and Host-owned; TOML is reserved
    for the hand-authored files the Host only reads. The extension carries the
    ownership rule, so no ``DO NOT EDIT`` banner is needed (ADR-0007).
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    # --- reading ---------------------------------------------------------

    def defaults(self, applet_id: str) -> dict[str, Cell]:
        """The Applet's saved input defaults, by Input name."""
        return _cells(self._kind(applet_id, DEFAULTS))

    def calibration(self, applet_id: str) -> dict[str, dict[str, Cell]]:
        """The Applet's calibration corrections, by key then field name."""
        return {
            key: _cells(row)
            for key, row in self._kind(applet_id, CALIBRATION).items()
            if isinstance(row, dict)
        }

    # --- writing ---------------------------------------------------------

    def save_defaults(self, applet_id: str, values: Mapping[str, Cell]) -> None:
        """Merge ``values`` into this Applet's saved defaults.

        Merged, not replaced: the form on screen carries **one mode's** Inputs
        while the saved defaults are the whole pool's, so replacing would throw
        away the other modes' saved values every time Save was pressed in this
        one (§4.5).
        """
        self._store(applet_id, DEFAULTS, {**self.defaults(applet_id), **values})

    def clear_defaults(self, applet_id: str) -> None:
        """Drop every saved default, returning the form to the author's."""
        self._store(applet_id, DEFAULTS, {})

    def save_calibration(
        self, applet_id: str, key: str, fields: Mapping[str, Cell]
    ) -> None:
        """Replace one key's corrections with ``fields``, leaving other keys be.

        Replacing *within the key* is what keeps the store sparse: a field the
        user has just typed back to the author's figure is absent from
        ``fields`` and must therefore stop being an override, not linger as one
        that happens to agree.
        """
        self._store_row(applet_id, key, dict(fields))

    def reset_calibration(self, applet_id: str, key: str, field: str) -> None:
        """Drop one field's correction, restoring the author's value (§5.5)."""
        row = self.calibration(applet_id).get(key, {})
        self._store_row(applet_id, key, _without(row, field))

    def _store_row(self, applet_id: str, key: str, row: Mapping[str, Cell]) -> None:
        """Write one key's row, leaving every other key's corrections alone."""
        stored = self.calibration(applet_id)
        self._store(
            applet_id,
            CALIBRATION,
            {**stored, key: dict(row)} if row else _without(stored, key),
        )

    # --- the file --------------------------------------------------------

    def _read(self) -> dict[str, Any]:
        """The whole file, or nothing at all.

        Missing, unreadable or unparseable are one case and none of them is an
        error: the Overlay is discardable by definition, so a file the Host
        cannot read is a Host with no overrides (§8.2, §10.4).
        """
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def _kind(self, applet_id: str, kind: str) -> dict[str, Any]:
        """One Applet's entries under one override kind, tolerantly."""
        applet = self._read().get(applet_id)
        if not isinstance(applet, dict):
            return {}
        stored = applet.get(kind)
        return stored if isinstance(stored, dict) else {}

    def _store(self, applet_id: str, kind: str, table: Mapping[str, Any]) -> None:
        """Write one Applet's entries under one override kind.

        Every other Applet's entries are carried through untouched. **Orphans
        are never pruned** (§8): an Applet missing from this scan may simply have
        an unmounted Root, and pruning would destroy defaults for something that
        is coming back.
        """
        entries = self._read()
        applet = entries.get(applet_id)
        if not isinstance(applet, dict):
            applet = {}
        # An emptied kind is removed rather than left as `{}`, so "saved nothing"
        # and "never saved" are the same file — the discardable invariant read
        # one Applet at a time.
        applet = {**applet, kind: dict(table)} if table else _without(applet, kind)
        entries = (
            {**entries, applet_id: applet} if applet else _without(entries, applet_id)
        )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def overlaid(applet: Applet, overlay: Overlay) -> Applet:
    """``applet`` as this user sees it: the author's declaration, overridden.

    Merging into the indexed Applet rather than teaching each consumer about the
    Overlay is what makes §4.6's consequence fall out instead of being coded: an
    overridden `default` is a `default`, so ``computes_on_open`` answers
    differently for a user who has saved one, and nothing in the form, the
    round-trip or ``compute()`` knows the Overlay exists.
    """
    inputs = _defaulted(applet.inputs, overlay.defaults(applet.id))
    pool = {declared.name: declared for declared in inputs}
    return replace(
        applet,
        inputs=inputs,
        # A mode holds the same Input objects as the pool. Re-resolving through
        # the pool keeps that true: an override reaching only one of the two
        # would show a saved default on the form and not in `computes_on_open`.
        modes=tuple(
            replace(mode, inputs=tuple(pool[i.name] for i in mode.inputs))
            for mode in applet.modes
        ),
        calibration=_calibrated(applet.calibration, overlay.calibration(applet.id)),
    )


@dataclass(frozen=True)
class CalibrationField:
    """One calibration field of the active key, as the disclosure shows it."""

    name: str
    authored: Cell
    value: Cell

    @property
    def input_name(self) -> str:
        """What this field posts under, prefixed away from the Inputs (§8)."""
        return FIELD_PREFIX + self.name


@dataclass(frozen=True)
class CalibrationView:
    """The active key's calibration slice, ready to render (§5.5).

    **The active key only.** The other keys are other people's benders, or the
    same bender in a size this calculation is not about.
    """

    key: str
    fields: tuple[CalibrationField, ...]


def calibration_view(
    authored: Calibration | None, applied: Calibration | None, form: Form
) -> CalibrationView | None:
    """The disclosure's contents, or ``None`` when there is nothing to show.

    ``applied`` is the merged calibration ``compute()`` will actually receive, so
    the boxes show the figures in use; ``authored`` is what *reset* restores.
    """
    if authored is None or applied is None:
        return None
    key = _active_key(applied, form)
    if key is None:
        return None
    # `_calibrated` preserves the authored key and field sets exactly, so the
    # two rows are indexable by each other's names.
    original = authored.values[key]
    return CalibrationView(
        key=key,
        fields=tuple(
            CalibrationField(name=name, authored=original[name], value=value)
            for name, value in applied.values[key].items()
        ),
    )


def submitted_calibration(
    view: CalibrationView, submitted: Mapping[str, str]
) -> dict[str, Cell]:
    """Read the disclosure back, keeping only what differs from the author.

    Each field is parsed as the kind the author wrote, because a calibration
    field has no declaration to check against — the names and the types are the
    author's own (§5.2), so the authored value *is* the schema. A value that
    will not parse is not reported: the Overlay's manner is silence (§10.4).

    **Silence means the figure in use stands, not that the field is absent.**
    The row returned here *replaces* the stored one, so a field left out is
    deleted rather than left alone — and a mistyped box would take the bench
    measurement it was typed over with it, with no message and no undo. Falling
    back to ``field.value`` is what makes §10.4's promise true: the box comes
    back showing the figure still in force.

    Keeping only the differences is §8.1's sparseness. Store the whole slice and
    a field the user never touched is pinned to today's authored value forever,
    which is the exact failure field-level merging exists to prevent. The two
    rules meet cleanly here because ``field.value`` is the merged figure: where
    there is no override to preserve it already equals ``authored``, and the
    same comparison drops it.
    """
    corrected: dict[str, Cell] = {}
    for field in view.fields:
        parsed = _parsed(field, submitted)
        value = field.value if parsed is None else parsed
        if value != field.authored:
            corrected[field.name] = value
    return corrected


def _parsed(field: CalibrationField, submitted: Mapping[str, str]) -> Cell | None:
    """One submitted calibration field, as the author's own kind."""
    if isinstance(field.authored, bool):
        # A checkbox has no invalid state and an unticked one sends nothing.
        return field.input_name in submitted
    raw = submitted.get(field.input_name, "").strip()
    if not raw:
        return None
    if isinstance(field.authored, int | float):
        try:
            number = float(raw)
        except ValueError:
            return None
        return number if math.isfinite(number) else None
    return raw


def _active_key(calibration: Calibration, form: Form) -> str | None:
    """Which calibration slice this form selects, or ``None`` if none does."""
    if calibration.keyed_by is None:
        return UNKEYED
    for field in form.fields:
        if field.declared.name == calibration.keyed_by:
            # `raw` covers the round-trip where some *other* field is invalid:
            # the slice on screen must still be the one the user is looking at.
            key = field.raw if field.value is None else str(field.value)
            return key if key in calibration.values else None
    return None


def _defaulted(
    inputs: tuple[Input, ...], saved: Mapping[str, Cell]
) -> tuple[Input, ...]:
    """Override each Input's `default` with the user's, where it still fits."""
    return tuple(
        _with_default(declared, saved.get(declared.name)) for declared in inputs
    )


def _with_default(declared: Input, value: Cell | None) -> Input:
    """One Input, carrying the user's saved default iff it is still admissible.

    Rot is ordinary and nobody is at fault: the author may rename the Input,
    narrow `max` from 90 to 45, or turn a `number` into a `choice`, all while the
    Manifest stays perfectly valid (§8).
    """
    if value is None or default_violation(declared, value) is not None:
        return declared
    return replace(declared, default=value)


def _calibrated(
    calibration: Calibration | None, saved: Mapping[str, Mapping[str, Cell]]
) -> Calibration | None:
    """Merge the user's corrections into the authored calibration (§8.1)."""
    if calibration is None or not saved:
        return calibration
    return replace(
        calibration,
        values={
            key: _row(row, saved.get(key, {}))
            for key, row in calibration.values.items()
        },
    )


def _row(authored: Mapping[str, Cell], saved: Mapping[str, Cell]) -> dict[str, Cell]:
    """Merge one slice field by field, keeping every field the author declared.

    Iterating the *authored* row is what makes this field-level rather than
    slice replacement, and it drops orphans and unknown fields by construction:
    a key the author has removed, or a field they have renamed, simply has
    nothing to merge into. The shape of every row is therefore untouched, so
    §5.3's rectangularity survives whatever is in the file.
    """
    corrections = {
        name: value
        for name, value in saved.items()
        if name in authored and _same_kind(authored[name], value)
    }
    return {**authored, **corrections}


def _same_kind(authored: Cell, value: Cell) -> bool:
    """Whether a stored correction is still the kind of thing the author wrote."""
    if isinstance(authored, bool):
        return isinstance(value, bool)
    if isinstance(authored, int | float):
        return (
            isinstance(value, int | float)
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
    return isinstance(value, str)


def _cells(table: Mapping[str, Any]) -> dict[str, Cell]:
    """Keep only the entries that are scalars a Manifest could have declared."""
    return {
        name: value
        for name, value in table.items()
        if isinstance(value, str | int | float | bool)
    }


def _without(table: Mapping[str, Any], key: str) -> dict[str, Any]:
    """``table`` without ``key``."""
    return {name: value for name, value in table.items() if name != key}
