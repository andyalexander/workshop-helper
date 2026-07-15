# Manifests are read-only to the Host; user overrides live in a Host-owned Overlay

The Host never writes to a Manifest. Every value a user overrides — saved defaults today, corrected calibration ([#15](https://github.com/andyalexander/workshop-helper/issues/15)), user tags if they ever arrive — is written to a single Host-owned **Overlay** file instead. At read time the Host merges the two: an Overlay entry, where present and valid, wins over the Manifest's authored value.

This amends [ADR-0004](0004-declarative-manifest-owns-input-schema.md), which made the Manifest the persistence layer for defaults. ADR-0004's two structural arguments — that discovery must be cheap and safe, and that a Host-owned schema makes Host features generic — are untouched: the Host still reads the schema from the Manifest and still renders, validates and saves generically. Only the *destination* of the write moves.

The reasoning:

**A Manifest is the author's declaration; a saved default is the user's state.** Mixing user state into an author-owned file is the modelling error underneath all three of this design's symptoms. Saved defaults conflict on `git pull` because they were written into a file git owns. They are destroyed by `uv tool upgrade` because the built-in Root ships inside the wheel and is replaced wholesale. They require comment-preserving TOML writing because the Host is editing prose a human wrote. One cause, three symptoms; separating the two files removes all three at once.

**The problem is live on day one, not on the day someone clones a collection.** It is tempting to defer this until shared Roots exist, since nothing is currently cloned from anyone. But the built-in Root is a read-only Root already — installed by `uv tool install` into a uv-managed venv, replaced on upgrade, possibly not writable at all — and the two worked examples ship in it, including the pipe-bender, which is exactly the Applet where save-as-defaults earns its keep. Deferring would ship a broken save-as-defaults in the demo that proves the design.

**One rule beats a taxonomy.** Every Root is read-only to the Host — built-in, the user's own, and cloned alike. No writability probing, no per-Root writability declaration, no built-in/user/foreign special-casing. A Root declaring itself writable would not even answer the question, only restate it: knowing a Root is read-only still leaves the value with nowhere to go.

**It deletes a dependency.** ADR-0004 noted that write-back requires something like `tomlkit`, because `tomllib` reads TOML but cannot write it. With Manifests read-only, the Host writes only a file it fully owns, in a format of its choosing, and `tomlkit` is gone — along with every bug in which the Host mangles an author's comments and formatting.

## The discardable invariant

**The Overlay is always safely discardable.** Deleting it returns the Host to a pristine working state. Nothing the Host cannot reconstruct from Manifests ever lives only in the Overlay.

This is what makes `git pull` and `uv tool upgrade` safe by construction rather than by care: the worst a schema change can do is cost a saved value. It also removes the need for a migration story — see Consequences.

## File format signals ownership

- **TOML = hand-authored, read-only to the Host.** Manifests, and Host config if it exists (#10).
- **JSON = machine-written, owned by the Host, safe to delete.** The Overlay (`overrides.json`), written with stdlib `json`.

This is not a format inconsistency but a visible rule, and it falls straight out of the stdlib's own asymmetry: `tomllib` (3.11+) reads TOML but cannot write it, while `json` does both. Reading TOML is free; writing it costs a dependency. So the split costs nothing to enforce and needs no `# DO NOT EDIT — GENERATED` banner — the extension carries the meaning.

The Overlay is a **separate file** from any Host config, never a section within it, for the same reason one level up: config is hand-edited, the Overlay is machine-written, and mixing them would put the Host back in the business of writing a file a human maintains. Which directory both live in is #10's decision.

## Merge rules

- **Keyed by Applet id alone**, no provenance in the key. Per ADR-0003 the folder name is the id and Roots are scanned PATH-style; per #6 each Applet is imported as a package named by its id, so ids are already unique across the loaded set. Shadow a built-in with your own Applet of the same id and saved defaults follow the id onto your version, where anything that no longer fits the schema is dropped by the rule below.
- **Namespaced by override kind**, so calibration (#15) can land beside input defaults without colliding — an Applet may legitimately have both an input and a calibration key named `r_outside`:
  ```json
  { "pipe-bender": { "defaults": { "size": "22", "angle": 45 } } }
  ```
- **Invalid or unrecognised entries are dropped**, falling back to the Manifest's authored default. This is never an error and is never reported. An Overlay entry can rot without anyone being at fault: the author may rename an input key, narrow `max` from 90 to 45, change a `number` to a `choice`, or drop the input entirely — all while the Manifest stays perfectly valid. So #8's malformed-Manifest error is the wrong surface, and there is no one to blame. The form already shows the value in use; re-saving is one click.
- **Orphaned entries are never pruned.** An Applet missing from the current scan is not evidence it is gone — its Root may be unmounted, not yet cloned on this machine, or registered in config but absent. Pruning would destroy defaults for an Applet that is coming back.

## Considered Options

- **Write back only to the user's own Root** — rejected: save-as-defaults would be dead on exactly the Applets that ship as worked examples.
- **Copy built-ins out to the user's directory on first run**, or **copy-on-write into the user's Root on save** — rejected: both fork the Applet's Python, not just its Manifest. Saving one default would silently opt the user out of every future fix to that Applet's compute — an especially sharp trap while #13 is actively re-litigating the pipe-bender's offset formula.
- **A Root declares whether it is writable** — rejected: a precondition, not an answer. It does not say where the value goes.
- **Defer until shared collections exist** — rejected: the built-in Root makes the problem live on day one.

## Consequences

**Defaults no longer sync between machines.** Manifest write-back had one real virtue: if the user's own Root is a git repo cloned onto two machines, saved defaults travelled with it. The Overlay is per-machine, so they no longer do. For defaults this is arguably an improvement — if the Linux box is the workshop and the Mac is the desk, workshop defaults *should* differ.

For **calibration it is a genuine wart**, accepted knowingly. Calibration does not describe a machine; it describes a physical bender in the workshop. `R_outside` 70mm is a fact about a lump of steel. Correcting it on one machine leaves the other wrong, and the way that surfaces is a mis-cut pipe. Syncing it would mean either placing the Overlay inside a Root (which Root? the built-in one that cannot be written?) or building a sync mechanism the map has no room for. The blast radius is one number, re-corrected once per machine. Tracked on #15.

**Your own Root gains a split brain.** Where the user is both author and user, "save as defaults" no longer edits the file they wrote, and a default can now come from two places with the Overlay winning. This is a real ergonomic loss, accepted in exchange for removing three failure modes.

**Compute-on-open becomes user-dependent.** #5 established that the Host computes on open iff every Input has a default. An Overlay value counts as a default — it must, or saving defaults on a partially-defaulted Applet would do nothing — so an Applet may compute on open for one user and not another. Use it once, save, and thereafter it is a compute-on-open calculator. This is what save-as-defaults is for, but the spec must say it out loud.

**No version field, and no migration story.** The drop rule *is* the migration strategy: if the Overlay's shape ever changes incompatibly, entries that no longer fit are dropped and the user re-saves. A version field would only buy the ability to write migration code the discardable invariant has already made unnecessary.

**The tags seam is decided in advance.** User-editable tags, if ever wanted, are the same seam and inherit this rule rather than reopening it.
