"""The facet sidebar, its token input, and the search fallback (spec §9).

The filter is a **token input over the tag vocabulary, not a text box**: type a
prefix, press ↵, and the text becomes a chip (`imp` → `imperial`). Here that is a
plain GET submit the Host answers with a redirect, so **the URL is the filter
state** — which is what makes the sidebar persist onto the Applet page (§9) with
no session, no JavaScript, and a back button that does the obvious thing.

Two rules carry the semantics:

- **Prefix beats substring.** `read` offers `reading` before `thread`, because
  the token input is something you *type through*, and what you have typed so far
  is the start of the word you mean.
- **Facets AND, with the leaves-nothing guard rail.** Every candidate carries the
  count it would leave *before* it is picked, and a dead end names the one chip to
  drop. That guard rail is load-bearing: ADR-0003 leaves no hierarchy to fall back
  on, so an empty result set has no natural "go up a level".

Everything in this module is a pure function of the index and the query. The
routes read the query off the URL, and the templates render what comes back.
"""

from dataclasses import dataclass, replace
from urllib.parse import urlencode

from werkzeug.datastructures import MultiDict

from workshop_helper.discovery import Applet, Fault, Index
from workshop_helper.roots import OWN_ROOT_NAME, Root

TAG_PARAM = "tag"
ROOT_PARAM = "root"
TEXT_PARAM = "q"


@dataclass(frozen=True)
class Query:
    """What the user is filtering by, as it rides in the URL.

    ``root`` is single-valued (#11): provenance is single-valued, which is the
    textbook case for a facet, and it AND-combines with the tag chips through the
    same machinery. ``text`` is only ever text that matched **no** tag — anything
    that did was promoted to a chip before it got here.
    """

    tags: tuple[str, ...] = ()
    root: str = ""
    text: str = ""

    @property
    def is_empty(self) -> bool:
        """Nothing is being filtered — the library as it stands."""
        return not (self.tags or self.root or self.text)

    @property
    def query_string(self) -> str:
        """The URL tail this query travels in — ``""`` when nothing is filtered."""
        params: list[tuple[str, str]] = [(TAG_PARAM, tag) for tag in self.tags]
        if self.root:
            params.append((ROOT_PARAM, self.root))
        if self.text:
            params.append((TEXT_PARAM, self.text))
        return f"?{urlencode(params)}" if params else ""

    def href(self, path: str) -> str:
        """``path`` with this query hung off it, for a link that keeps the filter."""
        return f"{path}{self.query_string}"

    def with_tag(self, tag: str) -> "Query":
        """Add a chip, or return this query unchanged when it is already on."""
        if tag in self.tags:
            return self
        return replace(self, tags=self.tags + (tag,))

    def without_tag(self, tag: str) -> "Query":
        """Drop one chip, leaving every other part of the filter alone."""
        return replace(self, tags=tuple(t for t in self.tags if t != tag))

    def toggled(self, tag: str) -> "Query":
        """What clicking a tag facet does: on becomes off, off becomes on."""
        return self.without_tag(tag) if tag in self.tags else self.with_tag(tag)

    def with_root(self, root: str) -> "Query":
        """Choose a Root. Single-valued, so a second choice replaces the first."""
        return replace(self, root=root)

    def toggled_root(self, root: str) -> "Query":
        """What clicking a Root facet does; clicking the chosen one clears it."""
        return self.with_root("" if root == self.root else root)

    def without_text(self) -> "Query":
        """Drop the search, keeping the chips — what ↵ does once text is a chip."""
        return replace(self, text="")


@dataclass(frozen=True)
class Results:
    """What the current query leaves: cards, and greyed cards (§10.1)."""

    applets: list[Applet]
    faults: list[Fault]

    @property
    def count(self) -> int:
        """How many cards are on screen. A greyed card is a card (§10.1)."""
        return len(self.applets) + len(self.faults)


