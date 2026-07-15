# Pipe-bender setback: geometry, formula and terminology

Research resolving [issue #4](https://github.com/andyalexander/workshop-helper/issues/4).
Date: 2026-07-15.

Scope was narrowed during research: the target tool is a
[Monument lever bender for 15mm copper pipe](https://www.screwfix.com/p/monument-tools-lever-copper-pipe-bender-15mm/688pt)
— UK plumbing, copper tube to BS EN 1057, fixed-former lever bender. That rules the
UK copper-plumbing tradition (BPEC) as primary, with US conduit, instrument tubing and
aerospace treated as comparators for terminology only.

---

## RECOMMENDATION

**Term: keep `setback`. The Applet name survives.**

Define it once, in `CONTEXT.md`, as:

> **Setback**: the distance from the **vertex** back to the **start of the bend**, measured
> along the pipe's **outside edge**. `setback = R_outside × tan(θ/2)`.
> _Avoid_: gain, deduct, take-up, shrink — each names a *different* quantity (see §3).

The reason to keep it is narrower than it looks, and worth recording: **there is no native
UK copper-plumbing term for this quantity**, because BPEC never computes it — it teaches a
physical square-and-scrap-pipe alignment instead (§4). So the project must borrow a term.
`setback` is the best-attested term that names *this specific quantity* and does not collide
with `gain`, `deduct` or `shrink`. It is borrowed from US pipefitting and aerospace, not from
BPEC — state that in the docs so nobody "corrects" it later.

**Formula to implement:**

```
R_outside = R_centreline + OD/2
setback   = R_outside × tan(θ/2)        ← the headline Output
arc       = R_centreline × θ_radians
gain      = 2 × R_centreline × tan(θ/2) − arc
```

**The single most important decision: pin the reference surface.** Every trade uses
`R_ref × tan(θ/2)`; they differ *only* in which surface `R_ref` is measured to (§3). This is
the entire source of the terminology mess, and it is where a workshop tool silently computes
the wrong number. Reference the **outside edge**, because BPEC states that marking out is done
to the outside edge. Every Output's label must name its reference surface.

**Manifest inputs:**

| Input | Essential? | Notes |
| --- | --- | --- |
| `pipe_od` | **Essential** | 15 / 22 / 28 mm. Sets `OD/2`. |
| `bend_angle` | **Essential** | Former is marked 30/45/60/90°. |
| `bend_radius` (centreline) | **Essential** | Default `4 × OD` (BPEC). **Must be user-overridable — see below.** |
| `wall_thickness` | **Omit** | Does not enter the geometry. Only gates *feasibility* (Monument: 0.7mm max). |

`wall_thickness` is the one to leave out. It appears in the *sheet-metal* setback formula
`(R+T)·tan(A/2)` because there `R` is an **inside** radius and `R+T` reconstructs the outside
radius. For tube we already know the outside radius directly from `OD`. Including wall
thickness would double-count.

**Bend radius must be an input, not a lookup.** Monument does not publish the former radius —
it is absent from the Screwfix listing and from Monument's own product pages. BPEC's `4 × OD`
is a *setting-out drawing convention* ("Radius = ~4 X Diameter"), not a measurement of any
specific tool. So: default to `4 × OD`, let the user measure their own former once and save it.
This is a natural fit for the Manifest being "where the Host writes saved defaults back to"
(`CONTEXT.md`) — the calculator becomes correct for *this* bender after one calibration.

**Honest caveat on scope (§4):** for a **90° bend BPEC explicitly says no drawing or
calculation is needed** — you align a mark against a scrap pipe with a square. The Applet's
real value is therefore the **setting-out diagram** and the non-90° cases, not the single
number. Treat the SVG as the primary deliverable and `setback` as one Output within it.

---

## 1. The standard formula(s)

### The core geometry

Two straight legs meet at a **vertex** (Swagelok's word). The bend is a circular arc tangent to
both legs. The tangent point — where the bend starts — sits back from the vertex by the
**tangent distance**:

```
setback = R × tan(θ/2)
```

For θ = 90°, `tan(45°) = 1`, so setback = R exactly. This is why 90° feels like a special case
in every trade: the setback simply *is* the radius.

**Gain** — the material saved by rounding the corner rather than going round two sides of it:

```
gain = 2 × R × tan(θ/2) − R × θ_radians
```

For θ = 90°: `gain = 2R − πR/2 = 0.4292 × R`.

That 0.4292 constant is not folklore — Swagelok derives it on p21 of the Hand Tube Bender
Manual with an explicit worked illustration: for R = 1.000 in, the radiused path is 1.57 in
(= πR/2) and the sharp path is 2 in (= 2R), so the adjustment is 0.4292 in. Reproduced exactly.

### Verification performed

| Check | Source value | Computed | Result |
| --- | --- | --- | --- |
| Swagelok p21 arc, R=1.000, 90° | 1.57 in | 1.5708 | ✅ |
| Swagelok p21 sharp path | 2 in | 2.0000 | ✅ |
| Swagelok gain factor, 90° | 0.4292 | 0.4292 | ✅ |
| Swagelok p22 worked example P2 | 5 3/16 in | 5.1875 | ✅ |
| Swagelok p22 worked example P3 | 7 7/8 in | 7.8750 | ✅ |
| BPEC inside radius, 22mm pipe | R77 | 88 − 11 = 77 | ✅ |
| BPEC passover arcs, 15mm | 52.5 & 67.5 | 60 ∓ 7.5 | ✅ |
| BPEC passover arcs, 22mm | 77 & 99 | 88 ∓ 11 | ✅ |
| Offset multipliers (cosec θ) | 2.613/2.000/1.414/1.154 | identical | ✅ |
| Greenlee EMT take-up ⇒ implied R | 5"/6"/8" → 4.65/5.54/7.42 | matches published bender radii | ✅ |

### Offsets (a separate formula, same Applet family)

All three manufacturers agree, and it is exactly the cosecant:

```
distance between bends = offset_depth × (1 / sin θ)
```

Swagelok tabulates 2.613 / 2.000 / 1.414 / 1.154 for 22.5/30/45/60° — cosec to 3 dp. Greenlee
rounds to 2.6 / 2.0 / 1.4 / 1.2 (note Greenlee's 1.2 at 60° is a *coarse* rounding of 1.155).
Prefer the exact cosecant; do not copy Greenlee's rounded table.

---

## 2. Required inputs — essential vs refinement

**Essential:** centreline bend radius `R`, bend angle `θ`, and pipe `OD` (only to convert
between reference surfaces via `OD/2`).

**Not required:** wall thickness. It does not appear in the tube-bending geometry. Its only
roles are (a) feasibility — the Monument 15mm bender is rated to 0.7mm max wall, matching the
common BS EN 1057 R250 half-hard 15×0.7mm tube — and (b) as a *second-order* driver of
springback (§5), which is not computed anyway.

The trap: the sheet-metal formula `SB = (R + T)·tan(A/2)` *does* contain thickness, and it is
widely quoted. It is not applicable here. There, `R` is the **inside** radius and `R + T` is
simply reconstructing the outside radius. For tube, `R_centreline + OD/2` already *is* the
outside radius. Applying the sheet-metal formula to a tube radius would add a wall thickness
that is already accounted for.

---

## 3. Terminology — the map (most valuable section)

### The unifying insight

Every tradition computes the same thing:

```
setback = R_reference × tan(θ/2)
```

**They differ only in which surface `R_reference` is measured to.** Once you see that, the
apparent contradictions between sources dissolve — and the real hazard becomes clear: two
sources can both say "setback" and mean values differing by `OD/2` (7.5mm on 15mm pipe — well
outside the trade's own ±2mm tolerance, per BPEC).

| Reference surface | `R_ref` | 15mm pipe, 90° | Who uses it |
| --- | --- | --- | --- |
| Centreline | `R` | 60.0 mm | Swagelok, US pipefitting, CAD/routing |
| **Outside edge / back of bend** | `R + OD/2` | **67.5 mm** | **BPEC**, Greenlee, sheet metal |
| Inside / throat | `R − OD/2` | 52.5 mm | (used for clearance checks only) |

Sheet metal's `(R_inside + T)` *is* the outside radius — so sheet metal and BPEC agree on the
reference surface, and only disagree on how they name the radius they start from.

### Who says what

| Concept | Swagelok (instrument tube) | Greenlee (US conduit) | BPEC (UK copper) | Aerospace / sheet metal |
| --- | --- | --- | --- | --- |
| Vertex→bend-start distance | *(unnamed; uses "vertex")* | — | *(not computed)* | **Setback** `= K(R+T)`, `K = tan(A/2)` |
| Material saved vs sharp corner | **Adjustment (gain)** | — | "tube gain" (trade press) | Bend deduction |
| Per-tool 90° stub constant | — | **Deduct** *(stamped on tool)* | — | — |
| Length lost in an offset | — | **Shrink** | — | — |
| Arc length | — | — | — | **Bend allowance** |
| Corner of the two legs | **Vertex** | — | — | Mold line intersection |
| Datum to measure from | Reference mark | Arrow / star | **Fixed point** | — |
| Elastic recovery | **Springback** | Springback | **Spring back** | Springback |

### Findings that matter

1. **"Setback" appears in none of the three manufacturer sources.** Not Swagelok, not Greenlee,
   not BPEC. It is a sheet-metal/aerospace and US-pipefitting term. Keeping it is a deliberate
   borrow (see Recommendation), not an appeal to the UK trade.

2. **Greenlee's `deduct` is not a setback.** It is the 90° *stub* constant, referenced to the
   outside edge: `deduct = R + OD/2`. Verified — inverting published EMT take-ups (5"/6"/8"
   for 1/2"/3/4"/1") yields implied centreline radii of 4.65"/5.54"/7.42", which match Greenlee's
   published hand-bender radii. So `deduct` and centreline `setback` differ by exactly `OD/2`.
   **`deduct` ≠ `take-up` ≠ `setback`** — treat any source using them interchangeably as unreliable.

3. **Two different "K-factors" exist and they are unrelated.** In AC 43.13-1B / setback
   calculations, `K = tan(A/2)` (ranges 0→∞). In neutral-axis / bend-allowance work, `K` is the
   neutral-axis ratio (0.3–0.5). Same letter, same industry, different quantity. Never write bare
   `K` in this codebase.

4. **`gain` is safe to adopt** — Swagelok defines it precisely and UK trade press uses "tube
   gain" compatibly. It is the one term with no cross-trade collision.

5. **`shrink` is Greenlee's, and belongs to offsets, not to single bends.** Don't let it leak
   into the setback Applet.

---

## 4. What the diagram conventionally shows

BPEC's own setting-out sheets are the model here — they are literally instructions for drawing
the thing the Applet should render. A tradesperson expects:

- **The two straight legs**, extended as thin construction lines to meet at the **vertex**.
- **The arc**, tangent to both legs.
- **Three radii struck from one bend centre** — BPEC draws all three: centreline (`4 × OD`),
  inside/throat (`R − OD/2`) and outside/back (`R + OD/2`). The pipe is drawn as *two* parallel
  arcs, not a single line.
- **The bend angle** annotated at the vertex. Note BPEC annotates the *included* angle for
  offsets (135° for a 45° bend) — if the Applet shows an included angle, label it as such.
- **The tangent points** marked — where the bend starts and stops.
- **The setback dimension**, from vertex back to the tangent point, measured on the outside edge.
- **The fixed point** — BPEC's datum concept: the pipe clip, fitting, or pipe end that the
  measurement originates from. Long measurements are explicitly discouraged in favour of a
  nearby fixed point.
- **The mark**, on the outside edge (BPEC: "all the marking out ... is done to the outside edge").

Also worth encoding: **BPEC states the industry-accepted tolerance is ±2mm.** That is a good
sanity bound for the Applet — and justifies not chasing false precision.

**The scope-check finding.** BPEC's 90° sheet opens: *"There is no need to produce a drawing for
90° bends."* The taught method is physical, not arithmetic: mark the outside edge, put the fixed
point behind the back stop, then use a **square and a scrap piece of pipe** to align the mark
with the outside edge, and pull the bend. No setback number is ever computed.

This is a genuine challenge to the Applet's framing, and #4 should record it rather than bury it.
The defensible position: the calculator earns its place for **non-90° bends, offsets and
passovers** — exactly the cases where BPEC *does* mandate a scale drawing and says "use the
drawing as a template". Rendering that drawing is the valuable output. The 90° case should
probably *tell the user the square-and-scrap-pipe trick* rather than pretend arithmetic is
better.

---

## 5. Spring-back

**Verdict: real, material-dependent, and out of scope to compute. In scope to state.**

All three primary sources treat it identically — as an empirical allowance verified against a
physical reference, never a published formula:

- **Swagelok** (p19): *"All tubing will exhibit springback after a bend has been completed. The
  amount of springback depends on the bend angle, bend radius, tubing material, and wall
  thickness."* Guidance: *"Expect to allow 1 to 3° of compensation"*, and verify against a
  template, protractor or known angle. Also: *"Do not bend all the way to the bend mark when
  bending softer tubing such as copper or aluminum."*
- **BPEC**: *"the copper pipe will spring back a little due to its elasticity so release the
  pressure before checking the angle or your bend will not be accurate."* Check with a square or
  angle finder.
- **Greenlee**: *"Overbend rigid conduit slightly to compensate for springback"* — note this is
  scoped to **rigid conduit only**, not EMT. Material-dependent, from the manufacturer's own mouth.

**Is it material-dependent?** Yes, explicitly — Swagelok names material and wall thickness as
drivers. Physically, springback scales with yield strength / elastic modulus and with R/t. Half-hard
(R250) copper springs back noticeably less than stainless; annealed (R220) copper less again.

**Should the Applet compute it?** No. A closed-form springback factor requires yield strength and
elastic modulus for the specific temper and heat, and is unreliable for real tube — which is why
none of Swagelok, Greenlee or BPEC publishes one for hand benders. Every one of them says
"overbend slightly and check with a square". For 15mm half-hard copper in a lever bender, Swagelok's
1–3° is the right order of magnitude.

**Recommendation:** show springback as a **static note on the Result**, not an Output. Something
like *"Copper springs back roughly 1–3°. Release lever pressure before checking, and verify with a
square."* Computing a number here would be false precision well inside the ±2mm trade tolerance,
and would be the tool "computing the wrong number" in exactly the way #4 warns against.

---

## 6. Worked examples (implementation fixtures)

All values recomputed and cross-checked. Reference surface stated for every figure.

### Example 1 — 15mm copper, 90° (the primary case)

| | |
| --- | --- |
| **Inputs** | `OD = 15mm`, `R_centreline = 60mm` (4 × OD, BPEC), `θ = 90°` |
| `R_outside` | `60 + 7.5` = **67.5 mm** |
| **Setback (outside edge)** | `67.5 × tan(45°)` = **67.50 mm** |
| Setback (centreline) | `60 × tan(45°)` = 60.00 mm |
| Arc length (centreline) | `60 × π/2` = 94.25 mm |
| Gain | `2 × 60 − 94.25` = 25.75 mm |

_Independent cross-check:_ UK trade rule-of-thumb for 15mm is "measure back 70mm" — our 67.5mm,
rounded up to the nearest 10mm as the trade does. ✅

### Example 2 — 15mm copper, 45°

| | |
| --- | --- |
| **Inputs** | `OD = 15mm`, `R_centreline = 60mm`, `θ = 45°` |
| **Setback (outside edge)** | `67.5 × tan(22.5°)` = **27.96 mm** |
| Setback (centreline) | `60 × tan(22.5°)` = 24.85 mm |
| Arc length (centreline) | `60 × π/4` = 47.12 mm |
| Gain | `2 × 24.85 − 47.12` = 2.58 mm |

Note how small the gain is at 45° (2.58mm) — inside the ±2mm tolerance's neighbourhood. This is
why Swagelok's table says *"Adjustments on angles of less than 30° are minimal"* and lists 0.

### Example 3 — 22mm copper, 90°

| | |
| --- | --- |
| **Inputs** | `OD = 22mm`, `R_centreline = 88mm` (4 × OD), `θ = 90°` |
| **Setback (outside edge)** | `99 × tan(45°)` = **99.00 mm** |
| Setback (centreline) | 88.00 mm |
| Arc length (centreline) | 138.23 mm |
| Gain | 37.77 mm |

_Cross-check:_ trade rule-of-thumb for 22mm is "measure back 100mm" — our 99mm. ✅
_Cross-check:_ BPEC's published arcs for 22mm are R77 and R99 — our `R ∓ OD/2`. ✅

### Example 4 — imperial regression fixture (guards the general formula)

From Swagelok's own worked example (p22), 1/4 in tube, 9/16 in bender:

| | |
| --- | --- |
| Gain factor at 90° | `2 − π/2` = **0.4292** |
| Cumulative marks | `P1 = 3`, `P2 = P1 + 2.5 − 5/16 = 5 3/16`, `P3 = P2 + 3 − 5/16 = 7 7/8` |

Worth keeping as a test even though the project is metric: it pins the general
`2R·tan(θ/2) − Rθ` formula against a manufacturer's published arithmetic.

**Caveat for anyone tempted to fixture Swagelok's *tables*:** the tabulated adjustments are
rounded conservatively and reflect *real die radii*, not the nominal ones — the manual itself
says "**Approx** Bend Radius". Proof: 1/8 in and 1/4 in tube share a nominal 9/16 in radius but are
tabulated 1/4 in and 5/16 in respectively. Fixture the p21/p22 *derivation*, never the tables.

---

## Sources and trust

**High trust — manufacturer / awarding-body primary documentation:**

- [Swagelok Hand Tube Bender Manual (MS-13-43)](https://www.swagelok.com/downloads/webcatalogs/en/ms-13-43.pdf) —
  read directly. Springback p19; Adjustment (Gain) Calculations p21–23; offset cosecant table p11.
  The single best source: it *derives* the gain factor rather than asserting it.
- [BPEC — Copper Skills: Producing a 90° bend / an offset / a passover](http://bpec.org.uk/wp-content/uploads/2016/01/BPEC-Copper-Bends.pdf) —
  read directly. The authoritative UK copper-plumbing method for this exact tool class. Source of
  the "outside edge" reference, the fixed-point concept, the `4 × D` convention, ±2mm tolerance, and
  the "no drawing needed for 90°" finding.
- [BPEC — Essential Plumbing Skills: Copper Pipe (2019 v2)](https://bpec.org.uk/wp-content/uploads/2019/11/BPEC-Essential-Plumbing-Skills-Copper-Pipefinal-version.pdf) — corroborating.
- [Greenlee SITE-RITE Hand Benders instruction manual (52034125)](https://www.itm.com/pdfs/cache/www.itm.com/843f/manual/843f-manual.pdf) —
  read directly. Source of `Deduct`, `Shrink`, `Multiplier`, and the rigid-vs-EMT springback distinction.
- [Monument 15mm lever bender — Screwfix listing](https://www.screwfix.com/p/monument-tools-lever-copper-pipe-bender-15mm/688pt) —
  retailer listing (medium trust for spec). Confirms 0.7mm max wall and 30/45/60/90° former marks.
  **Notably does not publish the former radius**; nor does [Monument's own page](https://monument-tools.com/2020/06/24/pipe-bender-15mm-22mm/).

**Medium trust — trade/training secondary, used only for corroboration:**

- [FAA AC 43.13-1B](https://www.faa.gov/documentlibrary/media/advisory_circular/ac_43.13-1b_w-chg1.pdf) —
  authoritative in aerospace, but cited here *only* for the sheet-metal `SB = K(R+T)` terminology
  contrast. Not applicable to tube.
- [Aircraft Systems Tech — Making Straight Line Bends](https://www.aircraftsystemstech.com/2017/06/making-straight-line-bends.html) —
  secondary restatement of AC 43.13 setback/K-factor definitions. Used only for the terminology table.
- [Installer Online — How to bend copper pipe right](https://www.installeronline.co.uk/how-to/how-to-bend-copper-pipe-right-a-guide-for-heating-and-plumbing-engineers/) —
  UK trade press. Source of the "tube gain" usage. Its "add 0.53 OD" rule is unexplained and was
  **not** adopted.

**Weak — not relied upon:**

- The "measure back 70mm / 100mm" rule-of-thumb surfaced via trade blogs and forum discussion.
  Used **only** as a corroborating cross-check *after* the figures were derived from BPEC's
  published radii — never as a source of truth. It agrees with `R + OD/2` to within the trade's
  own rounding, which is why it is quoted.
- Forum threads (Screwfix Community, DIYnot) and YouTube training videos appeared in searches and
  were **not** used as evidence for any claim in this document.

## Open questions for the Applet

1. **What is the Monument 15mm former's actual centreline radius?** Unpublished. Needs one
   measurement from the physical tool, then saved as a Manifest default. Until then `4 × OD = 60mm`
   is a convention, not a measurement — and the Applet should not imply otherwise.
2. **Does the Applet render the 90° case at all,** given BPEC says not to calculate it? Suggest it
   renders the diagram plus the square-and-scrap-pipe method note.
3. **Should offsets/passovers be the same Applet or siblings?** They share the radius/angle inputs
   but use the cosecant, not `tan(θ/2)`. Probably siblings.
