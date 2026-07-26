"""Root scanning, the index, and the discovery-time fault taxonomy.

Spec §2.5, §2.6, §2.7, §10.1, §10.4.

Discovery is **cheap and safe**: the Host builds its index by reading small text
files and **imports no Applet Python at all** (ADR-0004). If metadata lived in
Python, startup would scale with the library, one bad import would take down the
Host, and *listing* a contributed Applet would *execute* it.

Three rules do most of the work:

- A folder **with** ``manifest.toml`` is an Applet; a folder **without** one is
  not, and correctly never appears anywhere — not a card, not an error (§10.4).
- Every fault the Host can see without importing anything produces **one**
  :class:`Fault` — a greyed, un-openable card that stays searchable by folder
  name, which is the only handle left when the Manifest will not parse (§10.1).
- Roots are scanned in tier order and the first id wins, which is #8's
  ``own > built-in > foreign`` precedence. The loser is not dropped: it is
  greyed with a *"shadowed by Root 'X'"* notice (§2.7).
"""

from dataclasses import dataclass, field
from pathlib import Path

from workshop_helper.errors import ErrorSurface, error_surface
from workshop_helper.manifest import (
    DOCUMENTATION,
    MANIFEST_FILENAME,
    ManifestError,
    read_identity,
    read_manifest,
)
from workshop_helper.roots import Root

CONTENT_FILENAME = "content.md"
APPLET_MODULE_FILENAME = "applet.py"


@dataclass(frozen=True)
class Applet:
    """One indexed Applet: its identity, provenance, and declared metadata.

    ``body`` holds the ``content.md`` text of a ``documentation`` Applet and is
    ``None`` for a calculator. It is a real requirement, not a cache: #2's search
    falls back to full text over name + description + tags + content body, so the
    Host must read Applet content, not just Manifests (§2.6).
    """

    id: str
    root: Root
    path: Path
    type: str
    name: str
    description: str | None = None
    author: str | None = None
    tags: tuple[str, ...] = ()
    body: str | None = None


@dataclass(frozen=True)
class Fault:
    """One Applet folder the Host refused at scan: a greyed, un-openable card.

    ``name`` and ``author`` are whatever the Manifest yielded before the refusal
    — both ``None`` when it would not parse at all, which is exactly when the
    folder name has to carry the card (§10.1).
    """

    id: str
    root: Root
    path: Path
    reason: str
    name: str | None = None
    author: str | None = None

    @property
    def display_name(self) -> str:
        """What to title the greyed card: the declared name, else the folder."""
        return self.name or self.id

    @property
    def surface(self) -> ErrorSurface:
        """The blame line and Details this fault renders through (§10.3)."""
        return error_surface(
            name=self.display_name,
            root_name=self.root.name,
            details=self.reason,
            author=self.author,
        )

    @property
    def search_text(self) -> str:
        """What a greyed card stays findable by (§10.1).

        The folder name is the whole point: when the Manifest will not parse
        there is no name to search, and the id is the only handle left. #34 owns
        the search itself, and a loaded Applet's richer corpus (§2.6) with it —
        a Fault has nothing but this.
        """
        return "\n".join(part for part in (self.id, self.name) if part)


@dataclass(frozen=True)
class Index:
    """The Host's loaded view of every Root.

    ``faults`` are the Applets detected but refused at discovery time (greyed
    cards, §10.1); ``skipped_roots`` counts Root paths that were not there.
    """

    applets: list[Applet] = field(default_factory=list)
    faults: list[Fault] = field(default_factory=list)
    skipped_roots: int = 0

    @property
    def failed(self) -> int:
        """The `M failed` of the startup summary: one per greyed card."""
        return len(self.faults)

    def applet(self, applet_id: str) -> Applet | None:
        """Look an Applet up by id, or ``None`` when nothing owns that id.

        Faults are deliberately not reachable here: a greyed card is
        un-openable, so no route can resolve one into something to render.
        """
        return next((a for a in self.applets if a.id == applet_id), None)

    def summary_line(self) -> str:
        """The one-line console summary emitted at startup (spec §2.3 step 5)."""
        line = f"Loaded {len(self.applets)} Applets; {self.failed} failed."
        if self.skipped_roots:
            plural = "Root" if self.skipped_roots == 1 else "Roots"
            line += f" {self.skipped_roots} {plural} skipped."
        return line


