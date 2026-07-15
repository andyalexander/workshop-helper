# Declarative TOML manifest owns metadata and input schema; Python is pure compute

Each Applet declares itself in a `manifest.toml` sitting next to its Python. The Manifest owns the Applet's name, type, tags, and — for calculators — the **full input schema**: each input's key, label, unit, default, and (in future) validation constraints. `applet.py` is reduced to a pure compute function.

Two reasons, both structural:

**Discovery is cheap and safe; execution is lazy.** The Host needs every Applet's name, type and tags to render its browse/search UI. If that metadata lived in Python (a decorator, a module-level dict), the only way to read it would be to import every Applet at startup — so startup cost would scale with the library, one bad import would take down the whole Host, and, critically, **listing a contributed Applet would execute its code**. A declarative Manifest lets the Host build its index by reading small text files, importing an Applet's Python only when the user actually opens it.

**Host-owned schema makes Host features generic.** Because the Host knows what the inputs are, it renders the form, validates values, and persists "save as defaults" — for every Applet, with no Applet participating. If inputs were declared in Python, none of those could be generic.

## Considered Options

- **Python-native declaration (`@applet` decorator or module-level dict)** — rejected: one file instead of two and very ergonomic, but forces import-to-discover with all the costs above.

## Consequences

**Superseded in part by [ADR-0007](0007-manifests-read-only-user-overrides-in-overlay.md).** This ADR originally made Manifests the persistence layer for saved defaults — read-write, not author-only. It flagged the resulting seam: for a cloned collection the Host would be writing to files git owns, so saved defaults could conflict on `git pull`. That seam turned out to be live on day one rather than on the day someone clones a collection, because the built-in Root ships inside the wheel and is replaced by `uv tool upgrade`. ADR-0007 resolves it by making Manifests **read-only to the Host** and moving user overrides into a Host-owned Overlay.

Both structural arguments above survive unchanged — the Host still reads the schema from the Manifest, and still renders, validates and saves generically. Only the destination of the write moved. ADR-0007 also retires this ADR's other consequence: since the Host no longer writes TOML, the `tomlkit` dependency it anticipated is not needed. `tomllib` (3.11+) reads TOML from the stdlib, which is all the Host requires.
