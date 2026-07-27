"""The only Host-owned name an Applet may import (spec §7.1).

A no-leak facade: no third-party type appears in any signature, return value, or
exception. ``InvalidInput`` ships with its consumer, the pipe-bender's cross-field
refusal (#36) — shipping it unexercised would mean inferring how a field-targeted
message renders, and that surface is not nil (§1.6).
"""

from workshop_utils._errors import InvalidInput
from workshop_utils._markdown import render_markdown
from workshop_utils._result import Cell, Group, Result, Row, Table

__all__ = [
    "Cell",
    "Group",
    "InvalidInput",
    "Result",
    "Row",
    "Table",
    "render_markdown",
]
