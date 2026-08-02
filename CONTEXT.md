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
The declaration an Applet makes about itself to the Host — its Applet type, name, tags, and, for calculators, the input schema. This is what the Host reads when discovering an Applet. The Manifest is the **author's** file: the Host only ever reads it, never writes to it (see Overlay, and [ADR-0007](docs/adr/0007-manifests-read-only-user-overrides-in-overlay.md)).

**Overlay**:
The Host-owned file holding the **user's** overrides of author-declared values — saved defaults, and any later override such as a corrected calibration. Merged over the Manifest at read time, keyed by Applet id. Always safely discardable: deleting it returns the Host to a pristine working state.
_Avoid_: Settings, preferences, config — the Overlay is machine-written user state, distinct from the hand-edited Host config that declares Roots and port.

**Root**:
A directory the Host scans for Applets. An Applet belongs to exactly one Root, which is its provenance — the built-in set, the user's own, or a collection obtained from someone else.

**Facet**:
One value you can filter the library by — a tag, or the Root. Facets **AND**: each one placed narrows what is left, and a placed tag facet is a **chip** in the sidebar. Because ADR-0003 leaves no hierarchy to climb back up, every candidate must show what it would *leave* before it is picked, and an empty result must recover in one click ([spec §9](docs/spec/host-framework.md)). Root is single-valued, so choosing a second replaces the first; tags are not.
_Avoid_: Category, folder (there is no hierarchy), filter (the whole sidebar is the filter — a facet is one value within it).

**Fault**:
An Applet folder the Host refused, rendered as a **greyed, un-openable card** rather than hidden. A Fault is *not* a broken Applet the Host tolerates: the index holds it apart from its Applets, so no lookup can resolve one into something to open. Faults the Host can see at scan without importing anything are **discovery-time** ([spec §10.1](docs/spec/host-framework.md)); those needing the Applet to run are **compute-time** and render on the Applet page instead (§10.2). Every Fault renders through one **error surface** — a blame line over a collapsed Details disclosure (§10.3).
_Avoid_: Error (too broad — a healthy `InvalidInput` refusal is an error and is not a Fault), invalid Applet (it may be a perfectly good Applet that lost a name collision).

**Input**:
A single named value a calculator Applet needs in order to compute — declared in the Manifest, supplied by the user. The counterpart to an Output: both are named, labelled, and carry a unit.
_Avoid_: Parameter, field, argument

**Result**:
What a calculator Applet's compute function returns: named Outputs, plus an optional table, HTML fragment, and graphic.

**Output**:
A single named value in a Result — a value with its unit and label. Outputs are structured data, which is what lets the Host format and lay them out generically.

**Mode**:
One named shape of a calculator: its own subset of the Inputs, and its own Outputs with its own primary. A mode changes **what exists**; an Input changes what a thing *is*. The selector is derived by the Host from the declared modes, so there is never a `mode` Input — the modes are the single source of truth, with no separate selector to fall out of sync.
_Avoid_: Tab, view, variant — all suggest a display choice, where a mode selects a different calculation.

**Calibration**:
Data measured off the physical kit in the **user's own** workshop, declared in the Manifest so it can be corrected in the Overlay without editing anyone's code. The test is one question: *must the owner correct this for their own kit?* If no, it is **reference data** and stays a plain dict in Python — 15mm copper is 15mm everywhere on earth, and a thread standard is not a property of your bench.
_Avoid_: Constants — a "constant" the user is expected to edit is a contradiction, and the name attracts a junk drawer.

**InvalidInput**:
An Applet's **healthy refusal** of a valid-typed but impossible combination, naming the Input(s) it belongs against. It is not a Fault: it covers the one gap static validation cannot reach, a **cross-field** condition, and the Host renders it inline exactly like a `min`/`max` failure. *Refuse, don't round.*

## Workshop domain

**Designation**:
A size named from a standard series — 15mm copper, M8, BSP ½" — rather than measured. A Designation is a name, not a quantity: BSP ½" thread measures roughly 20.96mm across, so converting it is meaningless rather than merely unhelpful. Contrast a genuine measurement (a bend angle, a caliper reading), which does convert.
_Avoid_: Size, spec — both blur the line between a name and a measured quantity.

**Setback**:
The distance from the vertex back to the start of a bend — `setback = R_centreline × tan(θ/2)`, measured to the **vertex of the two centrelines**. Every trade computes this quantity; they differ only in which surface the radius is measured to, so any Output naming it must also name its reference surface.

_Corrected._ This entry previously said "outside edge" with `R_outside`. That was **inference, and it was falsified at the bench** ([#17](https://github.com/andyalexander/workshop-helper/issues/17)): the owner's rule is *"measure back 70mm from where the centre line of the vertical pipe will be — forget about 'the corner'."* [#22](https://github.com/andyalexander/workshop-helper/issues/22) then found BPEC printing all three surfaces for one bend, which is how the wrong one got copied in the first place. The two readings are **indistinguishable at 90°**, the only angle anyone had ever checked.
_Avoid_: gain, deduct, take-up, shrink — each names a **different** quantity, not a synonym.

Borrowed from US pipefitting and aerospace. UK copper plumbing has no native term for it, because its training tradition never computes the quantity — it teaches a physical square-and-scrap-pipe alignment instead. Don't let anyone "correct" it to a BPEC term; there isn't one.

**Gain**:
The material a bend gives back: `gain = 2 × R_centreline × tan(θ/2) − R_centreline × θ`, the amount by which the arc is shorter than the two tangent legs it replaces. It is Swagelok's term and Swagelok's definition. **It is not a synonym for setback**, and the trade's `deduct`, `take-up` and `shrink` each name yet another quantity.

**Mark gap**:
The distance between the two marks of an offset, **on straight pipe, before either bend** — `mark gap = D · cosec θ − 1 × gain`, where each mark is where that bend starts. The committed convention. It is *not* the vertex-to-vertex distance `D · cosec θ`, which is the same set-out measured a different way; the two differ by exactly one gain, which is why the gain is emitted as its own Output rather than folded away.

**Minimum step**:
The smallest offset achievable at a given angle, `2 × R_centreline × (1 − cos θ)` — where the two arcs meet and no straight pipe is left between them. Below it the step is impossible, not merely tight. Note the owner's bench figures are *higher* than this at every angle but one, because a lever bender needs real straight pipe to grip: the geometric floor is where the geometry stops, not where the tool does.

## Notes on usage

A stored manual or manufacturer link is not a separate concept — it's simply a `documentation` Applet whose content is a page of links/references, tagged like any other Applet.
