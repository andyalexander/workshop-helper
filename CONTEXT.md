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

**Input**:
A single named value a calculator Applet needs in order to compute — declared in the Manifest, supplied by the user. The counterpart to an Output: both are named, labelled, and carry a unit.
_Avoid_: Parameter, field, argument

**Result**:
What a calculator Applet's compute function returns: named Outputs, plus an optional table, HTML fragment, and graphic.

**Output**:
A single named value in a Result — a value with its unit and label. Outputs are structured data, which is what lets the Host format and lay them out generically.

## Workshop domain

**Designation**:
A size named from a standard series — 15mm copper, M8, BSP ½" — rather than measured. A Designation is a name, not a quantity: BSP ½" thread measures roughly 20.96mm across, so converting it is meaningless rather than merely unhelpful. Contrast a genuine measurement (a bend angle, a caliper reading), which does convert.
_Avoid_: Size, spec — both blur the line between a name and a measured quantity.

**Setback**:
The distance from the vertex back to the start of a bend, measured along the pipe's outside edge — `setback = R_outside × tan(θ/2)`. Every trade computes this quantity; they differ only in which surface the radius is measured to, so any Output naming it must also name its reference surface.
_Avoid_: gain, deduct, take-up, shrink — each names a **different** quantity, not a synonym.

Borrowed from US pipefitting and aerospace. UK copper plumbing has no native term for it, because its training tradition never computes the quantity — it teaches a physical square-and-scrap-pipe alignment instead. Don't let anyone "correct" it to a BPEC term; there isn't one.

## Notes on usage

A stored manual or manufacturer link is not a separate concept — it's simply a `documentation` Applet whose content is a page of links/references, tagged like any other Applet.
