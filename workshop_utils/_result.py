"""The Result an Applet returns, and the generic table it may fill (spec §6).

``compute()`` **only ever returns a Result**. Problems raise (§10.2); there is no
error variant, because one would force a union return type on every Applet.

The Applet returns **raw values**. Labels, units, ordering and which Output is
large are the Manifest's, and the formatting is the Host's — so nothing here
carries display strings, and a calculator's Python stays pure compute (§4.5).
"""

from collections.abc import Sequence
from dataclasses import dataclass

Cell = str | float | int | bool | None


@dataclass(frozen=True)
class Row:
    """One table row: its cells, in the table's column order."""

    cells: Sequence[Cell]

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))


@dataclass(frozen=True)
class Group:
    """Rows shown together, under one ``flag`` naming why they are inseparable.

    This is how an Applet **declines honestly**: candidates it cannot tell apart
    are shown as a group naming the discriminator, never one silent winner
    (§11.3).

    It is not an advisory channel (§6.2). A flag says *these rows cannot be told
    apart by what you measured* — a statement about the search, not a caveat
    about the answer.

    **A group is stated, never inferred.** Two collisions that happen to be
    adjacent and to read alike are still two refusals, and no rule over the row
    list could tell them apart — so the boundary is the Applet's to draw.
    """

    rows: Sequence[Row]
    flag: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rows", tuple(self.rows))


@dataclass(frozen=True)
class Table:
    """A header row plus rows, rendered generically by the Host.

    ``rows`` holds plain :class:`Row` s, and a :class:`Group` wherever several
    rows belong together.
    """

    columns: Sequence[str]
    rows: Sequence[Row | Group] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "rows", tuple(self.rows))
        width = len(self.columns)
        for group in self.groups():
            for row in group.rows:
                if len(row.cells) != width:
                    raise ValueError(f"row {row.cells!r} does not fill {width} columns")

    def groups(self) -> tuple[Group, ...]:
        """Every entry as a group, so rendering has one shape to walk."""
        return tuple(
            entry if isinstance(entry, Group) else Group((entry,))
            for entry in self.rows
        )


@dataclass(frozen=True)
class Result:
    """What ``compute()`` returns: values, plus the optional richer channels.

    ``outputs`` is required and guaranteed present (§6); the rest are channels an
    Applet uses if it has something for them. ``html`` is embedded **verbatim** —
    no validation, no sanitisation, nothing promised (§1.3). ``graphic`` is an SVG
    string (or a PNG data URI); the Host ships no graphics dependency and owes
    authors no drawing helpers (§6.1).
    """

    outputs: dict[str, Cell]
    table: Table | None = None
    html: str | None = None
    graphic: str | None = None
