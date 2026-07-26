"""Markdown rendering, kept behind the no-leak facade (spec §7.3).

``markdown_it`` is imported here and nowhere an Applet can reach it by importing
``workshop_utils``. The public surface is ``str -> str`` so the library stays
swappable.
"""

from markdown_it import MarkdownIt

_RENDERER = MarkdownIt()


def render_markdown(text: str) -> str:
    """Render Markdown ``text`` to an HTML fragment."""
    return _RENDERER.render(text)
