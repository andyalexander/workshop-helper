"""The only Host-owned name an Applet may import (spec §7.1).

A no-leak facade: no third-party type appears in any signature, return value, or
exception. ``Result`` and ``InvalidInput`` arrive with their consumers (tickets
#35, #36); ``render_markdown`` is the first member.
"""

from workshop_utils._markdown import render_markdown

__all__ = ["render_markdown"]
