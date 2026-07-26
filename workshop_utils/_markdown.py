"""Markdown rendering, kept behind the no-leak facade (spec §7.3).

``markdown_it`` is imported here and nowhere an Applet can reach it by importing
``workshop_utils``. The public surface is ``str -> str`` so the library stays
swappable.

Configuration follows `docs/research/library-stack.md`'s recommendation verbatim,
including its two recorded traps:

- ``MarkdownIt("commonmark").enable("table")``, **never** the ``gfm-like`` preset
  — that one enables ``linkify`` and raises at render time unless
  ``linkify-it-py`` is installed too.
- Relative links and images are scoped onto the Applet's asset mount with a
  **core rule over the token stream**, not by overriding the ``image`` render
  rule, which silently drops alt text.

``{"html": False}`` escapes raw HTML in Applet markdown. Applets are
user-installed and semi-trusted; the explicit lever is worth having, and an
Applet that genuinely needs markup has the Result's ``html`` channel (§1.3).
"""

from urllib.parse import urljoin, urlparse

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore

ASSET_BASE_KEY = "asset_base"
# Which attribute carries a URL, per inline token type.
_URL_ATTRS = {"link_open": "href", "image": "src"}


def _is_relative(url: str) -> bool:
    """Whether ``url`` points inside the Applet's own folder.

    Absolute paths, external URLs (any scheme), protocol-relative URLs and
    same-page fragments all address something the Host does not own, and are
    left exactly as the author wrote them.
    """
    if not url or url.startswith(("/", "#")):
        return False
    parsed = urlparse(url)
    return not parsed.scheme and not parsed.netloc


def _scope_assets(state: StateCore) -> None:
    """Rewrite relative URLs onto the asset base carried in ``env``."""
    base = state.env.get(ASSET_BASE_KEY)
    if not base:
        return
    for token in state.tokens:
        for child in token.children or []:
            attr = _URL_ATTRS.get(child.type)
            if attr is None:
                continue
            url = child.attrGet(attr)
            if isinstance(url, str) and _is_relative(url):
                child.attrSet(attr, urljoin(base, url))


_RENDERER = MarkdownIt("commonmark", {"html": False}).enable("table")
_RENDERER.core.ruler.push("scope_assets", _scope_assets)


def render_markdown(text: str, asset_base: str | None = None) -> str:
    """Render Markdown ``text`` to an HTML fragment.

    ``asset_base`` is the URL prefix the caller serves the document's own folder
    from. When given, relative links and images are resolved against it, so an
    author writes ``![](thread-form.svg)`` and never needs to know the mount
    point. External and absolute URLs are untouched.
    """
    return _RENDERER.render(text, {ASSET_BASE_KEY: asset_base})
