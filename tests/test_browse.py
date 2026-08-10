"""The facet sidebar, its token input, and the search fallback (spec §9)."""

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import client_for

from workshop_helper.browse import (
    Query,
    matches,
    promote,
    read_query,
    results,
    search_text,
    sidebar,
    tag_candidates,
    vocabulary,
)
from workshop_helper.discovery import Applet, Fault, Index
from workshop_helper.manifest import Output
from workshop_helper.roots import Root

BUILTIN = Root(name="built-in", path=Path("/builtin"))
OWN = Root(name="own", path=Path("/own"))


@pytest.fixture(autouse=True)
def _clean_modules() -> Iterator[None]:
    """One test here runs an Applet; no imported Applet may outlive its test."""
    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        del sys.modules[name]


def _applet(
    applet_id: str,
    *,
    root: Root = BUILTIN,
    name: str = "",
    description: str | None = None,
    tags: tuple[str, ...] = (),
    body: str | None = None,
) -> Applet:
    return Applet(
        id=applet_id,
        root=root,
        path=root.path / applet_id,
        type="documentation" if body is not None else "calculator",
        name=name or applet_id,
        description=description,
        tags=tags,
        body=body,
    )


def _library() -> Index:
    return Index(
        applets=[
            _applet("thread-pitch", name="Thread pitch", tags=("thread", "metric")),
            _applet("bsp", name="BSP sizes", tags=("thread", "imperial")),
            _applet(
                "pipe-bender", name="Pipe-bender", tags=("copper", "metric"), root=OWN
            ),
        ]
    )


# The token input: prefix beats substring (§9).


def test_prefix_matches_rank_above_substring_matches() -> None:
    vocab = ("thread", "reading", "imperial")

    assert tag_candidates(vocab, "read") == ("reading", "thread")


def test_typed_text_promotes_to_the_tag_it_prefixes() -> None:
    assert promote("imp", ("copper", "imperial", "metric")) == "imperial"


def test_typed_text_matching_no_tag_promotes_nothing() -> None:
    assert promote("setback", ("copper", "imperial")) is None


def test_blank_text_promotes_nothing() -> None:
    assert promote("  ", ("copper",)) is None


def test_the_vocabulary_is_one_flat_pool_across_roots() -> None:
    assert vocabulary(_library().applets) == (
        "copper",
        "imperial",
        "metric",
        "thread",
    )


# Facets AND, and Root ANDs with them (§9, #11).


def test_tag_facets_and_together() -> None:
    library = _library()

    both = results(library, Query(tags=("thread", "imperial")))

    assert [a.id for a in both.applets] == ["bsp"]


def test_root_is_a_single_valued_facet_that_ands_with_tags() -> None:
    library = _library()

    assert [a.id for a in results(library, Query(root="own")).applets] == [
        "pipe-bender"
    ]
    assert results(library, Query(tags=("thread",), root="own")).applets == []


def test_choosing_a_second_root_replaces_the_first() -> None:
    assert Query(root="own").with_root("built-in").root == "built-in"


# The search fallback: full text over name + description + tags + body (§2.6).


def test_search_text_spans_name_description_tags_and_the_content_body() -> None:
    applet = _applet(
        "thread-pitch",
        name="Thread pitch",
        description="Pitch and tap-drill reference.",
        tags=("fastener",),
        body="M8 coarse is 1.25mm.",
    )

    corpus = search_text(applet)

    assert "Thread pitch" in corpus
    assert "tap-drill" in corpus
    assert "fastener" in corpus
    assert "1.25mm" in corpus


def test_unmatched_text_searches_the_content_body() -> None:
    library = Index(applets=[_applet("thread-pitch", body="M8 coarse is 1.25mm.")])

    assert matches(library.applets[0], Query(text="coarse"))
    assert not matches(library.applets[0], Query(text="brass"))


def test_text_search_ignores_case() -> None:
    assert matches(_applet("bsp", name="BSP sizes"), Query(text="bsp sizes"))


# Faults stay findable by folder name, but carry no tags (§10.1).


def test_a_fault_is_searchable_by_folder_name() -> None:
    fault = Fault(id="broken-thing", root=BUILTIN, path=BUILTIN.path, reason="boom")
    library = Index(faults=[fault])

    assert results(library, Query(text="broken")).faults == [fault]


def test_a_tag_chip_excludes_every_fault() -> None:
    fault = Fault(id="broken-thing", root=BUILTIN, path=BUILTIN.path, reason="boom")

    assert results(Index(faults=[fault]), Query(tags=("thread",))).faults == []


