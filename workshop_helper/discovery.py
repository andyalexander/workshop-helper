"""Root scanning and the index (spec §2.5, §2.6).

Discovery is **cheap and safe**: the Host builds its index by reading small text
files and **imports no Applet Python at all** (ADR-0004). If metadata lived in
Python, startup would scale with the library, one bad import would take down the
Host, and *listing* a contributed Applet would *execute* it.

Two rules do most of the work:

- A folder **with** ``manifest.toml`` is an Applet; a folder **without** one is
  not, and correctly never appears anywhere — not a card, not an error (§10.4).
- Roots are scanned in tier order and the first id wins, which is #8's
  ``own > built-in > foreign`` precedence. The loser is dropped here; greying it
  with a *"shadowed by Root 'X'"* notice is #33's job (§2.7).
"""

from dataclasses import dataclass, field
from pathlib import Path

from workshop_helper.manifest import MANIFEST_FILENAME, ManifestError, read_manifest
from workshop_helper.roots import Root

CONTENT_FILENAME = "content.md"
APPLET_MODULE_FILENAME = "applet.py"
DOCUMENTATION = "documentation"


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
class Index:
    """The Host's loaded view of every Root.

    ``failed`` counts Applets detected but rejected at discovery time (greyed
    cards, §10.1); ``skipped_roots`` counts Root paths that were not there.
    """

    applets: list[Applet] = field(default_factory=list)
    failed: int = 0
    skipped_roots: int = 0

    def applet(self, applet_id: str) -> Applet | None:
        """Look an Applet up by id, or ``None`` when nothing owns that id."""
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
    claimed: set[str] = set()
    failed = 0
    skipped_roots = 0

    for root in roots:
        folders = _applet_folders(root)
        if folders is None:
            skipped_roots += 1
            continue
        for folder in folders:
            if folder.name in claimed:
                continue  # shadowed by a higher tier (§2.7) — #33 greys it.
            applet = _read_applet(folder, root)
            if applet is None:
                failed += 1
                continue
            claimed.add(applet.id)
            applets.append(applet)

    return Index(applets=applets, failed=failed, skipped_roots=skipped_roots)


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


def _read_applet(folder: Path, root: Root) -> Applet | None:
    """Index one Applet folder, or ``None`` on any discovery-time fault."""
    try:
        manifest = read_manifest(folder / MANIFEST_FILENAME)
    except ManifestError:
        return None

    body = None
    if manifest.type == DOCUMENTATION:
        body = _read_text(folder / CONTENT_FILENAME)
        if body is None:
            return None  # missing content.md is a discovery fault (§3.1)
    elif not (folder / APPLET_MODULE_FILENAME).is_file():
        return None  # a calculator must define compute() somewhere (§3.2)

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


def _read_text(path: Path) -> str | None:
    """Read a small text file, or ``None`` when it is missing or unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
