"""What the Result region shows, and how a value is written (spec §6).

The Applet returns raw values and the **Host formats, labels, units and ranks**
them. That split is why this module exists at all: an Applet that formatted its
own figures would be deciding how the Host's page looks, and the labels and units
it would need are in the Manifest, not in its hands.
"""

import math
from dataclasses import dataclass

from workshop_helper.errors import ErrorSurface
from workshop_helper.manifest import Output
from workshop_utils import Cell, Result

NOTHING = "—"


@dataclass(frozen=True)
class Computation:
    """A Result, a fault, or neither yet.

    Neither is not a failure state — it is a partly-filled form on an Applet that
    does not compute on open (§4.6), and the region says so rather than showing
    an empty answer.
    """

    result: Result | None = None
    surface: ErrorSurface | None = None

    def shown(self, outputs: tuple[Output, ...]) -> list[tuple[Output, Cell]]:
        """Declared Outputs paired with their values, in display order (§4.5)."""
        if self.result is None:
            return []
        return [(output, self.result.outputs[output.name]) for output in outputs]


def figure(value: Cell) -> str:
    """Write one value out for display.

    A missing cell is an em dash and not a zero: the thread finder's BA rows have
    no published tap drill, and an empty cell is honest where a computed one
    would be a lookup that never happened (#25 §3.4).
    """
    if value is None:
        return NOTHING
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int | float):
        if not math.isfinite(value):
            return NOTHING
        # `g` drops the trailing zeros an exact figure does not have: 8.0 is 8,
        # and 1.250 is 1.25, without rounding 20.955 to something tidier.
        return f"{value:g}"
    return value