# The guard rail: what each candidate would leave, before you commit (§9).


def test_each_candidate_previews_what_it_would_leave() -> None:
    view = sidebar(_library(), Query())

    leaves = {candidate.label: candidate.leaves for candidate in view.tags}
    assert leaves == {"copper": 1, "imperial": 1, "metric": 2, "thread": 2}


def test_a_candidate_that_would_leave_nothing_says_so_before_it_is_picked() -> None:
    view = sidebar(_library(), Query(tags=("thread",)))

    dead = next(candidate for candidate in view.tags if candidate.label == "copper")
    assert dead.leaves == 0
    assert dead.dead


def test_every_row_counts_the_query_its_own_link_leads_to() -> None:
    """A placed chip's row *removes* it, so its count is what removing leaves."""
    view = sidebar(_library(), Query(tags=("thread",)))

    chosen = next(candidate for candidate in view.tags if candidate.label == "thread")
    assert chosen.selected
    assert chosen.query.tags == ()
    assert chosen.leaves == 3


def test_a_root_facet_carries_the_same_guard_rail_as_a_tag() -> None:
    view = sidebar(_library(), Query(tags=("imperial",)))

    own = next(root for root in view.roots if root.label == "own")
    assert own.dead


def test_the_typed_token_previews_what_enter_would_leave() -> None:
    view = sidebar(_library(), Query(), typed="imp")

    assert view.top is not None
    assert view.top.label == "imperial"
    assert view.top.leaves == 1
    # Typing narrows the list to the candidates, ranked prefix-first.
    assert [candidate.label for candidate in view.tags] == ["imperial"]


def test_the_typed_token_says_when_enter_would_leave_nothing() -> None:
    view = sidebar(_library(), Query(tags=("thread",)), typed="cop")

    assert view.top is not None
    assert view.top.dead


def test_text_that_matches_no_tag_leaves_the_whole_vocabulary_showing() -> None:
    view = sidebar(_library(), Query(), typed="brass")

    assert view.top is None
    assert len(view.tags) == 4


def test_a_dead_end_no_single_step_recovers_from_clears_the_filter() -> None:
    # Every single undo is still a dead end: thread+brass, copper+brass and
    # thread+copper all leave nothing.
    view = sidebar(_library(), Query(tags=("thread", "copper"), text="brass"))

    assert view.recovery is not None
    assert view.recovery.drops == ""
    assert view.recovery.query == Query()


def test_a_step_whose_undo_is_still_a_dead_end_is_skipped() -> None:
    view = sidebar(_library(), Query(tags=("copper",), text="brass"))

    assert view.recovery is not None
    assert view.recovery.drops == "brass"


def test_a_dead_end_recovers_by_dropping_the_last_chip() -> None:
    view = sidebar(_library(), Query(tags=("thread", "copper")))

    assert view.count == 0
    assert view.recovery is not None
    assert view.recovery.drops == "copper"
    assert view.recovery.query.tags == ("thread",)


def test_a_dead_end_with_no_chips_recovers_by_dropping_the_search() -> None:
    view = sidebar(_library(), Query(text="brass"))

    assert view.recovery is not None
    assert view.recovery.drops == "brass"
    assert view.recovery.query == Query()


def test_a_live_result_set_offers_no_recovery() -> None:
    assert sidebar(_library(), Query(tags=("thread",))).recovery is None


# Own-Root tags carry a display-only marker; filtering stays global (#11).


def test_a_tag_used_in_the_own_root_is_marked() -> None:
    view = sidebar(_library(), Query())

    marked = {candidate.label for candidate in view.tags if candidate.own}
    assert marked == {"copper", "metric"}


def test_the_marker_does_not_narrow_what_a_tag_filters() -> None:
    library = _library()

    metric = results(library, Query(tags=("metric",)))

    assert [a.id for a in metric.applets] == ["thread-pitch", "pipe-bender"]


# The query is the URL: that is what makes the sidebar persist (§9).


def test_a_query_round_trips_through_its_own_query_string() -> None:
    query = Query(tags=("thread", "imperial"), root="own", text="brass")

    assert query.query_string == "?tag=thread&tag=imperial&root=own&q=brass"


def test_an_empty_query_has_no_query_string() -> None:
    assert Query().query_string == ""


def test_dropping_a_chip_leaves_the_rest_of_the_query_alone() -> None:
    query = Query(tags=("thread", "copper"), root="own")

    assert query.without_tag("thread") == Query(tags=("copper",), root="own")


# The routes.


