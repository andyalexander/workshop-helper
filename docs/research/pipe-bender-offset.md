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

**BPEC teaches offsets with no formula whatsoever** (§4) — scale drawing plus template, exactly as
#4 found for 90° bends.

**But the UK trade convention exists, and it is transposed** (§4A — added on review, from a source
the repo owner supplied). A UK plumber's masterclass teaches the multiplier method explicitly, marks
both points on straight pipe (the case this document predicted would be wrong by one gain), and
**swaps the 30° and 60° multipliers** — using `1.2` for 30° where `1/sin 30° = 2`. Wanting an 80mm
set, that delivers **48mm at 30°** and **144mm at 60°**. It is demonstrated only at 45° — the fixed
point of the swap, and the one angle where the error cannot show.

**This, not the gain, is the Applet's business case.** The gain is 0.3–2.7mm at the angles UK
plumbers actually use, and at 45° the trade's rounding of 1.4142 → 1.4 cancels ~42% of it anyway.
The transposition is a **30–60mm** error, and it is in circulation.

**Implement `mark gap = R_cl·θ + m`, and label it as a tangent-point distance on straight pipe.**
Show `D/sin θ` alongside it, labelled as the vertex distance. Showing one without the other is how
this goes wrong.

> **Added 2026-07-19 (§4B) — the owner's bench figures land, and they settle two things.** Measured
> multipliers and minimum steps for both benders were scored against this derivation. **15mm at 30°
> and 45° confirm the cosecant to within ±2mm — so §4A's transposition is now confirmed by
> measurement, not just by derivation** (the owner measures 2.0 at 30° where the video teaches 1.2).
> **22mm at 60° lands on the gain-corrected value (1.08), not on any published constant** — the
> strongest evidence in this document that the gain correction is real on these tools.
>
> It also produces the finding that should drive the Applet's interface: **`multiplier = cosec θ −
> gain/D` is a function of the step, so no constant multiplier is correct.** Flat at 30°, moving by
> 0.07 across a normal range at 60°. **Emit millimetres for the entered step, not a multiplier.**
> Three of the six figures conflict and are flagged for re-measure; because they point in opposite
> directions they are not a systematic fault. See §4B.

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
> *back-solved from* Swagelok's tabulated adjustment, this agreement is **circular**: `mark gap` is
> algebraically `leg − gain`, so feeding their gain back in must return their number. It is a
> **consistency check on the algebra, not a confirmation of the geometry**, and the ✅ originally
> here overstated it.
>
> It does **not** show that ideal geometry reproduces Swagelok's tables — it does not. Their real
> former (9/16 in ⇒ `R` = 14.29mm) gives a nominal gain of **6.13mm**, not the tabulated **7.94mm**,
> and the formula yields **57.37mm** against their published **55.56mm** — a **1.81mm** miss (§7).
>
> **The section's conclusion below still stands**, because it rests on the *algebraic* identity
> `leg − gain ≡ m + R·θ` — proven analytically in §1 to 10⁻¹⁴, independent of any radius — and on
> Swagelok's **prose**, quoted above and verified verbatim. Neither depends on this table.
>
> Note also that this example is **imperial US tube-fitting practice**, not UK copper plumbing.
> It is quoted because it is the only source that *documents* the marking convention (§2) — not
> because its numbers are a target to hit.

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

### **Nothing arithmetic — but "no UK convention exists" was too strong. See §4A.** [S]

> **Corrected on review.** This section's original headline read *"There is no UK convention to
> match."* The BPEC finding below is sound and unchanged: **the awarding body teaches no formula.**
> But the repo owner then supplied a UK plumber's pipe-bending masterclass that teaches a multiplier
> method explicitly (§4A). **"BPEC teaches no formula" ≠ "UK plumbers use no formula."** The
> convention exists; it is transmitted on site and on YouTube rather than through the syllabus, and
> the version in circulation is **transposed**. That is a far more useful finding than its absence
> would have been — and it is the one this research got wrong by only reading what is published.

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

## 4A. The UK trade convention — it exists, and it is transposed [S][D]

**Added on review.** The repo owner supplied a transcript of a UK plumber's pipe-bending
masterclass, demonstrating on a **Monument** bender in **copper/MLCP**. It answers three of this
ticket's questions from inside the owner's own tradition, and overturns §4's original headline.

**Provenance — URL supplied and verified [S]:**
[*Pipe bending master class!*](https://www.youtube.com/watch?v=OiBUU_QxD3A) — channel **mmplumber**,
uploaded 2025-03-28, 629s (10:29). I fetched the page this session and confirmed the title, channel,
and duration; the owner's transcript runs to 10:28, matching the stated length. **The video itself I
have not watched — the spoken content is quoted from the owner's transcript**, and the description
below is quoted from the page I retrieved.

Treat it as a **medium-trust trade source**: evidence of what a working UK plumber teaches, not an
awarding body's specification — and, per §4A's findings, **explicitly not authority for the
numbers**.

### It teaches a multiplier method — so the convention exists

> "there is a nice simple formula that we use to calculate this right every single time… if you want
> to bend at 30° you need to times your distance… by **1.2** … if you want to bend a 45 we times
> that Distance by **1.4** … and if you want to do 60° then you need to times that set Distance by
> **two**"

The distance is explicitly **centre-to-centre** (*"Center of here to center of here"*), and **both
marks are made on the straight pipe before any bending**:

> "Mark our first Mark let's just say here and then what you want to do is Mark your **112 after
> it**"

**This is precisely the case §3 predicted would be wrong by one gain** — the trade formula marked on
straight pipe as a mark gap. §2's conclusion said the published methods "never do that." **This one
does.**

### The multipliers are transposed [D]

| angle | video | `1/sin θ` | |
| --- | --- | --- | --- |
| 30° | **1.2** | **2.000** | ✗ |
| 45° | **1.4** | **1.414** | ✓ |
| 60° | **2** | **1.155** | ✗ |

The video's numbers are the standard trade table's numbers — `2` is exact for 30°, `1.2` is the
usual rounding of 1.1547 for 60° — **assigned to the wrong angles.** 30° and 60° are swapped. This
is a memorisation transposition, not a rival convention.

**The corrected table** — what the multipliers should be:

| angle | multiplier `1/sin θ` | trade rounding |
| --- | --- | --- |
| 30° | 2.0000 | **2.0** |
| 45° | 1.4142 | **1.4** |
| 60° | 1.1547 | **1.2** |

#### Why it is a transposition and not a different angle convention [D]

The one reading that would rescue the video is a **complementary** angle convention (his "30°"
meaning a 60° deviation), under which his multipliers would be correct. **His own full cross refutes
it**, with no appeal to outside sources:

> "bend the first Bend at **60°**… and then… bend both sets at **30°**"

A full cross must leave the pipe **parallel** to where it started, so the turns must cancel:

| reading | sum of turns | result |
| --- | --- | --- |
| marks are **deviation** angles | `60 − 30 − 30` = **0** | parallel ✓ |
| marks are **complements** | `30 − 60 − 60` = **−90** | pipe ends 90° off ✗ |

The 90° mark settles it a second time: it produces a right angle, which only a deviation reading
allows. **The bender's marks are deviation angles**, so the multiplier is `1/sin θ`, and `1.2` at
30° is not defensible under any reading.

Physically the same point, without algebra: a *shallow* set needs its marks *further* apart. The
video has it backwards.

**What it costs**, for a wanted 80mm set on 15mm copper (`R_cl` = 62.5):

| | mark gap used | set achieved | error |
| --- | --- | --- | --- |
| 30° × **1.2** (video) | 96.0 | **48.4** | **−31.6mm** |
| 30° × 2.0 (correct) | 160.0 | 80.4 | +0.4mm |
| 45° × **1.4** (video) | 112.0 | 81.1 | **+1.1mm** ✓ |
| 60° × **2** (video) | 160.0 | **144.4** | **+64.4mm** |
| 60° × 1.155 (correct) | 92.4 | 85.8 | +5.8mm |

**The demo is at 45° — the fixed point of the swap, and the only angle at which the error is
invisible.** He measures the result and it is right (*"we just double check that this is 80"*),
which is exactly what one would predict.

### Why the rounding hides the gain at 45° [D]

At 45°, the video's method lands **+1.1mm** from the requested set — inside BPEC's own ±2mm. That is
not luck:

| | value |
| --- | --- |
| exact vertex distance, `80 × 1.4142` | 113.14 |
| **correct mark gap**, `R·θ + m` | **110.45** |
| gain (the §1 discrepancy) | 2.69 |
| video's `80 × 1.4` | **112.00** |

**Rounding 1.4142 → 1.4 cancels ~42% of the gain**, and the remainder falls inside the tolerance.
So the trade formula survives contact with reality at 45° **because two errors partially cancel** —
one from rounding the multiplier down, one from ignoring the gain. This is the mechanism §3
hypothesised ("the setback step silently absorbs it") found in a different place than expected: not
in the sequencing, but in the rounding.

### It confirms the flip, and the 360° mark [S]

**Q5 is answered by a UK source.** The pipe *is* turned over:

> "once the first Bend's done **flip them over** and Mark just here and then Square them up"

and the 360° mark is taught for exactly that reason — the same convention Swagelok gives, arrived at
independently:

> "go ahead and Mark all around your pipes **CU you will be flip flopping it about**"

### It sources the 70mm [S]

For the 90° bend, from a mark at the corner:

> "you want to mark the center Mark of the pipe location and then you go ahead and you **measure 70
> mm back from this Mark**… and you want to mark all the way around the pipe"

**This is #4's 70mm, and #4 recorded it as an unsourced owner-supplied figure.** At 90°,
`setback = R_outside × tan 45° = R_outside`, so 70mm back from the vertex ⟹ `R_outside` = 70mm —
consistent with #4's calibration. *(The irony is worth recording: the citation #4 had to strip as
fabricated was a video. The real video says 70.)*

### The mark references the **bender**, not the geometry — a third convention

Both the 70mm mark and the offset marks are aligned to a **physical feature of the Monument bender**:

> "using the monument pipe benders **this Mark here goes just after the arm**"
> "you want to **start your marks just after the arm**"

This is neither a tangent point nor a vertex — it is a **bender datum**, and §2's
tangent-vs-vertex dichotomy does not cleanly apply to it. Two consequences:

- **70mm equals `R_outside` only if that datum sits at the tangent point.** If it does not, 70mm is a
  datum-to-vertex distance, and #4's rule — *store `R_outside`, extrapolate `setback = R_outside ×
  tan(θ/2)`* — would be extrapolating from a number that is not `R_outside`. At 90° the two are
  indistinguishable (`tan 45° = 1`), which is exactly why #4 could not catch it.
- **"Just after the arm" is not a measurement.** It is a hand skill with an unquantified tolerance,
  and the method rests on it being repeatable.

#### The author's own description argues against the pessimistic reading [S]

Retrieved from the video page this session:

> "The 70 mm measurement **does also work on your standard bender, not just the Monument one**."

That is evidence the 70mm is **geometric, not a Monument artifact**. A traditional scissor bender has
no "arm" to align to, and its frame geometry differs — so a datum-to-vertex distance would not be
expected to transfer between the two. A **former radius** would. This **supports #4's reading** that
`R_outside` = 70mm is a real radius, and correspondingly supports extrapolating
`setback = R_outside × tan(θ/2)` to other angles.

Stated at the strength it deserves: this is **the author's claim, not a measurement**, and it is the
same author whose multipliers are transposed (§4A) — so it is corroboration, not proof. But it is
the only cross-bender evidence in existence, it points the opposite way to the concern above, and
**intellectual honesty requires recording that the objection was raised here and then partly
answered by the source itself.**

**Still not settled by reading — the 45° check in #17 remains the only test that can separate the
two**, since every existing check (the video, #4, the owner) was made at 90°, where the readings
agree by construction.

---

## 4B. Owner's bench figures — and why a constant multiplier cannot be right [S][D]

**Added 2026-07-19.** The repo owner supplied multipliers and minimum steps measured on **their own
two benders**. These are the first figures in either ticket taken from *the tools this project is
actually for*, so they outrank every manufacturer table quoted above. Scoring them turned up
something more useful than any individual number: **a structural reason no constant multiplier can
be correct**, which changes what the Applet should emit.

**Method, as stated by the owner.** The multiplier is applied to the **step** — the offset between
the two parallel legs. Both marks go on the **straight pipe before any bending**: mark one, mark two
at `step × multiplier`, bend the first mark, move to the second, bend that. Worked example given: a
60mm step at 30° on 22mm ⇒ marks **111mm** apart.

That is precisely the sequencing §3 and §4A identify as **wrong by one gain** — Greenlee's and the
masterclass's method, not Swagelok's. So the quantity being measured here is the **mark gap**, and
the correct comparison is `D·cosec θ − gain`, never the bare cosecant.

### The structural finding: the multiplier is a function of the step

```
mark gap   = D · cosec θ − gain
multiplier = mark gap / D = cosec θ − gain / D
```

`gain` is a fixed millimetre quantity — it depends only on `R_cl` and `θ`, **not** on the step. So
dividing by `D` makes the multiplier **step-dependent** [D]: it approaches the cosecant as the step
grows and falls away from it as the step shrinks, fastest at steep angles where gain is largest.

Correct multiplier, `R_cl` = 62.5mm (15mm) and 88mm (22mm), across the working range [D]:

| | gain | 50mm | 75mm | 100mm | 150mm | 200mm | 300mm | → ∞ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15mm 30° | 0.77 | 1.985 | 1.990 | 1.992 | 1.995 | 1.996 | 1.997 | 2.000 |
| 15mm 45° | 2.69 | 1.360 | 1.378 | 1.387 | 1.396 | 1.401 | 1.405 | 1.414 |
| 15mm 60° | 6.72 | — | 1.065 | 1.088 | 1.110 | 1.121 | 1.132 | 1.155 |
| 22mm 30° | 1.08 | 1.978 | 1.986 | 1.989 | 1.993 | 1.995 | 1.996 | 2.000 |
| 22mm 45° | 3.79 | — | 1.364 | 1.376 | 1.389 | 1.395 | 1.402 | 1.414 |
| 22mm 60° | 9.46 | — | — | 1.060 | 1.092 | 1.107 | 1.123 | 1.155 |

*(dashes are below the geometric floor `D_min`.)*

**At 30° the column is flat to three decimals and a constant multiplier of 2.0 is genuinely fine. At
60° it moves by 0.07 across the range — 7mm of mark position per 100mm of step.** So the honest
statement is not "the multiplier is 1.155" or "1.2", but **"at 60° there is no such thing as the
multiplier"**. This is the sharpest form of §8.5: the number is correct only for a stated method
**and a stated step**.

### The figures, scored

Each multiplier run forwards through the geometry: mark at `step × multiplier`, bend both, and see
what step actually comes out [D]. Scored against BPEC's ±2mm.

| | multiplier | at the stated minimum step | at a 100mm step | verdict |
| --- | --- | --- | --- | --- |
| 15mm 30° | 2.0 | 30 → **30.4** (+0.4) | 100 → **100.4** (+0.4) | ✅ **confirmed** |
| 15mm 45° | 1.4 | 50 → **51.4** (+1.4) | 100 → **100.9** (+0.9) | ✅ **confirmed** |
| 15mm 60° | 1.2 | 70 → **78.6** (+8.6) | 100 → **109.7** (+9.7) | ❌ **conflict** |
| 22mm 30° | 1.85 | 60 → **56.0** (−4.0) | 100 → **93.0** (−7.0) | ❌ **conflict** |
| 22mm 45° | 1.32 | 80 → **77.3** (−2.7) | 100 → **96.0** (−4.0) | ❌ **conflict** |
| 22mm 60° | 1.08 | 150 → **148.5** (−1.5) | 100 → **101.7** (+1.7) | ✅ **confirmed** |

**Three of six land inside the trade tolerance, and they are the most valuable rows in this
document.**

**15mm at 30° and 45° independently confirm the cosecant** — and therefore confirm, from the owner's
own bench, that **§4A's video is transposed**. The owner measures **2.0 at 30°** where the video
teaches 1.2. That is no longer a derivation against a transcript; it is a measurement against a
transcript.

**22mm at 60° is the single most informative figure here.** 1.08 is *not* the trade table's 1.2, and
it is not the cosecant's 1.155 — it sits on the **gain-corrected** value (1.060 at a 100mm step,
1.092 at 150mm). A number that lands on the corrected curve rather than either published constant is
very hard to arrive at by anything except measurement.

### The three conflicts — and why they are not one fault

The user's standing rule is that empirical figures win unless the gap is small enough to be
measurement noise. These gaps are **not** small: 4–10mm against a ±2mm tolerance. But they also
**cannot share a physical cause, because they point in opposite directions** [D] — the 15mm figure
is too *high* and the 22mm figures too *low*, at overlapping angles on the same geometry. A former
radius error, a datum offset or a springback allowance would push both the same way.

Two specific things were tested and **ruled out** [D]:

- **A fixed datum offset** (e.g. the "just after the arm" mark of §4A sitting a constant distance
  off the tangent point). The implied offset would have to be the same at every angle. It is not —
  at any assumed step from 50 to 300mm the implied offset spreads ~9mm across the three angles.
- **A different 22mm former radius.** Gain scales with `R_cl`, so a bigger former *could* in
  principle depress the multipliers. Back-solving the required radius per angle gives **731mm at
  30°, 175mm at 45°, 104mm at 60°** — not a radius, and not a tool.

What survives, per row:

1. **15mm 60° = 1.2 looks carried over, not measured.** 1.2 is the standard trade rounding of
   1.1547, and it is the one figure in the set that matches a *published table* rather than the
   bench. Worse, its two errors **add** instead of cancelling: rounding 1.1547 → 1.2 pushes the mark
   gap up, and ignoring gain pushes it up again. (Contrast §4A's 45° case, where the rounding
   *down* to 1.4 cancels ~42% of the gain — which is exactly why 15mm 45° passes here.) The
   corrected figure is **1.06–1.09** over a 75–150mm step. **Recommend a re-measure at 60°.**
2. **22mm 30° = 1.85 and 45° = 1.32 are over-corrected** — they sit *below* the gain-corrected
   values (1.978 and 1.364). At 30° the mark gap is 8mm short, which yields a 4mm step error, and
   4mm at a shallow angle is a large miss: shallow angles are the *forgiving* ones, since
   `dD/d(mark gap) = sin θ` is only 0.5 at 30°. It takes an 8mm marking error to move the step 4mm.
   **Recommend a re-measure of both, and record the step used.**

**None of this touches the 15mm calibration.** `R_outside` = 70mm ⇒ `R_cl` = 62.5mm is what the three
passing rows were scored against, and they pass on it.

### Minimum step — no conflict, and it is a second constraint, not the same one

The owner's minimum steps are the **smallest offset achievable at that angle**, which is the
quantity §1 derives as `D_min = 2·R_cl·(1 − cos θ)` — the point where the two arcs meet and no
straight is left between them.

| | geometric floor `D_min` | owner's stated minimum | headroom |
| --- | --- | --- | --- |
| 15mm 30° | 16.7 | **30** | +13.3 |
| 15mm 45° | 36.6 | **50** | +13.4 |
| 15mm 60° | 62.5 | **70** | +7.5 |
| 22mm 30° | 23.6 | **60** | +36.4 |
| 22mm 45° | 51.5 | **80** | +28.5 |
| 22mm 60° | 88.0 | **150** | +62.0 |

**Every stated minimum clears the geometric floor, so there is no conflict** — the two numbers are
answering different questions and both are right. `D_min` is where the *geometry* fails; the owner's
figure is where the *tool* fails, and it is always the larger of the two because a lever bender needs
real straight pipe between the bends to grip and to swing the arm through.

The headroom is not a constant, so it cannot be modelled as a single "minimum straight" — it is
**+13mm on the 15mm bender at 30–45°** but **+28 to +62mm on the 22mm**, which is consistent with the
larger tool needing much more room. **Treat the owner's minimum as the one to enforce and `D_min` as
the explanation of why a floor exists at all.** The Applet should refuse below the owner's figure
where one is recorded, fall back to `D_min` where none is, and show both — a user who knows the
geometric floor is 88mm and the practical floor is 150mm understands their tool better than one who
is only told "no".

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

> **ANSWERED on review — see §4A. The pipe is flipped.** The UK masterclass the repo owner supplied
> says so in as many words: *"once the first Bend's done **flip them over** and Mark just here and
> then Square them up"* — and it teaches the 360° mark for precisely that reason: *"go ahead and
> Mark all around your pipes **CU you will be flip flopping it about**"*. Arrived at independently
> of Swagelok, in UK copper practice, on the owner's own bender. The paragraph below stands as the
> record of what the *published* sources do and do not say.

**[—] No source I retrieved says "turn the pipe over" or equivalent.** BPEC's second-bend wording is
genuinely ambiguous in the extracted text, and its meaning rests on a diagram I could read only as
extracted labels ("Outside edge of pipe 'B'"). The derivation says the two outside edges are on
opposite faces; BPEC's phrasing is *consistent* with that but does not state it. **I am not going to
claim BPEC teaches the flip.** What is certain [D]: the geometry puts each bend's heel on the
opposite face, so *something* must flip — pipe, mark, or bender direction.

**Recommendation:** Swagelok's model and UK practice agree, which is the strongest position
available here: mark position **360° round**, and let the flip carry the direction. Both traditions
independently reached the same convention, and the 360° mark is what makes the flip safe — it is
why the mark survives being turned over.

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

**Minimum step `D_min = 2·R_cl·(1 − cos θ)`** — the *geometric* floor [D]:

| | 22.5° | 30° | 45° | 60° |
| --- | --- | --- | --- | --- |
| 15mm (`R_cl` 62.5) | 9.5 | 16.7 | **36.6** | 62.5 |
| 22mm (`R_cl` 88) | 13.4 | 23.6 | **51.5** | 88.0 |

> **Amended 2026-07-19 (§4B).** An earlier revision said *"the Applet must refuse below this"*. It
> must refuse below the **owner's measured minimum**, which is higher at every angle measured — 70mm
> against 62.5mm at 15mm/60°, and **150mm against 88mm** at 22mm/60°. `D_min` is where the geometry
> stops being solvable; the bender runs out of grip well before that. Refusing only at `D_min` would
> pass steps the tool cannot physically pull.

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

**An earlier revision proposed** Swagelok's p22 worked example as a regression fixture, claiming
`mark gap = R·θ + m` reproduces it *"exactly (0.00e+00)"*. **Retracted.** It never was fixture
material: p22 is an **illustrative worked example** in a US tube-fitting manual — rounded numbers,
not a specification, and not this tool's tradition. Chasing it as ground truth was the error before
the arithmetic was.

The agreement is **circular**, and §3 says why in its own text: the radius was *back-solved from*
Swagelok's tabulated adjustment. `mark gap` is algebraically `leg − gain`, so feeding their gain
back in must return their number. §3 disclosed the inversion; §7 dropped the caveat and promoted
the result to a fixture "against a manufacturer's published arithmetic", which it is not.

Fed the **real** radius (their 9/16 in former ⇒ `R` = 14.29mm, θ = 90°, leg = 63.5mm):

| | mm | (source's units) |
| --- | --- | --- |
| nominal gain from geometry — `2R·tan(θ/2) − R·θ` | **6.13** | 0.2414 in |
| Swagelok's **tabulated** adjustment | **7.94** | 5/16 in |
| Swagelok's published `P2 − P1` | **55.56** | 2.1875 in |
| our formula, `leg − nominal gain` | **57.37** | 2.2586 in |
| **mismatch** | **1.81** | 0.0711 in |

A fixture asserting 55.56mm would **encode Swagelok's rounding as if it were geometry**, and would
fail the moment anyone supplied the true radius. It tests the table, not the derivation.

**The recommendation contradicted itself on its face**, which is what made it findable: the very
next paragraph says *"Do not fixture Swagelok's or Greenlee's tables… the nominal gain for a 9/16
in radius at 90° is 0.2414 in, but Swagelok tabulates 5/16 = 0.3125 in."* The proposed fixture
**was** Swagelok's table.

**Nothing else depends on it.** The structural claim — that Swagelok's Adjustment method *is*
`leg − gain = m + R·θ` — is an **algebraic identity**, proven in §1 to 10⁻¹⁴, independent of any
radius. Only the numeric check against a published table fails, for exactly the reason the caveat
below gives. The prose sourcing in §2–§6 is unaffected.

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

**High trust — measurement of the actual tools (added 2026-07-19):**

- **Owner's bench figures for their own 15mm and 22mm benders** — multipliers and minimum steps at
  30/45/60°, with the marking method stated (both marks on straight pipe, step measured between the
  parallel legs). Scored in §4B. **This is the only source in either ticket that is a measurement of
  the tools the project is for**, and it is the reason §4A's transposition finding is now backed by a
  measurement rather than only by derivation. Three of six figures confirm the geometry to within
  BPEC's ±2mm; three conflict and are flagged for re-measure (§4B) — the conflicts point in opposite
  directions, so they are not a single systematic fault in the source.

**Medium trust — trade secondary, used deliberately and labelled:**

- [**mmplumber, *Pipe bending master class!***](https://www.youtube.com/watch?v=OiBUU_QxD3A)
  (uploaded 2025-03-28, 10:29) — added on review; **URL supplied by the repo owner and verified this
  session**. I fetched the page and confirmed title, channel and duration (629s vs the transcript's
  10:28 final timestamp); the **description is quoted from that page**. **The video itself I have not
  watched** — spoken content is quoted from the owner's transcript, so that portion is *the owner's
  testimony about a source* rather than one I verified frame by frame. Demonstrates on a **Monument**
  lever bender in copper/MLCP.

  Its value: the **only** evidence found that a UK offset convention exists at all (§4A); confirms
  the flip and the 360° mark from inside UK practice; sources #4's 70mm; and its description gives
  the only cross-bender evidence on the 70mm. Its multipliers are **transposed at 30° and 60°**,
  provable from the transcript's own full cross — so it is cited as *what the trade teaches*,
  explicitly **not** as authority for the numbers.

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

- ~~Any UK source teaching an offset multiplier, cosecant, or distance-between-bends formula.~~
  **RESOLVED on review — and this document had it wrong.** A UK plumber's masterclass (§4A, owner-
  supplied transcript) teaches the multiplier method explicitly. The BPEC evidence was sound but the
  inference from it was not: **"the awarding body publishes no formula" is not "the trade uses no
  formula."** Reading only published syllabus material could not have found this, which is the
  methodological lesson of this ticket.
- ~~Any explicit instruction, in any source, to turn the pipe over between the two bends.~~
  **RESOLVED on review** — *"once the first Bend's done flip them over"* (§4A).
- What Greenlee's "center-to-center" mark actually references. **Still unsourced.**
- **Where the Monument bender's "just after the arm" datum sits** relative to the tangent point —
  new, and the load-bearing unknown (§4A). It decides whether #4's 70mm is `R_outside` or a datum
  offset. **Partially answered by the author's description** — *"The 70 mm measurement does also work
  on your standard bender"* [S], which argues the 70mm is a former radius rather than a Monument
  artifact — but that is his claim, not a measurement, and every check ever made was at 90°, where
  the two readings agree by construction. **Only #17's 45° test can separate them.**

## Open questions for the Applet

1. **Which sequencing does the Applet assume the user will follow?** This is the offset's version of
   #4's reference-surface decision, and it is load-bearing in exactly the same way. `mark gap` is
   right for mark-both-then-bend; `D/sin θ` is right for bend-then-measure. **The Applet cannot emit
   one number without naming the method.** Suggest: emit both, always, side by side.
2. **Should the Applet actively recommend BPEC's drawing method over its own arithmetic below 30°?**
   The gain there (0.32–1.08mm) is inside the ±2mm tolerance, so *gain correction* buys nothing. #4
   reached the same conclusion for 90° bends.

   > **Reframed on review (§4A).** The "honest scope is steep angles and larger pipe" conclusion was
   > drawn when the gain was the only error in view. It isn't. **The multiplier in circulation is
   > transposed at 30° and 60°** — a **31mm** error at 30° and **64mm** at 60°, against a ±2mm
   > tolerance. That dwarfs the gain by an order of magnitude, and it is *worst* at the shallow
   > angles where the gain argument said the tool was pointless. The Applet's business case is not
   > "correct a 2.7mm gain the trade tolerates"; it is **"emit a multiplier that is not
   > transposed"** — and it earns its place across the whole range, not at the edges. → #18.
3. **Is `mark gap` even the right headline Output**, or is the setting-out **drawing** the deliverable
   (per #4's conclusion) with the numbers as annotations on it? BPEC's entire method is "the drawing
   is the template". Rendering an accurate SVG the user can print and lay pipe on may beat any number.
4. **Confirm the flip convention against the physical bender.** One offset pulled in the actual
   Monument bender settles Q5 in five minutes and no reading will.
5. **Should the Applet emit a multiplier at all?** [Added 2026-07-19, §4B.] The multiplier is
   `cosec θ − gain/D` — a **function of the step**, not a constant. At 30° it is flat enough that 2.0
   is fine; at 60° it moves 0.07 across a normal working range. Emitting a single number reintroduces
   exactly the error the Applet exists to remove. **Suggest: emit the mark gap in millimetres for the
   step the user actually entered, and show the multiplier only as a derived sanity-check figure,
   labelled with its step.**
6. **Re-measure three figures** [Added 2026-07-19, §4B]: 15mm/60° (recorded 1.2, the trade table's
   rounding; geometry says 1.06–1.09), and 22mm/30° and 45° (recorded 1.85 and 1.32, both *below* the
   gain-corrected 1.978 and 1.364). Record the step used alongside each — without it a multiplier
   cannot be scored, which is the lesson of this section.
