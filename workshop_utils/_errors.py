"""The one healthy refusal an Applet may raise (spec §10.2).

``compute()`` only ever *returns* a :class:`~workshop_utils.Result`; everything
else raises, and everything else is an unplanned crash. ``InvalidInput`` is the
single exception to that reading, and it exists for exactly one gap static
validation cannot reach: a **cross-field** condition. `min`/`max`/`step` are
declared and hard-gate ``compute()`` before it runs (§4.3), but *"this offset is
impossible at this angle on this former"* names three Inputs at once, which is
not expressible in a Manifest (§1.1) and has no channel in the Result (§6).

It is deliberately **field-targeted**: the Host renders the message inline
against the named Input(s), exactly like a `min` failure. That is *"refuse,
don't round"* — a geometrically impossible step gets a specific message against
`offset`, not a plausible wrong number.
"""

from collections.abc import Sequence


class InvalidInput(Exception):
    """Refuse a valid-typed but impossible combination, naming what to change.

    ``inputs`` names the Input(s) the message belongs against, and is required:
    a refusal with nowhere to render is a message the user never sees, which is
    the silent failure this class exists to prevent.
    """

    def __init__(self, message: str, inputs: Sequence[str]) -> None:
        super().__init__(message)
        self.message = message
        self.inputs = tuple(inputs)
