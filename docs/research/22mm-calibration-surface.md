# 22mm calibration: which reference surface, and what number?

Research for [#22](https://github.com/andyalexander/workshop-helper/issues/22). Raised by
[#17](https://github.com/andyalexander/workshop-helper/issues/17)'s bench measurement, which
falsified the reference-surface assumption [#4](https://github.com/andyalexander/workshop-helper/issues/4)
recorded.

**Claim tags:** `[S]` sourced — a passage retrieved this session says it, quoted verbatim.
`[D]` derived — arithmetic from `[S]` facts, reversed in-session. `[—]` unsourced — nothing
retrieved this session establishes it.

---

## Headline

**BPEC's `4 × OD` is explicitly a centreline radius `[S]`, and BPEC's own figure for the
22mm *outside* radius is 99mm `[S]`.** So the calibration table's `22 = 99` is not a
derivation gone wrong — it is BPEC's published outside radius, copied verbatim from the same
paragraph that gives 88mm as the centreline. On the bench-established centreline footing the
BPEC-sourced figure is **88.0mm** `[D]`.

**But changing 99 → 88 may make the Applet's answer worse, not better.** The one bender
anyone has measured does *not* bend at `4 × OD`: the 15mm Monument measured **70mm**
centreline where BPEC predicts 60mm — **+16.7%** `[D]`. If the 22mm former is over-radiused
in the same proportion, its centreline is ~102.7mm `[D]`, and 88.0 is **14.7mm** short at 90°
— a *larger* error than the 11mm the ticket set out to fix, in the opposite direction.

The honest answer to "what is the 22mm figure?" is **unknowable from sources**. What *is*
now settled is the surface.

---

## 1. Does BPEC quote `4 × OD` as centreline, outside, or former/groove radius?

**Centreline. Stated in terms, with worked arithmetic for both pipe sizes. `[S]`**

Source: *BPEC — Essential Plumbing Skills: Copper Pipe (2019 v2)*, §"Setting out for bends and
bending", retrieved this session from
<https://bpec.org.uk/wp-content/uploads/2019/11/BPEC-Essential-Plumbing-Skills-Copper-Pipefinal-version.pdf>
(PDF, 22pp, HTTP 200, text extracted with `pdftotext -layout`).

Verbatim, in full, unedited:

> Most benders bend at a radius of 4 x the diameter of the pipe so: -
>
> For 15mm pipe it will be 15mm x 4 = 60mm radius to centre line.
>
> The outside radius will be 60mm + 7.5mm = 67.5mm.
>
> The inside radius (nearest the former) will be: - 60mm – 7.5mm (half the diameter) = 52.5mm.
>
> For 22mm it will be: - 4 x 22mm = 88mm to the centre line. The inside radius (nearest the
> former) will be: - 88mm – 11mm (half the diameter) = 77mm and the outside radius will be
> 88mm + 11mm = 99mm.

Three things fall out of that one paragraph:

1. **`4 × OD` is "radius to centre line"** — BPEC's own words, not an inference `[S]`.
2. **99mm is BPEC's *outside* radius for 22mm** `[S]`. It is not something #4 computed; it is
   printed. The table's `22 = 99` is BPEC's number read off the wrong line.
3. **The former/groove radius is a fourth quantity BPEC calls "inside radius (nearest the
   former)"** — 77mm for 22mm, 52.5mm for 15mm `[S]`. So all three surfaces are named and
   distinguished, and `4 × OD` is unambiguously none of the other two.

Corroborated independently in the second BPEC document, *Copper Skills: Producing a 90° bend /
an offset / a passover*, retrieved this session from
<http://bpec.org.uk/wp-content/uploads/2016/01/BPEC-Copper-Bends.pdf> (HTTP 200):

> 2. To set out, start as above then strike an arc from the centre of the pipe at 4 times the
> diameter as the radius, as shown: For 22mm 4 X dia = 88mm For 15mm 4 X dia = 60mm

("from the centre of the pipe" — the same claim, phrased as a drawing instruction) `[S]`, and
in the passover sheet, which strikes the inner and outer arcs and names them:

> 3. Striking through the two arcs - one at 52.5mm and 67.5mm if using 15mm pipe, or 77mm and
> 99mm for 22mm pipe as shown.

with the diagram labelled `R77` / `R99` and `22mm Pipe Inside Radius for = (88mm - 11mm)` `[S]`.

**Verdict on Q1: settled, sourced, quoted.** No inference was needed. `4 × OD` is a centreline
radius; 99 is the outside radius of the same bend.

### Reverse-check of BPEC's own arithmetic `[D]`

| BPEC statement | Check | |
|---|---|---|
| 15mm: `4 × 15 = 60` centreline | 60 | ✅ |
| 15mm outside `60 + 7.5 = 67.5` | `OD/2 = 7.5` | ✅ |
| 15mm inside `60 − 7.5 = 52.5` | | ✅ |
| 22mm: `4 × 22 = 88` centreline | 88 | ✅ |
| 22mm inside `88 − 11 = 77` | `OD/2 = 11` | ✅ |
| 22mm outside `88 + 11 = 99` | | ✅ |

Internally consistent, and `R_outside − R_centreline = OD/2` holds in all six figures.
#22's diagnosis of the 99 — `4×OD + OD/2` — is arithmetically identical to BPEC's printed
outside radius `[D]`. Same number, different story: not a conversion an agent performed, but a
line copied from the wrong sentence. The correction is the same either way.

---

## 2. Given (1), what is the correct 22mm centreline figure?

**On BPEC's authority: 88.0mm `[S]` for the *convention*. For the owner's actual 22mm
bender: unknown, and 88.0 is probably not it `[D]`.**

The ticket asks whether "88.0 is only right if BPEC's figure is already a centreline." It is
a centreline. But that makes 88.0 correct *as a transcription of BPEC*, which is a weaker
claim than "correct for the tool in the shed" — and #17 is direct evidence that those differ.

### The premise the 15mm bench measurement falsified

BPEC hedges its own rule: **"*Most* benders bend at a radius of 4 x the diameter"** `[S]`.
The Monument 15mm is not one of them.

| | BPEC `4 × OD` | Bench (#17) | Δ |
|---|---|---|---|
| 15mm `R_centreline` | 60.0mm `[S]` | **70.0mm** `[S]`, owner's measurement | **+10.0mm, +16.67%** `[D]` |
| `R_c / OD` | 4.000 | **4.667** `[D]` | |

Reverse-checked: `70 / 15 = 4.6667`; `4.6667 × 15 = 70.0` ✅. `(70 − 60) / 60 = 0.1667` ✅.

So for the only bender in this project that has ever been measured, BPEC's rule is wrong by
16.7%. Adopting 88.0 for 22mm is adopting, for an untested bender, a rule already shown to
fail on the tested one.

### Three candidate 22mm figures, none of them measured

Since `setback(90°) = R_c × tan(45°) = R_c` exactly `[D]`, each candidate radius *is* its own
90° setback, which makes the spread easy to read:

| Model | 22mm `R_c` | Basis | Tag |
|---|---|---|---|
| BPEC convention | **88.00mm** | `4 × 22`, printed | `[S]` for the convention |
| Constant *ratio* — 22mm former over-radiused like the 15mm | **102.67mm** | `4.6667 × 22` | `[—]` model, `[D]` arithmetic |
| Constant *offset* — same +10mm as the 15mm | **98.00mm** | `88 + 10` | `[—]` model, `[D]` arithmetic |

Reverse-checks: `4.6667 × 22 = 102.667` ✅ (and `102.667 / 22 = 4.667` ✅);
`88 + 10 = 98` ✅.

**Read that table carefully, because it inverts the ticket's expectation.** The current stored
value is **99.0**. Both non-BPEC models land at 98.0–102.7 — i.e. *within 0.3–3.7mm of the
number we are proposing to delete* — while the "corrected" 88.0 is 10–14.7mm away from both.

This is a coincidence, not a justification: 99 is right-ish for entirely the wrong reason (it
is an outside radius that happens to sit near where an over-radiused Monument centreline might
be). But it means **the fix is not risk-free**. Swapping 99 → 88 trades a known
wrong-surface error for an unknown wrong-magnitude one, and the second could be bigger:

| Stored | If truth is 88.0 (BPEC former) | If truth is 102.67 (ratio model) |
|---|---|---|
| 99.0 (today) | 11.0mm out `[D]` | 3.7mm out `[D]` |
| 88.0 (proposed) | 0mm | **14.7mm out** `[D]` |

`99 − 88 = 11 = OD/2` ✅ — confirming #22's stated 11mm error under the BPEC-former
assumption. `102.67 − 88 = 14.67` ✅. All well outside BPEC's stated ±2mm.

### Why this cannot be settled

- **No 22mm bender is available to measure.** #17's method — the only method that has ever
  produced a trustworthy number here — is unavailable. Stated in #22 and reconfirmed.
- **Monument publishes no former radius, for either size.** Searched this session: Monument's
  own product page states only a *qualitative* comparison —
  > "The Monument Masters 1215K-XV, 1315-XVE, 1315Longarm-XVL, 1222G-XXII and
  > 1322Extended-XXIIE create similar bend radiuses to a Monument 2600K combi bender; in fact
  > the 1222G has a slightly tighter radius that the 2600K combi bender"
  <https://monument-tools.com/2020/06/24/pipe-bender-15mm-22mm/> `[S]`.
  No figure in mm anywhere on the page. **This is itself a finding**: Monument's own words
  confirm that *different Monument models differ in radius*, so even a measured 22mm figure
  would be a figure for one specific tool, not for "the 22mm Monument".
- **Retail listings carry no radius either** (search across Screwfix, Axminster, Toolstation-
  class listings returned capability and former-marking detail — "formers are marked with
  bending angles of 30, 45, 60 & 90°" — but no radius in mm) `[S]`.

**Verdict on Q2: the surface is settled; the magnitude is not, and is not settleable from
sources.** 88.0 is the correct *centreline reading of BPEC*. Whether it is the correct
*calibration* for a bender nobody owns or has measured is unknown, and the one relevant data
point in this project argues against it.

**Recommendation.** Store **88.0** and name it honestly. It is the only figure with a source
behind it, and shipping a number tagged `[S]` beats shipping one tagged `[—]`. But it must
not be shipped *looking like* the 70.0 — see Q3. The 102.67 and 98.00 models are speculation
and should be recorded as such in this document only, never in the Manifest.

---

## 3. Does a published textbook default belong in the same table as a bench-measured figure?

**No — not without a provenance field. #15's own discriminator disqualifies it, and #17
supplied the evidence.**

#15's test for what counts as calibration:

> **must the owner correct this for their own kit?**

For 15mm, that question has now been answered empirically, and the answer is **yes, by 10mm**
`[D]`. The `4 × OD` convention did not survive contact with the bender. That is not a
hypothetical about the 22mm row; it is a measured demonstration that BPEC's convention and the
owner's kit disagree by 8× the trade tolerance.

So the two rows are not two calibrations. They are:

| | 15mm = 70.0 | 22mm = 88.0 |
|---|---|---|
| What it is | a measurement of a specific tool | a drawing convention for "most benders" |
| Provenance | owner's bench, #17 `[S]` | BPEC, printed `[S]` |
| Correction status | **corrected** — this *is* the correction | **uncorrected placeholder** |
| Known to describe the owner's kit? | yes, tested at 45° and 90° | **no, and the analogous claim failed at 15mm** |

They answer #15's discriminator differently, which by #15's own logic makes them different
kinds of thing.

**But they cannot simply be separated into two tables.** #15 hands the Host a validation rule
with teeth:

> the calibration key set and the keying `choice`'s value set must match exactly. A former
> with no pipe size, or a pipe size with no former, is a malformed Manifest

Deleting the 22mm row therefore either breaks the Manifest or forces 22mm out of the pipe-size
`choice` — removing a size the owner physically owns a bender for. Neither is acceptable.

**Recommendation: keep one table, add provenance to the row.** Something like:

```toml
[calibration.values.15]
r_centreline = 70.0
provenance = "measured"     # owner's bender, bench-verified 2026-07 (#17)

[calibration.values.22]
r_centreline = 88.0
provenance = "convention"   # BPEC 4 × OD; NOT measured on this bender
```

This is the smallest change that stops the table lying by omission. It also gives #9's
"show your working" Result page the one thing it needs: the ability to print *"this figure is
a published convention for your pipe size, not a measurement of your bender — measure your
former and correct it"* on the 22mm result and not on the 15mm one. A Result that silently
presents a `[—]`-grade default in the same typeface as a bench-verified constant is exactly
the failure mode this ticket exists to close.

Two further notes for #15/#9:

- **The 15mm row is the proof that `provenance` earns its place.** Had the table carried it
  from the start, #4's 22mm entry would have been visibly flagged as underived rather than
  inheriting the 15mm row's credibility.
- **A `provenance = "convention"` row is a standing invitation to correct it**, which is the
  behaviour #15 wants from calibration in the first place. It makes the write-back seam (#7)
  do useful work rather than being a theoretical concern.

**Verdict on Q3: it belongs in the table only if the table can say what it is. Add a
provenance field; do not silently mix grades of evidence.**

---

## 4. What should the field be named?

**`r_centreline`.** `[D]` from the sourced facts above.

Constraints the name must satisfy:

1. **It must state its reference surface.** #4's rule — *"pinning the reference surface is the
   whole ballgame"* — and this ticket is the second time an unstated surface has cost 7.5–11mm.
2. **`r_outside` is now false.** #17: the setback is measured back to *"where the centre line of
   the vertical pipe will be"* `[S]`, and 70.0 is the distance to that centreline. Leaving the
   name would have the next reader compute `R_c = 70 − 7.5 = 62.5` and land 7.5mm out — the
   precise error being fixed here, re-created by a name.
3. **A bare `bend_radius` or `radius` is not acceptable** — it is the unstated-surface form,
   and BPEC's own paragraph gives *three* radii for one bend (52.5 / 60 / 67.5 for 15mm) `[S]`.
   "Radius" without a surface is genuinely ambiguous in this domain, in the primary source.

| Candidate | Verdict |
|---|---|
| `r_outside` | **wrong** — states a surface, states the wrong one |
| `bend_radius`, `radius`, `r` | **rejected** — no surface; BPEC names three radii per bend |
| `former_radius` | **rejected** — BPEC's "inside radius (nearest the former)" is a *different* number (77mm for 22mm) `[S]`; this name would read as 77, not 88 |
| `r_centreline` | **recommended** — names the surface the bench established, matches BPEC's own phrase "radius to centre line" `[S]` |
| `r_centreline_mm` | acceptable if the project wants units in names; see ADR-0006 (unit is a display label) — probably not |

Note the general form the name must support, from #17:

> `setback = R_c × tan(θ/2)`, measured back to the **vertex of the two centrelines**

`r_centreline` is the radius; the *target the user aims at* is the centreline vertex. The
Applet must state the second as an instruction on the Result — a field name alone cannot carry
it. That is a #9 obligation, not a naming one.

**Verdict on Q4: `r_centreline`, plus a sibling `provenance` field per Q3.**

---

## Retrieved this session

| Source | URL | Status |
|---|---|---|
| BPEC — Essential Plumbing Skills: Copper Pipe (2019 v2) | <https://bpec.org.uk/wp-content/uploads/2019/11/BPEC-Essential-Plumbing-Skills-Copper-Pipefinal-version.pdf> | ✅ 200, 22pp, full text extracted |
| BPEC — Copper Skills: 90° bend / offset / passover | <http://bpec.org.uk/wp-content/uploads/2016/01/BPEC-Copper-Bends.pdf> | ✅ 200, full text extracted (some CAD glyph warnings; the quoted passages extracted cleanly) |
| Monument Tools — "Pipe Bender 15mm 22mm" | <https://monument-tools.com/2020/06/24/pipe-bender-15mm-22mm/> | ✅ 200, read; **no radius in mm** |
| Retail listings (Screwfix, Axminster, and others via search) | various | ✅ read; **no radius in mm** |

All quotations above were read out of the extracted text of the documents named, this session.

## Attempted and NOT retrieved

- **Any published former/groove radius for the Monument 22mm bender (1222G / 2600K / any
  model).** Searched Monument's own site and retail listings. Monument publishes only a
  qualitative comparison. **This is the single fact that would settle Q2, and it does not
  appear to be public.**
- **Any manufacturer statement, from anyone, giving a hand-bender former radius in mm.** Not
  found for Monument. Not sought exhaustively across other UK brands, since a Rothenberger
  figure would not calibrate a Monument.
- **BS EN 1057, or any British Standard specifying minimum bend radius for copper tube.**
  Not retrieved this session — standards are paywalled. Nothing in this document rests on one.
- **Swagelok and Greenlee.** Read in #4/#13 but **not re-retrieved this session**, so per the
  provenance rules nothing here is cited to them, and no claim above depends on them.
- **A 22mm bench measurement.** Impossible — no 22mm bender available. This is the reason
  Q2 terminates in "unknowable" rather than in a number.

## "No source says this"

- **No source retrieved this session states the actual bend radius of any Monument bender.**
  The 15mm figure of 70.0mm rests entirely on the owner's bench measurement (#17), and the
  22mm figure rests on nothing but a convention BPEC itself hedges with "Most".
- **No source retrieved this session relates BPEC's `4 × OD` convention to any specific
  manufacturer's tool.** BPEC describes what "most benders" do; it does not certify any of them.
- **No source retrieved this session supports either the constant-ratio (102.67mm) or
  constant-offset (98.00mm) model** for extrapolating the 15mm bender's over-radius to 22mm.
  Both are listed above solely to size the risk of adopting 88.0, and are tagged `[—]`. Neither
  should reach the Manifest.

## Arithmetic reverse-checked in this document

`4×15=60` ✅ · `60+7.5=67.5` ✅ · `60−7.5=52.5` ✅ · `4×22=88` ✅ · `88−11=77` ✅ ·
`88+11=99` ✅ · `70/15=4.6667` ✅ · `4.6667×22=102.667` ✅ · `102.667/22=4.667` ✅ ·
`(70−60)/60=16.67%` ✅ · `88+10=98` ✅ · `99−88=11=OD/2` ✅ · `102.67−88=14.67` ✅ ·
`tan(45°)=1 ⇒ setback(90°)=R_c` ✅
