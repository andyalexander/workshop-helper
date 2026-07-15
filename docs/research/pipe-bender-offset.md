# Pipe-bender offsets: what the two marks mean, and why the trade formula is right

Research resolving [issue #13](https://github.com/andyalexander/workshop-helper/issues/13).
Date: 2026-07-15.

Builds on [`pipe-bender-setback.md`](./pipe-bender-setback.md) (issue #4), which pinned
`setback = R_outside × tan(θ/2)` and established that `gain`, `deduct`, `take-up` and `shrink`
name **different quantities**. Same tool class: UK plumbing, copper tube to BS EN 1057, Monument
fixed-former lever bender.

Every claim below is tagged: **[D]** derived and verified numerically this session, **[S]** carried
by a source I retrieved and read this session, with the quote reproduced, **[—]** could not be
sourced. Nothing is asserted from memory or plausibility.

---

## RECOMMENDATION

**The ticket's derivation is correct. So is the trade's formula. They answer different questions,
and the difference between them is exactly one `gain` — which is not a discovery, it is
Swagelok's published Adjustment method.**

| Quantity | Formula | What it is |
| --- | --- | --- |
| Vertex-to-vertex distance | `D / sin θ` | **exact** [D]. This is what `O × A` means [S]. |
| **Tangent-point mark gap** | `R_cl·θ + m` = `D/sin θ − gain` | **exact** [D]. Swagelok's Adjustment method [S]. |
| Minimum step | `D_min = 2·R_cl·(1 − cos θ)` | arcs meet; below this the offset is impossible [D] |
| Diagonal | `m = (D − D_min) / sin θ` | electrician2's `P'P` [S] |
| Gain (per bend) | `2·R_cl·tan(θ/2) − R_cl·θ` | the whole discrepancy [D][S] |
| Shrink (per offset) | `D·tan(θ/2) − 2·gain` | run-length lost — a **different** quantity [D][S] |

**The resolution in one line:** `D/sin θ` is a **vertex-to-vertex** distance, and the trade formula
is exact *for that convention*. It becomes wrong by one gain only if you mark it on **straight pipe
as a tangent-point gap** — and the two published methods that use it never do that.

**There is no UK convention to match.** BPEC teaches offsets with **no formula whatsoever** (§4) —
scale drawing plus template, exactly as #4 found for 90° bends. This is the strongest finding in
this document and it should shape the Applet.

**Implement `mark gap = R_cl·θ + m`, and label it as a tangent-point distance on straight pipe.**
Show `D/sin θ` alongside it, labelled as the vertex distance. Showing one without the other is how
this goes wrong.

---

## 1. The geometry — derived and independently verified [D]

Centreline model: leg, arc(+θ), diagonal `m`, arc(−θ), leg.

```
D        = 2·R_cl·(1 − cos θ) + m·sin θ         step achieved
D_min    = 2·R_cl·(1 − cos θ)                   at m = 0, the arcs meet
m        = (D − D_min) / sin θ                  the straight diagonal
gain     = 2·R_cl·tan(θ/2) − R_cl·θ             per bend
mark gap = R_cl·θ + m                           tangent point to tangent point
```

I did **not** trust the ticket's algebra. I integrated the centreline path numerically in 200 000
steps per arc and compared against the closed form:

| Check | Result |
| --- | --- |
| Traced path `D` vs closed form, 5 cases | agrees to **2 × 10⁻¹⁰** ✅ |
| Traced material gap vs `R·θ + m`, 5 cases | agrees to **9 × 10⁻¹⁰** ✅ |
| Exit heading returns to 0° | `−0.000000°` ✅ |
| `D / sin θ ≡ m + 2·R·tan(θ/2)` (vertex-to-vertex), 6 cases | agrees to **3 × 10⁻¹⁴** ✅ |
| `(D/sin θ) − (mark gap) ≡ gain` exactly, 6 cases | agrees to **3 × 10⁻¹⁴** ✅ |
| Ticket's table (141.4/138.7, 120.0/119.2, 169.7/165.9) | reproduced exactly ✅ |
| Ticket's `D_min` (36.6mm @15mm/45°, 51.5mm @22mm/45°) | 36.61 / 51.55 ✅ |

The identity `(1 − cos θ)/sin θ = tan(θ/2)` is what makes `D/sin θ` collapse to `m + 2R·tan(θ/2)`.
That is *why* the vertex distance and the trade formula are the same thing — not a coincidence.

**The whole family is the vertex model minus gains** [D] — verified to 10⁻¹⁴ across 6 cases:

```
vertex gap   = D · cosec θ
mark gap     = D · cosec θ  −  1 × gain        ← one bend's worth of material saved
shrink       = D · tan(θ/2) −  2 × gain        ← both bends
```

---

## 2. Q1 — Do the trade's instructions mark tangent points or vertices?

### **Vertices. Explicitly, in the manufacturer's own words.** [S]

Swagelok MS-13-43 p9, *Bend Layout → The Measure-Bend Method*, step 3:

> "Measure from the reference mark and make a bend mark on the tube at a distance equal to the
> desired bend length. **This mark indicates the vertex of the bend.**"

and step 5, which even defines the term:

> "For additional bends, use the vertex of the previous bend as the reference mark, repeat steps 3
> and 4 for the next bend. **(The vertex is where the center lines of the two legs of the angle
> intersect.)**"

And the offset section (p10) ties the two together explicitly:

> "Use the offset calculation as **the distance between the bend marks** described in Bend Layout,
> page 9."

Since bend marks indicate vertices, `L = O × A` is a **vertex-to-vertex distance**. The ticket's
hypothesis — *"the folk one may be correct for its own convention"* — is **confirmed**. It is not
folk; it is Swagelok's published convention, and it is exact.

**Greenlee does not define what its mark references** [—]. The SITE-RITE manual calls the quantity
the "**center-to-center distance**" and says only "Mark the conduit as shown", never saying whether
"center" is the vertex, the arc midpoint, or something else. I read the whole manual; the definition
is not in it. Worth noting the arc-midpoint reading gives the *same* material distance as the
tangent reading (`R·θ + m`), so Greenlee's silence is genuinely ambiguous, not merely unstated.

---

## 3. Q2 — Is `D/sin θ` taught as exact, or as an approximation?

**Both — because there are two different published methods, and each is exact in its own
bookkeeping.** The ticket guessed this precisely: *"A method where you mark, bend, then measure the
second mark from the first bend may never accumulate the error."* That is exactly what Swagelok
teaches.

### Method 1 — Measure-Bend: sequence it, and the gain never appears [S]

Swagelok p9–10. Mark the vertex, **bend**, then measure the next leg *from the vertex of the
completed bend*. The worked example is explicit:

> "3. Bend the tube 90° as described in Using the Bender, page 12.
> **4. Make a second bend mark 4 in. from the vertex of the 90° bend**, away from the reference mark."

Bend *first*, measure *after*. The bend physically consumes the gain, so measuring from the real,
post-bend vertex absorbs it automatically. `D/sin θ` is used raw and is **exact**. No arithmetic.

### Method 2 — Adjustment (Gain): lay it all out first, and pay one gain per bend [S]

Swagelok p21, which introduces it as precisely the alternative:

> "When determining tube bend location, **adjustment (gain) factors can be considered as an
> alternate way to achieve the desired layout**."

and defines the quantity tangent-to-tangent:

> "Adjustment is the difference in the length of tubing used in a radiused bend compared to the
> length of tubing required in a sharp bend, **when measured from the beginning to the end of the
> bend**."

and gives the rule (p22):

> "To determine the location of the bend mark for a subsequent bend, add the new section leg length
> to the previous bend mark location, **then subtract the adjustment (gain) of the previous bend**.
> P2 = P1 + 2.5 in. – 5/16 in. adjustment = 5 3/16 in."

### **The ticket's formula IS Swagelok's Method 2.** [D][S]

Swagelok's p22 example is a Z with two 90° bends — **which is an offset with θ = 90°** (`sin 90° = 1`,
so `D/sin θ = D = 2.5 in`). Its published mark gap is `2.5 − 5/16 = 2.1875 in`.

I inverted Swagelok's own tabulated adjustment (5/16 in) to the radius it implies, then ran the
ticket's `mark gap = R·θ + m` formula at θ = 90°, D = 2.5:

| | |
| --- | --- |
| Our `mark gap = R·θ + m` | **2.1875** |
| Swagelok's published `P2 − P1 = 2.5 − 5/16` | **2.1875** |
| Difference | **0.00e+00** |

P1 = 3, P2 = 5.1875 (published 5 3/16 ✅), P3 = 7.8750 (published 7 7/8 ✅).

> **Read this check for exactly what it is — corrected on review.** Because the radius was
> *back-solved from* Swagelok's tabulated 5/16, this agreement is **circular**: `mark gap` is
> algebraically `leg − gain`, so feeding their gain back in must return their number. It is a
> **consistency check on the algebra, not a confirmation of the geometry**, and the ✅ originally
> here overstated it.
>
> It does **not** show that ideal geometry reproduces Swagelok's tables — it does not. Their real
> 9/16 in radius gives a nominal gain of **0.2414 in**, not 5/16 = **0.3125 in**, and the formula
> yields **2.2586**, missing their published 2.1875 by **1.81 mm** (see §7).
>
> **The section's conclusion below still stands**, because it rests on the *algebraic* identity
> `leg − gain ≡ m + R·θ` — proven analytically in §1 to 10⁻¹⁴, independent of any radius — and on
> Swagelok's **prose**, quoted above and verified verbatim. Neither depends on this table.

**The ticket's derivation is not novel geometry — it is Swagelok's published arithmetic,
generalised to arbitrary θ.** That is the strongest possible answer to "the derivation disagrees
with the formula the trade uses": it doesn't. It *is* the formula the trade uses, in the trade's
other method.

### Independent trade confirmation, with field measurements [S]

[electrician2.com, *Mathematics of the Offset Bend*](http://electrician2.com/electa1/offset.html)
(Gerald Newton, rev. 2006) derives the identical formula independently:

> "**Distance Between Bends = (angle of bend / 360) X 2 x Pi x radius + P'P**"

`(angle/360) × 2π × radius` is `R·θ_rad`; `P'P` is our `m`. **Character-for-character the ticket's
`R_cl·θ + m`.** He is blunt about the cosecant used as a mark gap:

> "This method is **an approximation and is not mathematically correct, because it does not use the
> length of the arc of the bend**."

He also independently states the `D_min` finding:

> "**A negative straight pipe length means the two arcs are extending into each other and should be
> avoided.**"

His published calculator outputs reproduce from our derivation, within his own 1/16 in rounding:

| Case | Page says | Ours [D] |
| --- | --- | --- |
| R=20", 90°, 60" offset — distance between bends | 51 7/16 (51.4375) | **51.4167** ✅ |
| — same, multiplier | 0.857 | **0.857** ✅ |
| — same, "gain or shrink" | 8 9/16 (8.5625) | **8.5833** ✅ |
| 3/4 EMT R=5.2", 90°, 15" — distance between bends | 12 3/4 (12.75) | **12.7692** ✅ |
| — same, calculated shrinkage | 10 9/16 (10.5625) | **10.5385** ✅ |
| 3/4 EMT R=5.2", 60°, 7" — distance between bends | 7 1/2 (7.5) | **7.5333** ✅ |
| — same, calculated shrinkage | 2 15/16 (2.9375) | **2.9231** ✅ |

**The decisive bit is a physical measurement, not a calculation.** He bent both ways and measured:
a 15 in offset marked at the cosecant distance came out **17 1/2 in** — 2.5 in too high. Our
prediction for that error: **2.232 in** (marking `15` apart when `12.77` is required). Same sign,
same magnitude, off by ~1/4 in on a hand-bent field test. **The one-gain error is real and has been
measured in the field** — it is not an artefact of the algebra.

**Verdict on Q2:** `D/sin θ` is *exact* as a vertex distance and *wrong by one gain* as a straight-pipe
tangent mark gap. Swagelok never makes that mistake (it sequences, or it subtracts). Greenlee lays
out both marks on straight conduit and never mentions gain at all — see §5.

---

## 4. Q3 — What does BPEC actually teach for offsets?

### **Nothing arithmetic. There is no UK convention to match.** [S]

I read both BPEC documents end to end. **Neither contains a multiplier, a cosecant, a
"distance between bends", a gain, or any formula at all for offsets.** The taught method is a scale
drawing used as a physical template — precisely what #4 found for the 90° bend.

The setting-out (identical in both documents):

> "To set out, start as above then strike an arc from the centre of the pipe at 4 times the diameter
> as the radius... For 22mm 4 X dia = 88mm. For 15mm 4 X dia = 60mm."
>
> "Draw a circle as shown, and **draw a line from the tangent of the circle at the required angle of
> the offset**. To obtain the outside edge, draw a line parallel to the first line at a distance that
> matches the diameter of the tube used. That completes the setting out."

Then — and this is the important part — **the second bend is marked after the first is pulled**:

> "**Use the drawing as a template**, and decide on a fixed point, which can be a pipe clip, a fitting
> or something else. The pipe should be marked for bending **on the outside of the first bend** as shown"
>
> *(bend it, check the angle, allow for spring back)*
>
> "**The pipe can now be returned to the drawing** and should fit perfectly without any adjustment by
> pulling etc. ... **Use the drawing as a template to mark out the second bend**, in line the outside
> edge as shown."

**So BPEC's method is structurally Swagelok's Measure-Bend method with a drawing instead of
arithmetic.** The pipe goes back on the drawing *with bend one already pulled*; bend two is marked
from the physical reality. **The gain question cannot arise, because no mark gap is ever measured on
straight pipe.** This is not an oversight in BPEC — it is a method that is immune to the entire
problem by construction.

BPEC also restates the tolerance:

> "Check that the clearance is correct – **The accepted industry tolerance is +/- 2mm.**"

Note the gain at the angles that matter for 15mm copper is **0.32mm at 22.5°, 0.77mm at 30°,
2.69mm at 45°** [D]. **At and below 30° the gain is inside BPEC's own tolerance** — which is very
likely *why* nobody in UK copper ever needed the correction. At 45° it is not, and at 60° (6.72mm)
it is badly outside.

### ⚠️ A fabrication attempt, caught — worth recording

A web search for "BPEC offset multiplier cosecant" returned a generated summary asserting:

> "The search results also included BPEC (British Plumbing Employers Council) copper piping training
> materials, **confirming this methodology is used in UK plumbing training**."

**This is false.** I had already read both BPEC PDFs in full; neither contains a multiplier or a
cosecant. The summary inferred it from co-occurrence in a result list. **This is exactly the failure
mode that produced #4's fabricated provenance** — a plausible sentence, assembled from adjacency,
that no primary document supports. Recorded here as a caution, not as evidence.

---

## 5. Q4 — Gain / take-up / deduct / shrink: which one is this?

### **It is `gain`. It already has a name, and Swagelok owns the definition.** [S]

The discrepancy is `2·R_cl·tan(θ/2) − R_cl·θ` — **exactly** Swagelok's *adjustment (gain)*, defined
tangent-to-tangent ("from the beginning to the end of the bend"), verified to 10⁻¹⁴ across 6 cases [D].
**`gain` is the right term and needs no new coinage.** `CONTEXT.md` already reserves it correctly.

**It is emphatically *not* `shrink`.** Shrink is a different quantity — the run-length lost as the
offset walks the pipe sideways. Greenlee tabulates it separately from the multiplier, and says why:

> "**When working toward an obstruction, the conduit will appear to 'shrink.'** To compensate for
> shrinkage, use the shrink per inch of offset..."

Derived and verified [D]: `shrink = D·tan(θ/2) − 2 × gain` (identity holds to 10⁻¹⁴, 6 cases).
It depends on `D`; gain depends only on `R` and `θ`. Different inputs, different units of meaning.

### ⚠️ A live terminology collision — #4's warning, confirmed in the wild [S]

**electrician2.com uses "shrink" for *both* quantities on a single page**:

> "**Shrink = 2 x radius x (tan (bend angle / 2)) - Developed Length**"

— that is the **gain** formula (`Developed Length` is his term for the arc, `R·θ`). And he writes
"the **gain or shrink** is 8 9/16 inches", treating them as synonyms. Yet the *same page* tabulates
"Shrinkage = Shrinkage Multiplier x Offset Height" with multipliers 1/16 … 1/2 — which is the
**Greenlee run-length shrink**, a different number entirely.

So on one page, "shrink" means both `2R·tan(θ/2) − R·θ` and `≈ D·tan(θ/2)`. **This is precisely the
hazard #4 flagged, caught live.** It also means: any source using "shrink" without saying which one
is unusable without checking its formula.

### Greenlee's `deduct` and `take-up` are not in play [S]

`Deduct` remains the 90° **stub** constant, stamped on the tool — Greenlee's own instructions confirm
it is a stub-only concept:

> "See the Deduct length shown on the bender. **Subtract the Deduct length from Mark A** and make a
> new mark. This is Mark B." *(under Stub-Ups, not offsets)*

Neither `deduct` nor `take-up` appears anywhere in Greenlee's offset section. They are single-bend,
90°-stub concepts. Don't let them near the offset Applet.

**Summary for Q4:**

| Term | Quantity | Depends on | Owner |
| --- | --- | --- | --- |
| **gain** | `2R·tan(θ/2) − R·θ` | R, θ | Swagelok ("adjustment (gain)") — **this is our discrepancy** |
| shrink | `D·tan(θ/2) − 2·gain` | R, θ, **D** | Greenlee (run-length loss) |
| deduct | `R + OD/2` | R, OD | Greenlee (90° stub constant only) |
| take-up | per-tool 90° constant | tool | Greenlee (90° stub only) |

### Greenlee is the one source that could actually be wrong [D][S]

Greenlee **marks both points on straight conduit** and then bends both:

> "1. Determine the center-to-center distance... (For 45° x 45°, the multiplier is 1.4). Multiply the
> height of the obstruction by the multiplier (10" x 1.4 = 14). **2. Mark the conduit as shown.**
> 3. See the bending instructions."

That is Method 2 *without* the gain subtraction. Two mitigations, both real:

- **Greenlee's multipliers are coarse** [D]: 1.4 vs 1.4142 (45°), 1.2 vs 1.1547 (60°), 6.0 vs 5.7588
  (10°). On a 10 in offset the *rounding* error alone is 3.6mm at 45° and 11.5mm at 60°.
  The gain for 1/2" EMT at 45° is 5.1mm. **The rounding error and the gain are the same order of
  magnitude** — so the tables are empirical fudge, not geometry, and conduit tolerances absorb both.
- **Greenlee's shrink table tracks the *exact* arc-aware shrink, not the vertex model** [D]. For
  1/2" EMT (R = 4-3/16"), 10" at 45°: table 3.750, exact **3.782**, vertex model 4.142. The table is
  tuned to real bender radii. This is consistent with #4's finding that Swagelok's tables are
  likewise empirical.

electrician2 attacks exactly this and quantifies it: "the errors in distance between bends for a 30
inch high offset varied from 1/16 of an inch for 1/2 inch EMT with a 30 degree offset to **4 inches
for 5 inch rigid pipe with a 60 degree offset**" [S]. Big pipe, steep angle — where our 22mm/60°
gain of 9.46mm lives.

---

## 6. Q5 — Do the marks land on opposite faces?

**Partly sourced, and the answer is better than the question.** [S]

**Swagelok sidesteps it entirely** — p9, the very first note in Bend Layout:

> "**Note: Make all marks 360° around the tube.**"

A mark that goes all the way round has no face. Direction is then carried by a *separate* mark
(p10, step 5):

> "**Place a directional mark over the bend mark to indicate the outside, or heel, of the 45° bend.**
> This will help ensure the bend is made in the intended direction."

So Swagelok's answer is: **position marks are faceless; a distinct directional mark carries the
heel.** For an offset (two opposing bends) the two *directional* marks are on opposite faces — the
position marks are not. That is a cleaner model than "flip the pipe", and it is the one I'd
implement.

**BPEC marks the outside edge of each bend** — and since the bends oppose, each bend's outside edge
is the other's inside:

> "The pipe should be marked for bending **on the outside of the first bend** as shown"
>
> "Use the drawing as a template to mark out the second bend, **in line the outside edge** as shown."
> *(phrasing is verbatim from the source, including the missing preposition)*

**[—] No source I retrieved says "turn the pipe over" or equivalent.** BPEC's second-bend wording is
genuinely ambiguous in the extracted text, and its meaning rests on a diagram I could read only as
extracted labels ("Outside edge of pipe 'B'"). The derivation says the two outside edges are on
opposite faces; BPEC's phrasing is *consistent* with that but does not state it. **I am not going to
claim BPEC teaches the flip.** What is certain [D]: the geometry puts each bend's heel on the
opposite face, so *something* must flip — pipe, mark, or bender direction.

**Recommendation:** adopt Swagelok's model. Mark position 360° round; carry direction in a separate
heel mark. It makes Q5 a non-question.

---

## 7. Worked examples (implementation fixtures)

`R_cl` per #4's calibration: **15mm → 62.5mm** (from calibrated `R_outside` = 70mm), **22mm → 88mm**
(`4 × OD` BPEC default). All values [D], recomputed this session.

| Case | `D_min` | vertex gap `D/sin θ` | **mark gap** ⭐ | gain | shrink |
| --- | --- | --- | --- | --- | --- |
| 15mm, 22.5°, 60mm step | 9.52 | 156.79 | **156.47** | 0.32 | 11.29 |
| 15mm, 30°, 60mm step | 16.75 | 120.00 | **119.23** | 0.77 | 14.54 |
| 15mm, 45°, 100mm step | 36.61 | 141.42 | **138.73** | 2.69 | 36.04 |
| 15mm, 60°, 100mm step | 62.50 | 115.47 | **108.75** | 6.72 | 44.30 |
| 22mm, 30°, 80mm step | 23.58 | 160.00 | **158.92** | 1.08 | 19.27 |
| 22mm, 45°, 120mm step | 51.55 | 169.71 | **165.92** | 3.79 | 42.13 |
| 22mm, 60°, 150mm step | 88.00 | 173.21 | **163.74** | 9.46 | 67.68 |

**Minimum step `D_min = 2·R_cl·(1 − cos θ)`** — the Applet must refuse below this [D]:

| | 22.5° | 30° | 45° | 60° |
| --- | --- | --- | --- | --- |
| 15mm (`R_cl` 62.5) | 9.5 | 16.7 | **36.6** | 62.5 |
| 22mm (`R_cl` 88) | 13.4 | 23.6 | **51.5** | 88.0 |

**Gain, against BPEC's ±2mm tolerance** [D] — the row that decides whether the Applet matters:

| | 22.5° | 30° | 45° | 60° | 90° |
| --- | --- | --- | --- | --- | --- |
| 15mm (`R_cl` 62.5) | 0.32 | 0.77 | **2.69** | **6.72** | 26.83 |
| 22mm (`R_cl` 88) | 0.45 | 1.08 | **3.79** | **9.46** | 37.77 |

**Read this table carefully — it is the Applet's whole business case.** Below 30°, the gain is
smaller than the tolerance and the trade formula is fine. At 45° and above it is not, and it grows
fast. An Applet that corrects a 0.32mm error at 22.5° is noise; one that corrects 9.46mm at 22mm/60°
is the difference between a pipe that fits the clips and one that doesn't.

### Do NOT fixture Swagelok's worked example — retracted on review [D]

**An earlier revision of this document proposed** Swagelok's p22 worked example as a regression
fixture, on the grounds that `mark gap = R·θ + m` reproduces `P2 − P1 = 2.5 − 5/16 = 2.1875`
*"exactly (0.00e+00)"*. **The fixture recommendation is retracted.**

The agreement is real but **circular**, and §3 says why in its own text: the radius was
*back-solved from* Swagelok's tabulated 5/16 adjustment. `mark gap` is algebraically `leg − gain`,
so feeding their gain back in must return their number. §3 disclosed the inversion; **§7 dropped
that caveat and called the result a fixture against "a manufacturer's published arithmetic"**,
which it is not.

Worked through with the actual geometry (1/4 in tube, `R` = 9/16 in, θ = 90°, leg = 2.5 in):

| | value |
| --- | --- |
| nominal gain from geometry — `2R·tan(θ/2) − R·θ` | **0.2414 in** |
| Swagelok's tabulated adjustment | **0.3125 in** (5/16) |
| Swagelok's published `P2 − P1` | **2.1875 in** |
| our formula, `leg − nominal gain` | **2.2586 in** |
| **mismatch** | **0.0711 in ≈ 1.81 mm** |

Fed the **real** 9/16 in radius, the formula does not reproduce 2.1875 — it gives 2.2586, missing
by 1.81 mm. A fixture asserting 2.1875 would therefore **encode Swagelok's rounding as if it were
geometry**, and would fail the moment anyone supplied the true radius. It would test the table, not
the derivation.

**The recommendation contradicted itself on its face**, which is the useful lesson: the very next
paragraph said *"Do not fixture Swagelok's or Greenlee's tables… the nominal gain for a 9/16 in
radius at 90° is 0.2414 in, but Swagelok tabulates 5/16 = 0.3125 in."* The proposed fixture **was**
Swagelok's table. Both cannot stand, and the arithmetic settles which.

**Nothing else in this document depends on it.** The structural claim — that Swagelok's Adjustment
method *is* `mark gap = vertex gap − gain`, i.e. `leg − gain = m + R·θ` — is an **algebraic**
identity and holds regardless (§1, verified to 10⁻¹⁴). What fails is only the attempt to check that
identity **numerically against a published table**, and it fails for precisely the reason the
caveat below already gave. The prose sourcing in §2–§6 is unaffected.

**Do not fixture Swagelok's or Greenlee's tables** — #4's caveat holds and I re-confirmed it. The
nominal gain for a 9/16 in radius at 90° is **0.2414 in**, but Swagelok tabulates **5/16 = 0.3125 in**.
The metric table is likewise high (3mm/R15 → 6 tabulated vs 6.44 nominal; 6mm/**R15** → **8**, same
radius, different number). The tables encode real die radii and conservative rounding — they are
**not** the ideal geometry, and the 1.81mm gap above is that difference made visible.

**Fixture the derivation** (§1's numeric integration), never a manufacturer's table.

---

## 8. What the Result page should show (recommendation — input to #9, not settled)

Consistent with #4 §7: the Applet must show its working.

1. **Both distances, both labelled with their convention.** This is the single decision that keeps
   the tool honest:
   > `vertex-to-vertex = D / sin θ = 141.42 mm` — what the trade formula gives; the distance
   > between the *corners*, not a mark gap.
   > `mark gap = R·θ + m = 138.73 mm` — **measure this on the straight pipe**, tangent point to
   > tangent point. Difference = one gain = 2.69 mm.
2. **The minimum step**, checked before anything else: `D_min = 2·R_cl·(1 − cos θ)`. Below it, no
   arithmetic is meaningful — the arcs collide. Refuse, don't round.
3. **The gain, next to the ±2mm tolerance**, so the user can see when it matters. At 22.5° it is
   0.32mm and the Applet should say *"below the trade tolerance — the trade formula is fine here"*.
   Honesty about when the tool is unnecessary is what makes it trustworthy when it is.
4. **The BPEC method, as a first-class alternative — not a footnote.** BPEC's drawing-as-template
   method is *immune* to this entire problem, and for a 15mm offset at 30° it is strictly better than
   arithmetic. The page should say: draw it at `4 × OD`, pull bend one, put the pipe back on the
   drawing, mark bend two from the pipe.
5. **Which sequencing the number assumes.** `mark gap` assumes you mark both on straight pipe *before*
   bending. If the user bends first and measures from the vertex (Swagelok Method 1 / BPEC), they want
   `D/sin θ` and no correction. **The number is only correct for a stated method** — this is the
   offset analogue of #4's "name the reference surface".
6. **Springback and tolerance carry over unchanged** from #4 §5.

---

## Sources and trust

**High trust — manufacturer / awarding-body primary documentation, all retrieved and read in full
this session:**

- [Swagelok Hand Tube Bender Manual (MS-13-43)](https://www.swagelok.com/downloads/webcatalogs/en/ms-13-43.pdf) —
  downloaded, text-extracted, read. **The decisive source.** *Bend Layout* p9–10 (the vertex
  definition, the Measure-Bend method, "make all marks 360°", the directional/heel mark); *Offset
  Bend Formula* p10 (`L = O × A`, the 2.613/2.000/1.414/1.154 table, "use the offset calculation as
  the distance between the bend marks"); *Adjustment (Gain) Calculations* p21–23 (the gain
  definition, the subtract-one-gain-per-bend rule, the P1/P2/P3 worked Z, the fractional and metric
  adjustment tables).
- [BPEC — Copper Skills: Producing a 90° bend / an offset / a passover](http://bpec.org.uk/wp-content/uploads/2016/01/BPEC-Copper-Bends.pdf) —
  downloaded, read in full. Source of the **no-formula finding** and the return-to-the-drawing
  sequencing.
- [BPEC — Essential Plumbing Skills: Copper Pipe (2019 v2)](https://bpec.org.uk/wp-content/uploads/2019/11/BPEC-Essential-Plumbing-Skills-Copper-Pipefinal-version.pdf) —
  downloaded, read in full. Independently confirms the same offset method verbatim, and the ±2mm
  tolerance. Grepped for `offset|multipl|cosec|1.414|2.613|formula|calculat|gain` — **no formula hits**.
- [Greenlee SITE-RITE Hand Benders instruction manual (52034125)](https://www.itm.com/pdfs/cache/www.itm.com/843f/manual/843f-manual.pdf) —
  downloaded, read in full. Source of the offset/shrink tables, "center-to-center", "two equal
  opposing bends", the stub-only scope of `Deduct`, and the mark-both-then-bend method.

**Medium trust — trade secondary, used deliberately and labelled:**

- [electrician2.com — *Mathematics of the Offset Bend*](http://electrician2.com/electa1/offset.html)
  (Gerald Newton, rev. 26 Jan 2006) — **raw HTML fetched and read in full this session**, not via a
  summariser. This is a *secondary* trade source, not a manufacturer document, and I am citing it as
  **what the trade actually does and knows** — which the ticket explicitly permits. Its value: it
  derives `R·θ + m` independently, states the cosecant-as-mark-gap is "not mathematically correct",
  and — uniquely among everything I found — **field-tested both methods with a tape measure**. Its
  numeric claims were checked against our derivation and reproduce within its own 1/16 in rounding
  (§3). Its *terminology* is unreliable (it conflates gain and shrink) and is cited only as evidence
  of the collision, never as authority.

**Not used as evidence:**

- Web-search generated summaries. One asserted BPEC teaches the cosecant multiplier; the primary
  documents disprove it (§4). Recorded as a caution.
- Forum threads, YouTube, and the secondary conduit-bending write-ups that surfaced in searches
  (conduitbending.com, expertce.com, utilitypipesupply.com) — **not retrieved, not cited, not relied
  upon for any claim**.
- The Benfield Conduit Bending Manual — **I did not retrieve it**. It is described only via
  electrician2's characterisation, and is named here solely to attribute the origin of the
  multiplier tables *as that page reports it*. Treat as hearsay until someone reads it.

**Could not be sourced [—]:**

- Any UK source teaching an offset multiplier, cosecant, or distance-between-bends formula. **I
  believe none exists in the BPEC tradition**, on the evidence of two BPEC documents read in full.
- What Greenlee's "center-to-center" mark actually references.
- Any explicit instruction, in any source, to turn the pipe over between the two bends.

## Open questions for the Applet

1. **Which sequencing does the Applet assume the user will follow?** This is the offset's version of
   #4's reference-surface decision, and it is load-bearing in exactly the same way. `mark gap` is
   right for mark-both-then-bend; `D/sin θ` is right for bend-then-measure. **The Applet cannot emit
   one number without naming the method.** Suggest: emit both, always, side by side.
2. **Should the Applet actively recommend BPEC's drawing method over its own arithmetic below 30°?**
   The gain there (0.32–1.08mm) is inside the ±2mm tolerance, so arithmetic buys nothing. #4 reached
   the same conclusion for 90° bends. There is a real pattern here: **this tool's honest scope is
   steep angles and larger pipe**, and it should say so rather than pretend universal value.
3. **Is `mark gap` even the right headline Output**, or is the setting-out **drawing** the deliverable
   (per #4's conclusion) with the numbers as annotations on it? BPEC's entire method is "the drawing
   is the template". Rendering an accurate SVG the user can print and lay pipe on may beat any number.
4. **Confirm the flip convention against the physical bender.** One offset pulled in the actual
   Monument bender settles Q5 in five minutes and no reading will.
