"""The one layered error surface (spec §10.3)."""

from workshop_helper.errors import error_surface


def test_the_blame_line_names_the_applet_its_root_and_its_author() -> None:
    surface = error_surface(
        name="Pipe-bender setback",
        root_name="mate-collection",
        details="no [applet] section",
        author="dave",
    )

    assert surface.blame == "Pipe-bender setback — from Root 'mate-collection', by dave"


def test_a_missing_author_falls_back_to_the_root_name() -> None:
    """`author` is free text, so provenance is the only blame left (§10.3)."""
    surface = error_surface(
        name="Thread pitch", root_name="own", details="missing content.md"
    )

    assert surface.blame == "Thread pitch — from Root 'own', by own"


def test_the_details_are_carried_verbatim() -> None:
    """Details is the full account: a reason here, a traceback for #35 (§10.3)."""
    details = 'manifest.toml is not valid TOML: Expected "=" (line 1)'
    surface = error_surface(name="Broken", root_name="own", details=details)

    assert surface.details == details
