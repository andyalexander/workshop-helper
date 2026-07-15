# Declarative TOML manifest owns metadata and input schema; Python is pure compute

Each Applet declares itself in a `manifest.toml` sitting next to its Python. The Manifest owns the Applet's name, type, tags, and — for calculators — the **full input schema**: each input's key, label, unit, default, and (in future) validation constraints. `applet.py` is reduced to a pure compute function.

Two reasons, both structural:

**Discovery is cheap and safe; execution is lazy.** The Host needs every Applet's name, type and tags to render its browse/search UI. If that metadata lived in Python (a decorator, a module-level dict), the only way to read it would be to import every Applet at startup — so startup cost would scale with the library, one bad import would take down the whole Host, and, critically, **listing a contributed Applet would execute its code**. A declarative Manifest lets the Host build its index by reading small text files, importing an Applet's Python only when the user actually opens it.

**Host-owned schema makes Host features generic.** Because the Host knows what the inputs are, it renders the form, validates values, and rewrites the `default` fields on "save as defaults" — for every Applet, with no Applet participating. If inputs were declared in Python, none of those could be generic.

## Considered Options

- **Python-native declaration (`@applet` decorator or module-level dict)** — rejected: one file instead of two and very ergonomic, but forces import-to-discover with all the costs above.

## Consequences

Manifests are read-write, not author-only — they are the persistence layer for defaults. For a cloned collection this means the Host writes to files git owns, so saved defaults can conflict on `git pull`; that seam is tracked separately. Python's stdlib reads TOML (`tomllib`, 3.11+) but cannot write it, so writing back requires a dependency such as `tomlkit`, which preserves comments and formatting.
