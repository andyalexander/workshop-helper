"""The Result an Applet returns, and the generic table it may fill (spec §6).

``compute()`` **only ever returns a Result**. Problems raise (§10.2); there is no
error variant, because one would force a union return type on every Applet.

The Applet returns **raw values**. Labels, units, ordering and which Output is
large are the Manifest's, and the formatting is the Host's — so nothing here
carries display strings, and a calculator's Python stays pure compute (§4.5).
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field

Cell = str | float | int | bool | None


@dataclass(frozen=True)
class Row:
    """One table row, optionally flagged as part of a tied group.

    ``flag`` is a sentence the Host renders once over the run of rows carrying
    it. It exists for the case where the Applet **declines honestly**: candidates
    it cannot separate are shown together, naming the discriminator, never one
    silent winner (§11.3).

    It is not an advisory channel (§6.2). A flag says *these rows cannot be told
    apart by what you measured* — a statement about the search, not a caveat
    about the answer.
    """

    cells: Sequence[Cell]
    flag: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))


@dataclass(frozen=True)
class Table:
    """A header row plus rows, rendered generically by the Host.

    Grouping is **adjacency**: a run of consecutive rows sharing one ``flag`` is
    one group. Two separate collisions are therefore two groups even when the
    sentence is identical, and no row needs a group id it would have to keep in
    step with its neighbours.
    """

    columns: Sequence[str]
    rows: Sequence[Row] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "rows", tuple(self.rows))
        width = len(self.columns)
        for row in self.rows:
            if len(row.cells) != width:
                raise ValueError(f"row {row.cells!r} does not fill {width} columns")

    def groups(self) -> Iterator[tuple[str | None, list[Row]]]:
        """Walk the rows as ``(flag, rows)`` runs, in order."""
        runs: list[tuple[str | None, list[Row]]] = []
        for row in self.rows:
            if runs and runs[-1][0] == row.flag and row.flag is not None:
                runs[-1][1].append(row)
            else:
                runs.append((row.flag, [row]))
        return iter(runs)


@dataclass(frozen=True)
class Result:
    """What ``compute()`` returns: values, plus the optional richer channels.

    ``html`` is embedded **verbatim** — no validation, no sanitisation, nothing
    promised (§1.3). ``graphic`` is an SVG string (or a PNG data URI); the Host
    ships no graphics dependency and owes authors no drawing helpers (§6.1).
    """

    outputs: dict[str, Cell] = field(default_factory=dict)
    table: Table | None = None
    html: str | None = None
    graphic: str | None = None
