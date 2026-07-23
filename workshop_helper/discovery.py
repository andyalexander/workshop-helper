"""Root scanning and the index (spec §2.5, §2.6).

Discovery is cheap and safe: the Host builds its index by reading small text
files and imports no Applet Python at all (ADR-0004). The walking skeleton loads
no Applets yet — Manifest parsing arrives with #32 — but the index shape and the
"missing Root is not an error" rule are established here.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Index:
    """The Host's loaded view of every Root.

    ``applets`` holds the successfully indexed Applets; ``failed`` counts those
    detected but rejected at discovery time (greyed cards, spec §10.1).
    """

    applets: list = field(default_factory=list)
    failed: int = 0

    def summary_line(self) -> str:
        """The one-line console summary emitted at startup (spec §2.3)."""
        return f"Loaded {len(self.applets)} Applets; {self.failed} failed."


def build_index(roots: list[Path]) -> Index:
    """Scan ``roots`` in order and build the index.

    Missing or unreadable Root paths are skipped, not raised (spec §2.5). Applet
    parsing is deferred to #32, so the skeleton yields an empty index regardless.
    """
    return Index(applets=[], failed=0)
