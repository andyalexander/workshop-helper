"""PROTOTYPE — throwaway. Restyle variants for the Browse page.

Not part of the Host. This module answers one question — *what should Browse
look like?* — by serving three structurally different renderings of the same
Browse data behind ``?variant=``, plus a floating switcher to flip between them.

It is off unless ``WORKSHOP_HELPER_PROTOTYPE=1`` is in the environment, so a
stray merge cannot ship the switcher to a workshop. Delete this file, the
``templates/prototype/`` folder, and the few lines it costs ``browse()`` once a
variant has won.
"""

import os
from collections.abc import Callable
from typing import Any

VARIANT_PARAM = "variant"

#: Variant key -> the name the switcher shows.
VARIANTS = {
    "A": "Bench — warm card grid",
    "B": "Index — dense typographic list",
    "D": "Bench Index — B's rows, A's surface",
}


def enabled() -> bool:
    """Whether the prototype hook is switched on for this process."""
    return os.environ.get("WORKSHOP_HELPER_PROTOTYPE") == "1"


def chosen(args: Any) -> str | None:
    """The variant asked for on the URL, or ``None`` for the real page."""
    if not enabled():
        return None
    asked = args.get(VARIANT_PARAM)
    return asked if asked in VARIANTS else None


def stick(url: str, variant: str) -> str:
    """``url`` with the variant kept on it, so links stay inside the variant."""
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}{VARIANT_PARAM}={variant}"


def render_args(variant: str) -> dict[str, Any]:
    """Template name and extra context for one variant."""
    href: Callable[[Any, str], str] = lambda query, path: stick(
        query.href(path), variant
    )
    return {
        "template": f"prototype/variant_{variant.lower()}.html",
        "current": variant,
        "variants": VARIANTS,
        "proto_href": href,
    }
