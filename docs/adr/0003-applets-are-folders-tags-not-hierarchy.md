# Applets are folders in multiple flat roots; categorisation is tags, not hierarchy

An Applet is a folder, and the Host discovers Applets by scanning a set of roots (built-in, the user's own, and any cloned collections) PATH-style. Folders are **flat within each root**, and no category ever appears in a path.

The reasoning: a filesystem path is single-valued (a folder lives in exactly one place), but categorisation is multi-valued — a pipe-bender calculator is legitimately "metalwork" and "measurement" and "pipe" at once. Any hierarchy forces a contributor to nominate one facet as the "real" one, re-litigating an unanswerable question on every addition. So the filesystem carries only what is genuinely single-valued:

- **Identity** — the folder name is the Applet's id.
- **Provenance** — the root an Applet came from; an Applet has exactly one source.
- **Categorisation** — entirely tags in the Manifest, never a directory.

## Considered Options

- **Category hierarchy on disk** — rejected for the reason above.
- **Python entry points / pip-installable Applets** — rejected: real versioning and dependency resolution, but puts a build-and-publish step between an idea and a working tool, and makes every Applet care about virtualenvs.

## Consequences

A root may contain many flat folders. This is acceptable because the directory is storage, not navigation — the UI is the navigation, and browsing the folder by hand should never be necessary. Multiple roots keep contributed Applets visibly separate from built-ins without encoding a category in a path. Applets in a folder-convention model have no dependency-resolution story; that gap is tracked separately.