def build_index(roots: list[Root]) -> Index:
    """Scan ``roots`` in tier order and build the index."""
    applets: list[Applet] = []
    faults: list[Fault] = []
    claimed: dict[str, Root] = {}
    skipped_roots = 0

    for root in roots:
        folders = _applet_folders(root)
        if folders is None:
            skipped_roots += 1
            continue
        for folder in folders:
            winner = claimed.get(folder.name)
            if winner is not None:
                faults.append(_shadowed(folder, root, winner))
                continue
            # The id is claimed by the folder, before the Manifest is read: a
            # *broken* higher-tier Applet still wins. Otherwise a foreign Root
            # could capture a built-in id by shipping a broken twin of its name,
            # which is the collision §2.7 exists to close.
            claimed[folder.name] = root
            found = _read_applet(folder, root)
            if isinstance(found, Fault):
                faults.append(found)
            else:
                applets.append(found)

    return Index(applets=applets, faults=faults, skipped_roots=skipped_roots)


def _applet_folders(root: Root) -> list[Path] | None:
    """Every Applet folder in ``root``, or ``None`` if the Root is unreadable.

    A missing or unreadable Root path is not an error; it is skipped and counted
    (§2.5). Folders are flat within a Root (ADR-0003), so this never recurses.
    """
    try:
        entries = sorted(root.path.iterdir())
    except OSError:
        return None
    return [
        entry
        for entry in entries
        if entry.is_dir() and (entry / MANIFEST_FILENAME).is_file()
    ]


def _read_applet(folder: Path, root: Root) -> Applet | Fault:
    """Index one Applet folder, or say why it cannot be indexed."""
    try:
        manifest = read_manifest(folder / MANIFEST_FILENAME)
    except ManifestError as error:
        return _fault(folder, root, str(error))

    body = None
    if manifest.type == DOCUMENTATION:
        body = _read_text(folder / CONTENT_FILENAME)
        if body is None:
            return _fault(folder, root, f"missing {CONTENT_FILENAME}")
    elif not (folder / APPLET_MODULE_FILENAME).is_file():
        # A calculator must define compute() somewhere (§3.2) — and the Host can
        # see the file is absent without importing it.
        return _fault(folder, root, f"missing {APPLET_MODULE_FILENAME}")

    return Applet(
        id=folder.name,
        root=root,
        path=folder,
        type=manifest.type,
        name=manifest.name,
        description=manifest.description,
        author=manifest.author,
        tags=manifest.tags,
        body=body,
    )


def _shadowed(folder: Path, root: Root, winner: Root) -> Fault:
    """Grey a lower-tier twin, naming the Root that beat it (§2.7).

    Shadowing is reported whatever else is wrong with the folder: it will never
    be opened, so its own faults are moot and stacking them would only bury the
    one thing the reader can act on.
    """
    return _fault(folder, root, f"shadowed by Root '{winner.name}'")


def _fault(folder: Path, root: Root, reason: str) -> Fault:
    """Build a fault, blaming whoever the Manifest still says to blame (§10.3).

    The identity is re-read rather than salvaged from validation, because most
    faults arrive *as* a failure to validate and there is no half-built Manifest
    to take a name off. Re-reading one small TOML file on the fault path costs
    nothing and keeps every path here identical.
    """
    name, author = read_identity(folder / MANIFEST_FILENAME)
    return Fault(
        id=folder.name,
        root=root,
        path=folder,
        reason=reason,
        name=name,
        author=author,
    )


def _read_text(path: Path) -> str | None:
    """Read a small text file, or ``None`` when it is missing or unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
