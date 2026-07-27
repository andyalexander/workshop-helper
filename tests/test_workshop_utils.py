"""The `workshop_utils` facade — the only Host-owned name an Applet may import."""

import inspect

import pytest

import workshop_utils

BASE = "/a/thread-pitch/assets/"


def test_render_markdown_returns_html() -> None:
    html = workshop_utils.render_markdown("# Title\n\nsome *text*")
    assert "<h1>" in html
    assert "Title" in html
    assert "<em>text</em>" in html


def test_render_markdown_renders_tables() -> None:
    """A reference table is the point of most documentation Applets (§11.1)."""
    html = workshop_utils.render_markdown(
        "| Size | Pitch |\n| :--- | ---: |\n| M8 | 1.25 |\n"
    )
    assert "<table>" in html
    assert "<td" in html and "1.25" in html
    assert "text-align:right" in html


def test_render_markdown_escapes_raw_html() -> None:
    """Applet markdown is semi-trusted, so raw HTML renders inert (library-stack)."""
    html = workshop_utils.render_markdown("<script>alert('xss')</script>")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_relative_urls_are_scoped_onto_the_asset_base() -> None:
    html = workshop_utils.render_markdown(
        "[sheet](tables/iso-metric.pdf) ![form](./thread-form.svg)", asset_base=BASE
    )
    assert 'href="/a/thread-pitch/assets/tables/iso-metric.pdf"' in html
    assert 'src="/a/thread-pitch/assets/thread-form.svg"' in html


def test_scoping_preserves_alt_text() -> None:
    """The render-rule shortcut silently drops alt text; the core rule does not."""
    html = workshop_utils.render_markdown("![thread form](thread-form.svg)", BASE)
    assert 'alt="thread form"' in html


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/a.pdf",
        "mailto:someone@example.com",
        "//example.com/a.pdf",
        "/a/other/assets/x.svg",
        "#a-section",
    ],
)
def test_urls_the_host_does_not_own_are_untouched(url: str) -> None:
    html = workshop_utils.render_markdown(f"[link]({url})", asset_base=BASE)
    assert f'href="{url}"' in html


def test_relative_urls_are_left_alone_without_an_asset_base() -> None:
    html = workshop_utils.render_markdown("![form](thread-form.svg)")
    assert 'src="thread-form.svg"' in html


def test_render_markdown_signature_is_str_to_str() -> None:
    """No third-party type leaks into the facade signature (spec §7.3)."""
    sig = inspect.signature(workshop_utils.render_markdown)
    text, asset_base = sig.parameters.values()
    assert text.annotation is str
    assert asset_base.annotation == str | None
    assert sig.return_annotation is str


def test_invalid_input_carries_its_message_and_the_fields_it_names() -> None:
    """The one healthy refusal is field-targeted by construction (spec §10.2)."""
    refusal = workshop_utils.InvalidInput(
        "Too tight at this angle.", ["offset", "angle"]
    )

    assert refusal.message == "Too tight at this angle."
    assert refusal.inputs == ("offset", "angle")
    assert str(refusal) == "Too tight at this angle."


def test_facade_does_not_reexport_markdown_it() -> None:
    """The underlying library stays private, so it remains swappable (§7.3)."""
    assert not hasattr(workshop_utils, "MarkdownIt")
    assert not hasattr(workshop_utils, "markdown_it")
