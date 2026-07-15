# Workshop Helper

A local-first framework for browsing and running small, pluggable reference tools (calculators, documentation) for workshop and house use.

## Language

**Host** (or **Host application**):
The framework itself — the process that starts up, discovers Applets, and renders the shell UI for browsing, searching, and tagging them.
_Avoid_: Shell, app, framework (when referring to the running program specifically)

**Applet**:
A single pluggable unit — one calculator or one piece of documentation — that the Host loads and runs. Applets are the thing contributors write to extend the Host.
_Avoid_: Plugin (implies extending someone else's closed system), module (collides with Python's own module concept)

**Applet type**:
The category an Applet declares itself as in its Manifest — currently `documentation` or `calculator` (calculators may be static or interactive). A closed set the Host understands, not something Applets invent freely; the Host uses it to decide how to render and run the Applet.

**Manifest**:
The declaration an Applet makes about itself to the Host — its Applet type, name, tags, and, for calculators, the input schema. This is what the Host reads when discovering an Applet, and where the Host writes saved defaults back to.

**Root**:
A directory the Host scans for Applets. An Applet belongs to exactly one Root, which is its provenance — the built-in set, the user's own, or a collection obtained from someone else.

**Result**:
What a calculator Applet's compute function returns: named Outputs, plus an optional table, HTML fragment, and graphic.

**Output**:
A single named value in a Result — a value with its unit and label. Outputs are structured data, which is what lets the Host format and lay them out generically.

## Notes on usage

A stored manual or manufacturer link is not a separate concept — it's simply a `documentation` Applet whose content is a page of links/references, tagged like any other Applet.
