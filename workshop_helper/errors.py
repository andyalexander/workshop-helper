"""The error surface every fault renders through (spec §10.3).

**One layered surface, not two audiences.** A local single-user tool cannot
authenticate "user" versus "author", so it shows a plain blame line over a
collapsed Details disclosure and lets the reader decide how far to look.

Both halves of §10 render through here: discovery-time faults carry a reason
(§10.1, this ticket) and compute-time faults carry a full traceback (§10.2, #35).
Keeping the string here rather than in a template is what makes the `author`
fallback a tested rule instead of a Jinja expression.
"""

from dataclasses import dataclass

BLAME = "{name} — from Root '{root_name}', by {author}"


@dataclass(frozen=True)
class ErrorSurface:
    """A blame line over the Details a reader can open if they want it."""

    blame: str
    details: str


def error_surface(
    name: str, root_name: str, details: str, author: str | None = None
) -> ErrorSurface:
    """Build the surface for one fault, degrading ``author`` to the Root name.

    An Applet's ``author`` is optional free text (§4.1). When it is absent the
    Root is the only provenance left, and provenance is exactly what the blame
    line is for.
    """
    return ErrorSurface(
        blame=BLAME.format(name=name, root_name=root_name, author=author or root_name),
        details=details,
    )