@dataclass(frozen=True)
class Facet:
    """One row of the facet list — a tag, or a Root (#11).

    ``leaves`` is what **this row's own link** leaves: picking it up when it is
    off, putting it down when it is on. One rule for every row, so the number can
    never describe a different destination from the click that carries it (§9).

    ``own`` marks a tag carried by an Applet in the user's own Root — a badge in
    the sidebar, **display-only**: the tag still filters foreign Applets exactly
    as it always did, because the pool is global and flat (#11, §4.2).
    """

    label: str
    leaves: int
    selected: bool
    query: Query
    own: bool = False

    @property
    def dead(self) -> bool:
        """Picking this would leave nothing — said before it is picked (§9)."""
        return self.leaves == 0 and not self.selected


@dataclass(frozen=True)
class Chip:
    """A placed tag, and the query that drops it."""

    tag: str
    query: Query


@dataclass(frozen=True)
class Recovery:
    """The one click out of a dead end: what it drops, and where it lands.

    ``drops`` is empty when nothing short of clearing the whole filter gets back
    to something — the link then says so rather than naming one part of it.
    """

    query: Query
    drops: str = ""


@dataclass(frozen=True)
class Sidebar:
    """Everything the sidebar renders, for one query over one index.

    ``top`` is the candidate ↵ would place — the token input's preview, and the
    only place the prefix-beats-substring ranking is visible to the user.
    """

    query: Query
    chips: tuple[Chip, ...]
    tags: tuple[Facet, ...]
    roots: tuple[Facet, ...]
    count: int
    total: int
    typed: str = ""
    top: Facet | None = None
    recovery: Recovery | None = None


def read_query(args: MultiDict[str, str]) -> Query:
    """Read the filter off the request's query string.

    A repeated tag is one chip, in the order the chips were placed — which is
    what lets the dead-end recovery drop *the last thing the user did*.
    """
    tags = tuple(dict.fromkeys(tag for tag in args.getlist(TAG_PARAM) if tag))
    return Query(
        tags=tags,
        root=(args.get(ROOT_PARAM) or "").strip(),
        text=(args.get(TEXT_PARAM) or "").strip(),
    )


def vocabulary(applets: list[Applet]) -> tuple[str, ...]:
    """Every tag in play, sorted — one global flat pool across Roots (§4.2)."""
    return tuple(sorted({tag for applet in applets for tag in applet.tags}))


def own_tags(applets: list[Applet]) -> frozenset[str]:
    """The tags carried by the user's own Applets, for the inline marker (#11)."""
    return frozenset(
        tag
        for applet in applets
        if applet.root.name == OWN_ROOT_NAME
        for tag in applet.tags
    )


def tag_candidates(vocab: tuple[str, ...], typed: str) -> tuple[str, ...]:
    """The tags ``typed`` offers, **prefix first, substring after**.

    A token input is typed *through*: what is in the box is the start of the word
    the user means, so `imp` must offer `imperial` ahead of anything that merely
    contains it. Beyond this there is no matching cleverness — stemming and
    synonyms are semantics, and §4.2 rules them out.
    """
    needle = typed.strip().lower()
    if not needle:
        return ()
    prefix = tuple(tag for tag in vocab if tag.startswith(needle))
    substring = tuple(
        tag for tag in vocab if needle in tag and not tag.startswith(needle)
    )
    return prefix + substring


def promote(typed: str, vocab: tuple[str, ...]) -> str | None:
    """The tag ``typed`` becomes on ↵, or ``None`` when it matches no tag.

    ``None`` is the fallback branch, not a failure: unmatched text stays in the
    box and searches full text instead, so one control does both jobs (§9).
    """
    candidates = tag_candidates(vocab, typed)
    return candidates[0] if candidates else None


def search_text(applet: Applet) -> str:
    """The corpus an unmatched search runs over (§2.6).

    Name + description + tags + the ``content.md`` body. The body is why the index
    reads Applet content and not just Manifests — searching for a figure that only
    appears inside a documentation page has to find it.
    """
    parts = (
        applet.name,
        applet.description or "",
        " ".join(applet.tags),
        applet.body or "",
    )
    return "\n".join(part for part in parts if part)