def test_the_token_input_promotes_typed_text_to_a_chip() -> None:
    response = client_for(_library()).get("/?q=imp")

    assert response.status_code == 302
    assert response.headers["Location"] == "/?tag=imperial"


def test_promotion_keeps_the_chips_already_placed() -> None:
    response = client_for(_library()).get("/?tag=thread&q=imp")

    assert response.headers["Location"] == "/?tag=thread&tag=imperial"


def test_promoting_a_tag_already_chipped_only_clears_the_box() -> None:
    response = client_for(_library()).get("/?tag=thread&q=thread")

    assert response.headers["Location"] == "/?tag=thread"


def test_unmatched_text_is_kept_and_searched() -> None:
    body = client_for(_library()).get("/?q=BSP").get_data(as_text=True)

    assert "BSP sizes" in body
    assert "Thread pitch" not in body


def test_the_browse_page_filters_to_the_chips_in_the_url() -> None:
    body = (
        client_for(_library()).get("/?tag=thread&tag=imperial").get_data(as_text=True)
    )

    assert "BSP sizes" in body
    assert "Pipe-bender" not in body


def test_a_dead_end_offers_its_recovery_link() -> None:
    body = client_for(_library()).get("/?tag=thread&tag=copper").get_data(as_text=True)

    assert 'href="/?tag=thread"' in body
    assert "copper" in body


def test_a_filter_offers_one_way_out_of_all_of_it() -> None:
    """Chips only cover tags, so the way out is keyed off the whole query (§9)."""
    client = client_for(_library())

    for filtered in ("/?tag=thread", "/?q=brass", "/?root=own"):
        body = client.get(filtered).get_data(as_text=True)
        assert 'class="clear" href="/"' in body, filtered


def test_nothing_filtered_offers_nothing_to_clear() -> None:
    """Never a dead control: with no filter on there is nothing to undo."""
    body = client_for(_library()).get("/").get_data(as_text=True)

    assert 'class="clear"' not in body


def test_the_live_preview_answers_with_the_facet_lists_alone() -> None:
    """htmx swaps this block while you type; the page renders it in place (§9)."""
    body = client_for(_library()).get("/facets?tag=thread&q=imp").get_data(as_text=True)

    assert body.lstrip().startswith('<div id="facets"')
    assert "<aside" not in body
    assert "imperial" in body


def test_the_own_root_marker_renders_as_a_badge_and_not_as_colour_alone() -> None:
    body = client_for(_library()).get("/").get_data(as_text=True)

    facets = body.split('class="facets"')[1]
    assert '<span class="own"' in facets


def test_the_root_facets_render_as_links_that_and_with_the_chips() -> None:
    body = client_for(_library()).get("/?tag=metric").get_data(as_text=True)

    assert 'href="/?tag=metric&amp;root=own"' in body


def test_the_sidebar_persists_on_the_applet_page() -> None:
    index = Index(
        applets=[
            _applet("thread-pitch", name="Thread pitch", tags=("thread",), body="M8")
        ]
    )

    body = client_for(index).get("/a/thread-pitch?tag=thread").get_data(as_text=True)

    # The chip is still placed, and the crumb goes back to the *filtered* list.
    assert 'class="chip" href="/"' in body
    assert 'href="/?tag=thread"' in body


def test_a_no_javascript_compute_comes_back_with_the_filter_still_on(
    tmp_path: Path,
) -> None:
    """`keep` is what carries the sidebar through a plain form POST (§9)."""
    folder = tmp_path / "doubler"
    folder.mkdir()
    (folder / "applet.py").write_text(
        "from workshop_utils import Result\n\n\n"
        "def compute(inputs):\n"
        "    return Result(outputs={'answer': 2})\n"
    )
    applet = Applet(
        id="doubler",
        root=BUILTIN,
        path=folder,
        type="calculator",
        name="Doubler",
        tags=("thread",),
        outputs=(Output(name="answer", label="Answer", primary=True),),
    )
    client = client_for(Index(applets=[applet]))

    page = client.get("/a/doubler?tag=thread").get_data(as_text=True)
    assert 'action="/a/doubler/compute?tag=thread"' in page

    answered = client.post("/a/doubler/compute?tag=thread").get_data(as_text=True)
    assert 'class="chip" href="/"' in answered


def test_read_query_takes_repeated_tag_parameters() -> None:
    app = client_for(_library()).application
    with app.test_request_context("/?tag=thread&tag=copper&root=own&q=brass"):
        from flask import request

        assert read_query(request.args) == Query(
            tags=("thread", "copper"), root="own", text="brass"
        )
