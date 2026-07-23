"""The `workshop_utils` facade — the only Host-owned name an Applet may import."""

import inspect

import workshop_utils


def test_render_markdown_returns_html() -> None:
    html = workshop_utils.render_markdown("# Title\n\nsome *text*")
    assert "<h1>" in html
    assert "Title" in html
    assert "<em>text</em>" in html


def test_render_markdown_signature_is_str_to_str() -> None:
    """No third-party type leaks into the facade signature (spec §7.3)."""
    sig = inspect.signature(workshop_utils.render_markdown)
    (param,) = sig.parameters.values()
    assert param.annotation is str
    assert sig.return_annotation is str


def test_facade_does_not_reexport_markdown_it() -> None:
    """The underlying library stays private, so it remains swappable (§7.3)."""
    assert not hasattr(workshop_utils, "MarkdownIt")
    assert not hasattr(workshop_utils, "markdown_it")
