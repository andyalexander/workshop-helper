# Unit is a display label; the Host ships no unit model

An Input's `unit` is shown beside the field and carried onto Outputs, but the Host never interprets or converts it. `compute()` receives what the user entered, in the unit the Manifest declared. Where an Applet genuinely needs dual-unit entry, it declares a unit `choice` Input like any other and converts inside `compute()`.

This reads like an omission — converting units looks like exactly the sort of generic job a Host should own. Two things make it a bad trade here.

**Most workshop "units" are Designations, not quantities.** 15mm copper, M8, BSP ½" are names drawn from a standard series; there is no quantity there to convert (a BSP ½" thread measures roughly 20.96mm across). These are `choice` Inputs, and conversion is meaningless for every one of them. The mixed-unit reality of a UK workshop — pipe in mm but fittings in inches, fasteners in M8 but Whitworth on old kit, timber in mm but sheet goods in 8×4 — is almost entirely mixed *Designations*, which no unit model would help with.

**The conversions that remain are not all linear.** Across every calculator on the map, the only true measurements are a bend angle (degrees — nobody wants radians) and the closest-bolt-size finder's caliper readings. That finder needs outer diameter (`× 25.4`, linear) and thread pitch (`pitch_mm = 25.4 / TPI`, **reciprocal**). A generic unit model built the obvious way — a table of multipliers per dimension — is silently wrong on the pitch, and wrong in the worst possible shape: coarse-versus-fine is a small difference, so the bad answer looks plausible rather than obviously broken. Getting it right means expressing non-linear conversions in the Manifest — a unit library's worth of machinery, serving one calculator. An author writing `25.4 / tpi` themselves gets it right, locally and visibly.

## Considered Options

- **Host converts to a canonical unit before calling `compute()`** — rejected. The intuition behind it is sound (it keeps Applet authors out of unit-conversion bugs), but it inverts in this domain: the Host would be *introducing* the bug, generically, across every Applet, in precisely the case that matters.
- **Host converts lengths only; non-linear cases left to authors** — rejected. Two mechanisms for one concept, and an author has to know which side of an invisible line their Input falls on.

## Consequences

Unit correctness becomes a per-Applet property rather than a Host guarantee. Two Applets can label the same quantity differently, and an author can get their own conversion wrong. At this scale that is accepted.

Nothing is left for a global or per-Applet unit preference to toggle, so the Host has none. The stickiness such a preference would offer — "I have imperial calipers, stop asking me every time" — already falls out of [ADR-0004](./0004-declarative-manifest-owns-input-schema.md): a unit `choice` is an Input, so "save as defaults" persists it, at finer granularity than a global flag could manage (imperial on the bolt-finder, metric everywhere else). Locale therefore carries no weight for units.