def matches(applet: Applet, query: Query) -> bool:
    """Does ``applet`` survive the filter? Facets AND; text is the fallback."""
    if not all(tag in applet.tags for tag in query.tags):
        return False
    return _card_matches(query, applet.root, search_text(applet))


def fault_matches(fault: Fault, query: Query) -> bool:
    """A greyed card filters by what it still has: its Root and its name.

    A Fault carries no tags — the Manifest that would have declared them is the
    thing that was refused — so any chip at all excludes it. That is honest rather
    than lossy: with a tag chip on, the user is asking about a vocabulary a Fault
    was never able to join.
    """
    if query.tags:
        return False
    return _card_matches(query, fault.root, fault.search_text)


def _card_matches(query: Query, root: Root, corpus: str) -> bool:
    """The half of the filter every card answers alike: its Root, then text.

    Only the tag rule differs between an Applet and a Fault, so only the tag rule
    lives above this.
    """
    if query.root and root.name != query.root:
        return False
    return not query.text or query.text.lower() in corpus.lower()


def results(index: Index, query: Query) -> Results:
    """Everything ``query`` leaves, cards and greyed cards alike."""
    return Results(
        applets=[applet for applet in index.applets if matches(applet, query)],
        faults=[fault for fault in index.faults if fault_matches(fault, query)],
    )


def sidebar(index: Index, query: Query, typed: str = "") -> Sidebar:
    """Build the whole sidebar: chips, facets, the ↵ preview, and the way out.

    ``typed`` is what is in the box *now* — a half-written token, which narrows
    and ranks the candidates and picks ``top``. It is deliberately **not** part of
    ``query``: the counts must preview what the chip would leave, not what the
    half-written word matches as text.
    """
    left = results(index, query)
    marked = own_tags(index.applets)
    vocab = vocabulary(index.applets)
    narrowed = tag_candidates(vocab, typed)
    tags = tuple(
        _facet(index, query.toggled(tag), tag, tag in query.tags, tag in marked)
        for tag in (narrowed or vocab)
    )
    roots = tuple(
        _facet(index, query.toggled_root(root.name), root.name, root.name == query.root)
        for root in _roots(index)
    )
    return Sidebar(
        query=query,
        chips=tuple(Chip(tag=tag, query=query.without_tag(tag)) for tag in query.tags),
        tags=tags,
        roots=roots,
        count=left.count,
        total=len(index.applets) + len(index.faults),
        typed=typed,
        top=tags[0] if narrowed else None,
        recovery=_recovery(index, query) if left.count == 0 else None,
    )


def _facet(
    index: Index, target: Query, label: str, selected: bool, own: bool = False
) -> Facet:
    """One row, counted against ``target`` — the query its own link leads to."""
    return Facet(
        label=label,
        leaves=results(index, target).count,
        selected=selected,
        query=target,
        own=own,
    )


def _roots(index: Index) -> list[Root]:
    """The Roots that put something on screen, in the order they were scanned."""
    seen: dict[str, Root] = {}
    for card in (*index.applets, *index.faults):
        seen.setdefault(card.root.name, card.root)
    return list(seen.values())


def _recovery(index: Index, query: Query) -> Recovery | None:
    """The single click out of a dead end (§9).

    The **last** thing added is the first thing offered: it is what the user just
    did, and undoing the most recent step is the recovery that needs no
    explaining. But the promise is *one* click, so a step whose undo is still a
    dead end is skipped, and if nothing on its own is enough the whole filter goes
    — clearing it always works, which is what makes the guard rail a guarantee.
    """
    steps = [
        *((tag, query.without_tag(tag)) for tag in reversed(query.tags)),
        *([(query.text, query.without_text())] if query.text else []),
        *([(query.root, query.with_root(""))] if query.root else []),
    ]
    for drops, target in steps:
        if results(index, target).count:
            return Recovery(query=target, drops=drops)
    return Recovery(query=Query()) if steps else None
