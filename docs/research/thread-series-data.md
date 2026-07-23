# Thread series and reference data for the thread finder

Research resolving [issue #25](https://github.com/andyalexander/workshop-helper/issues/25).
Date: 2026-07-20.

All sources in this document were opened and read **in this session**. Every claim carries a
tag: **[S]** sourced (a retrieved passage says it), **[D]** derived (arithmetic from a retrieved
source, shown), **[—]** unsourced (nothing retrieved supports it). Per #22, a claim is graded
*against the question asked* — a general statement is **[—]** evidence for any specific row.

---

## RECOMMENDATION

**Ship seven series, not six. Include BSP — but as a clearly-labelled *pipe* series.**

| Series | Ship it? | Data retrieved this session? | Source quality |
| --- | --- | --- | --- |
| ISO metric coarse | **Yes** | **Yes, complete** | **Primary** (ISO 261 preview) |
| ISO metric fine | **Yes** | **Yes, complete** | **Primary** (ISO 261 preview) |
| UNC | **Yes** | **Yes, complete** | **Primary** (NBS H28-1969, US Gov, free) |
| UNF | **Yes** | **Yes, complete** | **Primary** (NBS H28-1969, US Gov, free) |
| BSW | **Yes** | Yes — but **secondary** | Gage manufacturer chart citing BS 84 |
| BSF | **Yes** | Yes — but **secondary** | Gage manufacturer chart citing BS 84 |
| BA | **Yes** | Yes — **secondary + independently verified** | Chart citing BS 93, checked against NBS H28-1944 formulas |
| **BSPP (G-series)** | **Yes** | **Yes, complete** | **Primary** (ISO 228-1:2000 preview) |
| BSPT (R-series) | Defer | No | — |

**Why BSP belongs, stated as a design argument, not a taxonomy argument.** #25 is right that BSP
is a pipe designation and not a fastener thread — ISO 228-1's own scope says these threads are
"*intended for the mechanical assembly of the component parts of fittings, cocks and valves*"
and are "*not suitable as jointing threads*" **[S]**, §1. But the Applet's input is a **measured
diameter and pitch**, and the user cannot know a priori what they are holding. That produces a
concrete, silent failure:

> A G 1/2 male thread measures **20.955 mm major diameter, 1.814 mm pitch** **[S]**
> (ISO 228-1:2000 Table 1). Nothing in "1/2" predicts 20.955 mm.

With BSP excluded, the finder's nearest candidate for that measurement would be something in the
M20–M22 or 3/4" BSF neighbourhood, offered confidently and wrongly. **The cost of omitting BSP is
a wrong answer with no warning; the cost of including it is one extra column of context.** Include
it, label the row `BSPP (G) — pipe thread, not a fastener`, and suppress its tap-drill column
(see §3). Note the size designation is nominal *bore*, not diameter — the row must never be
rendered in a way that invites the user to read "G 1/2" as half an inch across.

**BSPT (R-series) is deferred, not rejected.** It is tapered, so a single measured "diameter" is
not well defined without also knowing where along the thread it was measured. That is a genuinely
different input model. No data for it was retrieved this session.

**Tap drill: emit the published stocked drill, never the formula. Source it to ISO 2306.**
See §3 — this is the strongest single result of the research, because ISO 2306:1972 states the
`major − pitch` rule *and* tabulates the stocked drills, so both halves of #25's worry come from
one retrieved document and cannot be silently mixed.

**Ranking is the owner's call and this document does not make it.** See §4.

**Nothing in §5's tables may ship without a human spot-check against the source page images.**
The OCR of every scanned source used here contains visible errors (§6). This is #22's failure
mode with a hundred places to hide.

---

## 1. Which series

### 1.1 The floor proposed in #25 is right

ISO metric coarse + fine, BSW, BSF, BA, UNC, UNF. Nothing retrieved contradicts this, and two
sources actively support the imperial-legacy framing:

> "The Whitworth screw thread form is not commonly used for nuts and bolts because it has mostly
> been replaced by the Unified-Series and Metric-Series screw threads."
> — Gage Crib Worldwide, *British Standard Whitworth Screw Thread Form*,
> <https://www.ring-plug-thread-gages.com/ti-bs-Whitworth-screw-thread-form.htm>, retrieved 2026-07-20 **[S]**

> "British Association Standard Screw Threads are used mainly for instruments and clocks. The
> BA-series screw threads should not be used for new designs. Instead use the M-series screw
> threads."
> — Gage Crib Worldwide, *BS 93 BA Screw Threads Data Charts*,
> <https://www.ring-plug-thread-gages.com/PDChart/BA-thread-data.html>, retrieved 2026-07-20 **[S]**

Both are statements that these series are **legacy**, which is precisely the case for including
them in a *finder* (you meet them on old kit) and against including them in a *selector*.

### 1.2 BSP — what the sources actually say

The claim "BSP is a pipe designation, not a fastener thread" is **half** supported and the other
half is contradicted by the primary source. ISO 228-1:2000 §1:

> "This part of ISO 228 specifies the requirements for thread form, dimensions, tolerances and
> designation for **fastening pipe threads**, thread sizes 1/16 to 6 inclusive. Both internal and
> external threads are parallel threads, **intended for the mechanical assembly of the component
> parts of fittings, cocks and valves, accessories, etc.**
>
> These threads are **not suitable as jointing threads** where a pressure-tight joint is made on
> the thread. If assemblies with such threads must be made pressure-tight, this should be effected
> by compressing two tightening surfaces outside the threads, and by interposing an appropriate
> seal."
> — <https://cdn.standards.iteh.ai/samples/33777/842b7c5409454ceba69c7dad9c308be1/ISO-228-1-2000.pdf>,
> retrieved 2026-07-20 **[S]**

So ISO's own word for the G-series is **"fastening pipe threads"** — it is a *fastening* thread
whose sealing is done elsewhere. That is a stronger case for inclusion than #25 assumed. The
tapered variant is the one that seals on the thread, and it is explicitly a different standard:

> "NOTE 1 For pipe threads where pressure-tight joints are made on the threads, see ISO 7-1." **[S]**

The lineage from the British standards is stated by the gage manufacturer, which is corroborating
rather than primary:

> "British Standard Pipe Taper (BSPT) which is now referred to as the R-Series screw thread and is
> defined in ISO 7; EN 10226; BS 21 and formerly in DIN 2999. British Standard Pipe Parallel (BSPP)
> which is now referred to as the G-Series screw thread and is defined in ISO 228 and formerly in
> BS 2779." — Gage Crib, retrieved 2026-07-20 **[S]**

**The practical wrinkle, stated plainly.** A workshop user measuring an unknown male thread has a
caliper reading and a pitch reading. Nothing in those two numbers announces "this is a pipe
thread". The BSP major diameters are *not* near any fastener series' nominal sizes — G 1/4 is
13.157 mm, G 3/8 is 16.662 mm, G 1/2 is 20.955 mm **[S]** — so they sit in the gaps between M12/M14,
M16/M18 and M20/M22. A finder without them does not say "no match"; it says "M14 × 1.5, close
enough", which is worse. **[D]**

---

## 2. Sources, per series

### 2.1 What was retrieved, and its standing

| Series | Retrieved source | Type | Complete? |
| --- | --- | --- | --- |
| ISO metric coarse + fine | **ISO 261:1998 Table 2** (iTeh free preview PDF) | **Primary standard** | Yes, 1–300 mm |
| ISO metric selected sizes | **ISO 262:1998 Table 1** (iTeh free preview PDF) | **Primary standard** | Yes, 1–64 mm |
| ISO metric basic dimensions | **ISO 724:1993 Table 1** (iTeh free preview PDF) | **Primary standard** | Yes, but OCR-damaged |
| Metric / UNC / UNF / BSPP tap drills | **ISO 2306:1972 Tables 1–5** (iTeh free preview PDF) | **Primary standard** | Yes |
| UNC / UNF | **NBS Handbook H28 (1969) Part I, Table 2.7** (NIST, US Gov) | **Primary, public domain** | Yes |
| BSW / BSF | Gage Crib Worldwide charts, cited to BS 84 | Manufacturer engineering data | Yes (see caveats) |
| BSW / BSF (form, tpi) | **NBS Handbook H28 (1944) Tables 149–150** (NIST, US Gov) | **Primary, public domain** | Yes, but *Truncated Whitworth* — see 2.4 |
| BA | Gage Crib Worldwide chart, cited to BS 93:2008 | Manufacturer engineering data | Yes, 0–16 BA |
| BA generating formulas | **NBS Handbook H28 (1944), Foreign Thread-Form Standards** | **Primary, public domain** | Formulas only |
| BSPP (G) | **ISO 228-1:2000 Table 1** (iTeh free preview PDF) | **Primary standard** | Yes, 1/16–6 |

**On the iTeh previews.** These are the publisher-side free sample PDFs, watermarked
"iTeh STANDARD PREVIEW (standards.iteh.ai)" and footed "Price based on N pages". For the five
short standards used here the preview happens to contain the **entire normative table**. This is
free sample material distributed by an ISO reseller, not a scraped or leaked copy — a distinction
worth recording, because a pirated full-text copy of ASME B1.13M was found during this research and
was **deliberately not used** (§6).

### 2.2 ISO metric — fully sourced, primary

ISO 261:1998 §5 sets the selection rules the Applet should honour when ranking:

> "5.1 Choose, for preference, diameters in column 1 of table 2 and, if necessary, in column 2 and
> then in column 3. […] Pitches shown in parentheses are to be avoided as far as possible.
>
> 5.2 The words 'coarse' and 'fine' are given in order to conform to usage. No concept of quality
> shall, however, be associated with these words. It shall be understood that the 'coarse' pitches
> are the largest metric pitches used in current practice." **[S]**

Two things follow directly:

1. **The 1st/2nd/3rd-choice column is a ranking signal the standard itself provides** **[S]**. A
   finder that offers M26 × 1,5 (3rd choice) ahead of M24 × 1,5 (1st choice) at equal numeric
   distance is arguably wrong by the standard's own preference order. This is an input to §4.
2. **"coarse" and "fine" are labels, not a quality ordering** **[S]** — so the table must not sort
   coarse above fine on principle.

Also retrieved, and useful as a sanity bound:

> "5.4 If screw threads finer than those appearing in table 2 are found necessary, only the
> following pitches shall be used: 3 mm; 2 mm; 1,5 mm; 1 mm; 0,75 mm; 0,5 mm; 0,35 mm; 0,25 mm;
> 0,2 mm" **[S]**

### 2.3 UNC / UNF — fully sourced, primary, free

NBS Handbook H28 (1969) Part I, Table 2.7 *Unified standard screw thread series*, retrieved from
<https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1969p1.pdf>. The table's columns are
"Nominal size and basic major diameter" (inch) against "Threads per inch — Series with graded
pitches: Coarse UNC / Fine UNF" **[S]**. This is a US Government publication and is free and
in the public domain; the OCR of this particular table is clean.

### 2.4 BSW / BSF — the honest position

**No primary British source was retrieved.** BS 84 is paywalled (§6). What was retrieved:

- **NBS H28 (1944) Tables 149 and 150**, titled *"Screw threads of Truncated Whitworth form,
  coarse thread series"* and *"…fine thread series"* **[S]**. These are on pp. 249–252 of the
  scanned PDF (PDF pages 261–262). They carry Whitworth **sizes and threads per inch** — but the
  major-diameter columns are for the **American Truncated Whitworth** form, an American variant
  whose major diameter is deliberately *not* the Whitworth basic major diameter:

  > "TWC—Truncated Whitworth, coarse thread series / TWF—Truncated Whitworth, fine […]
  > These threads are British Standard Whitworth threads, special series." **[S]** (H28-1944 p.241–243)

  So H28-1944 is a **good source for BSW/BSF sizes and tpi** and a **bad source for basic major
  diameter**. Reading its major-diameter column as "the BSW major diameter" is exactly the #22
  error. Recorded here so nobody does it.

- **Gage Crib Worldwide's BSW and BSF charts**, headed "Whitworth Coarse Thread BS 84" and
  "Whitworth Fine Thread BS 84" — full tables of major diameter, pitch, tpi, pitch diameter, minor
  diameter and tap drill (§5.3). Manufacturer engineering data citing the standard. **Secondary.**

### 2.5 BA — secondary data, but independently verified against a primary formula

The Gage Crib BA chart is cited to BS 93:2008 (paywalled, §6). But NBS H28 (1944) reproduces the
BA **generating formulas**, which lets the whole table be checked without the standard:

> "In 1878 the Horological Section of the Geneva Society of Arts recommended a system of screw
> threads […] The sizes were designated by consecutive numbers, n, the pitch, p, corresponding to
> any given size being given by the formula: **p = 0.9ⁿ**, and the major diameter, D, corresponding
> to any pitch, being given by the formula: **D = 6p^(6/5)**"
> — NBS H28 (1944), *Foreign Thread-Form Standards*, p.264–265,
> <https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1944.pdf>, retrieved 2026-07-20 **[S]**

**OCR caveat, stated because it matters:** the exponent renders in the OCR text as `D -&p 6/fe`.
The reading `D = 6p^(6/5)` is **[D]**, recovered by fitting, not read cleanly off the page. It fits
all 17 rows of the BA table to the standard's own rounding (§7), which is strong evidence but is
still a reconstruction. **A human must confirm the exponent off the page image before this is used
as a check.**

The same page also fixes the standard reference:

> "British Standards Institution Standard No. 93-1919.— British Association (B.A.) screw threads
> with tolerances for Nos. 0 to 15 B. A. (Add. August 1940.)" **[S]**

### 2.6 BSPP — fully sourced, primary

ISO 228-1:2000 Table 1, columns 1–7 (designation, threads per 25,4 mm, pitch *P*, thread height
*h*, major *d=D*, pitch *d₂=D₂*, minor *d₁=D₁*) — retrieved in full (§5.6). The symbol definitions
are also given, which makes the table self-checking:

> "D₁ = D – 1,280 654 P = d₁; minor diameter of the internal thread
> D₂ = D – 0,640 327 P = d₂; pitch diameter of the internal thread" **[S]**

Note this is the **Whitworth 55° form**, so the coefficients differ from the metric 60° form —
another reason the BSP rows must not share a formula path with the fastener rows.

---

## 3. Tap drill sizes

### 3.1 The finding: ISO 2306 settles this, and it says both things at once

The single most useful retrieval of this session. **ISO 2306:1972 — *Drills for use prior to
tapping screw threads*** — states the formula *and* tabulates the stocked drills, in the same
document:

> "This International Standard specifies the sizes of drills to be used prior to tapping parallel
> screw threads of normal length of engagement, **the drill diameter being approximately equal to
> the nominal diameter of the thread minus the pitch**. Drill sizes are given for the following
> threads: 1) ISO metric threads (coarse and fine pitch series): Tables 1 and 2. 2) ISO inch
> threads (UNC and UNF): Tables 3 and 4. 3) Pipe threads: Tables 5 and 6."
> — ISO 2306:1972 §1,
> <https://cdn.standards.iteh.ai/samples/7135/5bef5f85e78040d6b848307ffd62d83f/ISO-2306-1972.pdf>,
> retrieved 2026-07-20 **[S]**

And it is candid about why the tabulated number is not the formula's number:

> "The diameter of a hole produced by a drill depends to some extent upon the degree of accuracy to
> which the drill point is ground, the material being drilled, the lubricant used, and the
> alignment, feed and speed of the operation. When tapping relatively soft material, there is a
> tendency for the material to be squeezed down towards the root and in such cases the minor
> diameter of the tapped hole may become smaller than the diameter of the drill used. […] The
> larger the drilled hole, within the relevant minor diameter tolerance, the more economical
> tapping becomes and the risk of tap breakage is reduced. With the foregoing points in mind, the
> tables have been prepared as a guide to drilling prior to conventional tapping. However, it is
> realised that users may find it beneficial to choose their own drill diameters for certain
> applications. Even in these instances, stocked diameter drills should be used whenever possible." **[S]**

### 3.2 How far apart are the formula and the table? Measured, not guessed

Taking ISO 2306 Table 1 (coarse series, M1–M56) as transcribed in §5.2, and computing `D − P` for
every row **[D]**:

| Rows checked | `D − P` equals the tabulated drill | Exceptions |
| --- | --- | --- |
| 37 | **33** | **4** |

| Size | `D − P` | ISO 2306 drill | Difference |
| --- | --- | --- | --- |
| M4,5 × 0,75 | 3,75 | **3,70** | −0,05 |
| M8 × 1,25 | 6,75 | **6,80** | +0,05 |
| M9 × 1,25 | 7,75 | **7,80** | +0,05 |
| M12 × 1,75 | 10,25 | **10,20** | −0,05 |

**[D]** — arithmetic performed this session on the retrieved table. So for the metric coarse series
the two methods disagree in **4 of 37 rows, always by 0,05 mm**. Small — and therefore *exactly* the
kind of discrepancy that survives review and ships. M8 is the single most-used tap in a UK
workshop, and it is one of the four.

### 3.3 The engagement percentage — and a trap I nearly fell into

#25 says `major − pitch` is "~100% metric thread". **It is not, on either definition of the
percentage.** And there are two definitions in circulation, which is itself the hazard.

NBS H28 (1969) fixes the reference height:

> "For 60° Unified thread this equals 0.75H = 100 percent thread height." **[S]**
> (H = height of the fundamental triangle = 0,866 P, so 100% thread height = 0,6495 P per flank.)

NBS H28 (1944) Table 23 tabulates, per size, *every stock drill falling between the minor-diameter
limits* together with its "Percentage of depth of basic thread" — e.g. for 1/4-20 it lists
No. 9 (0.1960) → 83, No. 8 (0.1990) → 79, 13/64 in (0.2031) → 72 **[S]**. Reconstructing that
column from the 0,6495 P reference reproduces H28's own numbers to the rounding
(83.1 / 78.5 / 72.2) **[D]** — which confirms the denominator.

On that definition:

| Rule | % of basic thread depth | Basis |
| --- | --- | --- |
| `drill = D − P` | **77,0 %** | **[D]** — `(P/2) ÷ (0,6495 P)` |
| ISO 2306 M8 × 1,25 (6,80) | 73,9 % | **[D]** |
| ISO 2306 M12 × 1,75 (10,20) | 79,2 % | **[D]** |
| ISO 2306 M4,5 × 0,75 (3,70) | 82,1 % | **[D]** |

If instead you measure engagement as "fraction of the way from major diameter *D* down to the basic
minor diameter *D₁ = D − 1,0825 P*" (ISO 724's formula **[S]**), the same `D − P` drill reads
**92,4 %** **[D]**. Same drill, same thread, two published-looking percentages 15 points apart.
**This is a #22 in waiting and the Applet must never print a bare percentage.**

That 77% figure is corroborated by a tap manufacturer, independently:

> "Most tap drill charts call out only one tap drill size, and that will produce an approximate 75
> percent thread. In general, tap tool life can be increased significantly by using a lower percent
> of thread and we suggest using values between 60% and 70% for most applications. Thread strength
> is not directly proportional to percent of thread. For example a 100% thread specification is
> only 5% stronger than a 75% thread specification but requires 3 times the torque to produce."
> — Guhring Inc., *Tap Drill Calculator*, <https://guhring.com/Tech/tapdrill>, retrieved 2026-07-20 **[S]**

So: **published tap-drill tables target roughly 75%, not 100%** **[S]**, and `major − pitch` lands
at 77% **[D]**. #25's premise that the formula is a 100%-thread rule is **not supported by anything
retrieved**, and the Applet's copy should not repeat it.

### 3.4 What the Applet should emit

1. **Emit the published stocked drill from ISO 2306** for ISO metric coarse, ISO metric fine, UNC,
   UNF and BSPP. It is a primary standard, it is retrievable, it covers four of the seven series,
   and it is what a workshop actually has in the drill index.
2. **For BSW, BSF and BA, emit the manufacturer chart's drill and label the source differently** —
   these come from Gage Crib, not ISO 2306. **Never merge the two columns into one unlabelled
   `tap_drill` field.** Carry the provenance per row, not per table. That is the direct lesson of
   #22: two rows on two surfaces in one column.
3. **Never emit the formula result as if it were a table value.** If a size has no retrieved
   published drill, emit `—` and a note, not `D − P`. An empty cell is honest; a computed cell
   dressed as a lookup is the failure this ticket exists to prevent.
4. **If a computed value is offered at all**, put it in a separate, separately-labelled Output
   (`tap_drill_calculated`), state the rule and its 77%-of-basic-depth consequence, and never sort
   or rank on it.
5. **Suppress the tap drill for BSPP by default.** ISO 2306 Table 5 does tabulate them, but drilling
   and tapping a G thread is not a normal workshop operation and offering the number invites it.
   If shown, show it behind the pipe-thread label.
6. **Say nothing about material.** Guhring's 60–70% recommendation is material- and tool-dependent
   **[S]** and the Applet has no material input. State the standard's number; do not adjust it.

---

## 4. Ranking — surfaced, not answered

**This is the owner's decision. This document deliberately does not make it.** What follows is the
option set and the evidence bearing on each.

The problem: the user supplies (`d_measured`, `p_measured`); candidates have (`d_nominal`,
`p_nominal`) in mixed units and wildly different scales. "Closest" is undefined until someone
chooses a metric.

### Option A — normalised Euclidean distance

`score = √( ((Δd)/σ_d)² + ((Δp)/σ_p)² )`, with σ chosen per-dimension.

- Symmetric, simple, one number.
- **Requires choosing σ_d and σ_p, and that choice *is* the ranking.** It does not remove the
  judgement call, it hides it inside two constants.

### Option B — pitch-first lexicographic

Filter to candidates whose pitch matches within a tolerance, then order those by |Δd|.

- Matches how the trade plausibly identifies a thread: pitch is measured with a gauge and is
  effectively exact; diameter is measured with a caliper on a possibly-damaged, possibly-plated,
  possibly-worn thread.
- **Nothing was retrieved this session that establishes this is how UK workshops identify threads.**
  It is a plausible model of practice, tagged **[—]**. Per #13's rule — published sources are not
  the trade — this is a question for the owner, who has the bench.
- Fails ugly when the user has no pitch gauge and estimates the pitch.

### Option C — tolerance-band gating

Admit a candidate only if the measurement falls inside the standard's own tolerance zone for that
thread, then rank the survivors.

- The tolerance data exists and was partly retrieved: ISO 228-1 Table 1 columns 8–16 **[S]**; the
  BA chart's min/max limits **[S]**; ISO 2306's per-class 5H/6H/7H minor diameters **[S]**.
- **Physically the most defensible, and the most likely to return an empty set** — a 60-year-old
  BSW bolt out of a shed will be outside its own tolerance band. A finder that says "no match" for
  a real thread on the bench is worse than useless.
- Could be used as a *badge* ("in tolerance") rather than a gate.

### Option D — weighted by instrument uncertainty

Weight each dimension by the plausible error of the instrument the user actually used — e.g. a
vernier caliper on a male thread (repeatable to a few hundredths, but reads the *worn* crest, so
biased low), versus a pitch gauge (exact when it matches, useless when it doesn't).

- The most principled framing, and the one that makes the σ in Option A meaningful instead of
  arbitrary.
- **Requires knowing what the owner measures with.** Nothing retrieved answers this. **[—]**

### What the research can contribute to the decision

Three retrieved facts bear on it, and they should be on the table when the owner decides:

1. **The standard itself publishes a preference order.** ISO 261 §5.1 ranks diameters 1st / 2nd /
   3rd choice and marks some pitches "to be avoided as far as possible" **[S]**. A tie-break on
   choice-column is free and is *the standard's own opinion*, not an invention.
2. **"Coarse" must not outrank "fine" by default.** ISO 261 §5.2: "No concept of quality shall,
   however, be associated with these words." **[S]**
3. **Diameter alone is nearly useless across series.** BSW 3/8" is 9,525 mm and M10 is 10,0 mm — a
   0,475 mm gap, well inside caliper-plus-wear error on a used thread **[D]**. Meanwhile their
   pitches are 1,588 mm and 1,5 mm — a 0,088 mm gap that a pitch gauge separates instantly and a
   caliper never will **[D]**. Whatever metric is chosen, **it must not let diameter dominate.**

**Recommendation on process, not on the metric:** ask the owner (a) what they measure pitch with,
and (b) whether a "no confident match" answer is acceptable. Those two answers select between A–D
almost by themselves. Do not pick the best-sourced guess.

---

## 5. The tables actually retrieved

**Every table below was transcribed row-by-row from a retrieved page in this session.** Each states
its single source. **All of them require a human spot-check against the source page before they
ship.** Per #22, "read the right source off the wrong line" is live here, and §6 documents visible
OCR corruption in three of the five source documents.

### 5.1 ISO metric — nominal diameter / pitch

**Source: ISO 262:1998 Table 1** (selected sizes for screws, bolts and nuts, 1–64 mm), transcribed
from <https://cdn.standards.iteh.ai/samples/4167/365d2316ebbe496e87cc7e365bdc8331/ISO-262-1998.pdf>,
retrieved 2026-07-20. **This is the recommended table to ship** — it is the standard's own
selection for fasteners, so it is short and it excludes sizes nobody will meet.

| 1st choice | 2nd choice | Coarse | Fine |
| --- | --- | --- | --- |
| 1 | | 0,25 | |
| 1,2 | | 0,25 | |
| | 1,4 | 0,3 | |
| 1,6 | | 0,35 | |
| | 1,8 | 0,35 | |
| 2 | | 0,4 | |
| 2,5 | | 0,45 | |
| 3 | | 0,5 | |
| | 3,5 | 0,6 | |
| 4 | | 0,7 | |
| 5 | | 0,8 | |
| 6 | | 1 | |
| | 7 | 1 | |
| 8 | | 1,25 | 1 |
| 10 | | 1,5 | 1,25 · 1 |
| 12 | | 1,75 | 1,5 · 1,25 |
| | 14 | 2 | 1,5 |
| 16 | | 2 | 1,5 |
| | 18 | 2,5 | 2 · 1,5 |
| 20 | | 2,5 | 2 · 1,5 |
| | 22 | 2,5 | 2 · 1,5 |
| 24 | | 3 | 2 |
| | 27 | 3 | 2 |
| 30 | | 3,5 | 2 |
| | 33 | 3,5 | 2 |
| 36 | | 4 | 3 |
| | 39 | 4 | 3 |
| 42 | | 4,5 | 3 |
| | 45 | 4,5 | 3 |
| 48 | | 5 | 3 |
| | 52 | 5 | 4 |
| 56 | | 5,5 | 4 |
| | 60 | 5,5 | 4 |
| 64 | | 6 | 4 |

**Basic major diameter = the nominal diameter, exactly** — ISO 724:1993 heads its column
"Nominal diameter = Major diameter *D, d*" **[S]**.

**The wider ISO 261:1998 Table 2 was also retrieved in full** (1 mm to 300 mm, with 3rd-choice
diameters and additional fine pitches — e.g. M10 also admits 0,75; M12 also admits 1; M6 admits
0,75). It is in the same preview PDF and should be consulted if the owner wants coverage beyond
ISO 262. Sizes 5,5 · 9 · 11 · 15 · 17 · 25 · 26 · 28 · 32 · 35 · 38 · 40 · 50 · 55 · 58 · 62 · 65
are 3rd-choice-only and absent from ISO 262 **[S]**.

### 5.2 ISO metric coarse — tap drills

**Source: ISO 2306:1972 Table 1**, transcribed from the preview PDF, retrieved 2026-07-20.
Right-hand column is the standard's recommended stocked drill.

| Size | Pitch | Basic minor dia. (min) | **Drill** |
| --- | --- | --- | --- |
| M1 | 0,25 | 0,729 | 0,75 |
| M1,1 | 0,25 | 0,829 | 0,85 |
| M1,2 | 0,25 | 0,929 | 0,95 |
| M1,4 | 0,3 | 1,075 | 1,10 |
| M1,6 | 0,35 | 1,221 | 1,25 |
| M1,8 | 0,35 | 1,421 | 1,45 |
| M2 | 0,4 | 1,567 | 1,60 |
| M2,2 | 0,45 | 1,713 | 1,75 |
| M2,5 | 0,45 | 2,013 | 2,05 |
| M3 | 0,5 | 2,459 | 2,50 |
| M3,5 | 0,6 | 2,850 | 2,90 |
| M4 | 0,7 | 3,242 | 3,30 |
| M4,5 | 0,75 | 3,688 | **3,70** |
| M5 | 0,8 | 4,134 | 4,20 |
| M6 | 1 | 4,917 | 5,00 |
| M7 | 1 | 5,917 | 6,00 |
| M8 | 1,25 | 6,647 | **6,80** |
| M9 | 1,25 | 7,647 | **7,80** |
| M10 | 1,5 | 8,376 | 8,50 |
| M11 | 1,5 | 9,376 | 9,50 |
| M12 | 1,75 | 10,106 | **10,20** |
| M14 | 2 | 11,835 | 12,00 |
| M16 | 2 | 13,835 | 14,00 |
| M18 | 2,5 | 15,294 | 15,50 |
| M20 | 2,5 | 17,294 | 17,50 |
| M22 | 2,5 | 19,294 | 19,50 |
| M24 | 3 | 20,752 | 21,00 |
| M27 | 3 | 23,752 | 24,00 |
| M30 | 3,5 | 26,211 | 26,50 |
| M33 | 3,5 | 29,211 | 29,50 |
| M36 | 4 | 31,670 | 32,00 |
| M39 | 4 | 34,670 | 35,00 |
| M42 | 4,5 | 37,129 | 37,50 |
| M45 | 4,5 | 40,129 | 40,50 |
| M48 | 5 | 42,587 | 43,00 |
| M52 | 5 | 46,587 | 47,00 |
| M56 | 5,5 | 50,046 | 50,50 |

**Bold rows are the four that disagree with `D − P`** (§3.2).

**Fine-series drills (ISO 2306 Table 2) were retrieved but only partially transcribed here** —
confirmed rows include M2,5 × 0,35 → 2,15; M3 × 0,35 → 2,65; M3,5 × 0,35 → 3,15; M10 × 1,25 → 8,80;
M12 × 1,25 → 10,80; M14 × 1,25 → 12,80; and a long M×2 and M×3 block (M18–M52) **[S]**. The full
fine table is in the preview PDF and must be transcribed from the page image, not from the OCR
text, which mangles several values (§6).

### 5.3 BSW and BSF

**Source: Gage Crib Worldwide, "Whitworth Coarse Thread BS 84" / "Whitworth Fine Thread BS 84"**,
<https://www.ring-plug-thread-gages.com/PDChart/BSW-thread-data.html> and
<https://www.ring-plug-thread-gages.com/PDChart/BSF-thread-data.html>, retrieved 2026-07-20.
**Secondary — manufacturer engineering data citing BS 84, which was not itself retrieved.**

**BSW (coarse)**

| Size | Major dia. (mm) | Pitch (mm) | tpi | Tap drill (mm) |
| --- | --- | --- | --- | --- |
| 1/16" | 1,587 | 0,423 | 60 | 1,15 |
| 3/32" | 2,381 | 0,529 | 48 | 1,90 |
| 1/8" | 3,175 | 0,635 | 40 | 2,50 |
| 5/32" | 3,969 | 0,793 | 32 | 3,20 |
| 3/16" | 4,762 | 1,058 | 24 | 3,70 |
| 7/32" | 5,556 | 1,058 | 24 | 4,50 |
| 1/4" | 6,350 | 1,270 | 20 | 5,10 |
| 5/16" | 7,938 | 1,411 | 18 | 6,50 |
| 3/8" | 9,525 | 1,588 | 16 | 7,90 |
| 7/16" | 11,113 | 1,814 | 14 | 9,20 |
| 1/2" | 12,700 | 2,117 | 12 | 10,40 |
| 5/8" | 15,876 | 2,309 | 11 | 13,40 |
| 3/4" | 19,051 | 2,540 | 10 | 16,25 |
| 7/8" | 22,226 | 2,822 | 9 | 19,25 |
| 1" | 25,400 | 3,175 | 8 | 22,00 |
| 1 1/8" | 28,576 | 3,629 | 7 | 24,50 |
| 1 1/4" | 31,751 | 3,629 | 7 | 27,25 |
| 1 3/8" | 34,926 | 4,233 | 6 | 30,25 |
| 1 1/2" | 38,100 | 4,233 | 6 | 33,50 |

(chart continues to 4 1/2"; sizes above 1 1/2" omitted here as out of workshop scope)

**BSF (fine)**

| Size | Major dia. (mm) | Pitch (mm) | tpi | Tap drill (mm) |
| --- | --- | --- | --- | --- |
| 3/16" | 4,763 | 0,794 | 32 | 4,00 |
| 7/32" | 5,556 | 0,907 | 28 | 4,60 |
| 1/4" | 6,350 | 0,977 | 26 | 5,30 |
| 9/32" | 7,142 | 0,977 | 26 | 6,10 |
| 5/16" | 7,938 | 1,156 | 22 | 6,80 |
| 3/8" | 9,525 | 1,270 | 20 | 8,30 |
| 7/16" | 11,113 | 1,411 | 18 | 9,70 |
| 1/2" | 12,700 | 1,588 | 16 | 11,10 |
| 9/16" | 14,288 | 1,588 | 16 | 12,70 |
| 5/8" | 15,875 | 1,814 | 14 | 14,00 |
| 11/16" | 17,463 | 1,814 | 14 | 15,50 |
| 3/4" | 19,050 | 2,117 | 12 | 16,75 |
| 13/16" | 20,638 | 2,117 | 12 | 18,25 |
| 7/8" | 22,225 | 2,309 | 11 | 19,75 |
| 1" | 25,400 | 2,540 | 10 | 22,75 |

(chart continues to 4 1/4")

**Three flags on these two tables, all found this session:**

1. **The two charts disagree with each other on rounding.** BSW 3/16" is given as 4,762 and BSF
   3/16" as 4,763; BSW 5/8" as 15,876 and BSF 5/8" as 15,875 **[S]**. Exact value is
   0,625 × 25,4 = 15,875 **[D]**. The BSW page rounds up. Harmless numerically, but it proves the
   charts are not machine-generated from one basis, so **row-level errors are possible**.
2. **The BSW chart omits sizes that BS 84 covers.** NBS H28-1944 Table 149 lists 9/16" (12 tpi) and
   11/16" (11 tpi) in the Whitworth coarse series **[S]**; the Gage Crib BSW chart does not. Whether
   BS 84 itself lists them was not established. **[—]**
3. **BSF's tap-drill column stops at 2 1/2"** ("n/a" above that) **[S]** — so the Applet must handle
   a missing drill without substituting a computed one.

### 5.4 BA

**Source: Gage Crib Worldwide, "BS 93 British Association (BA) Screw Threads Data Charts"**,
<https://www.ring-plug-thread-gages.com/PDChart/BA-thread-data.html>, retrieved 2026-07-20.
**Secondary — cited to BS 93:2008, which was not retrieved.** Values are the internal-thread
table's `D min` (= basic major diameter) and pitch.

| Size | Pitch (mm) | Major dia. (mm) |
| --- | --- | --- |
| 0 BA | 1,00 | 6,000 |
| 1 BA | 0,90 | 5,300 |
| 2 BA | 0,81 | 4,700 |
| 3 BA | 0,73 | 4,100 |
| 4 BA | 0,66 | 3,600 |
| 5 BA | 0,59 | 3,200 |
| 6 BA | 0,53 | 2,800 |
| 7 BA | 0,48 | 2,500 |
| 8 BA | 0,43 | 2,200 |
| 9 BA | 0,39 | 1,900 |
| 10 BA | 0,35 | 1,700 |
| 11 BA | 0,31 | 1,500 |
| 12 BA | 0,28 | 1,300 |
| 13 BA | 0,25 | 1,200 |
| 14 BA | 0,23 | 1,000 |
| 15 BA | 0,21 | 0,900 |
| 16 BA | 0,19 | 0,790 |

**No tap drill column exists on this chart** **[S]**, and ISO 2306 does not cover BA **[S]**. So
**the BA rows must ship with no tap drill.** Do not compute one.

**Collision warning for the ranker, found this session:** 10 BA is 1,700 mm × 0,35 and M1,8 is
1,800 mm × 0,35 — **identical pitch, 0,1 mm apart in diameter** **[D]**. Also 13 BA (1,200 × 0,25)
versus M1,2 (1,200 × 0,25) — **identical in both dimensions** **[D]**. No ranking metric can
separate that pair; the Applet must be able to return a genuine tie and say so.

### 5.5 UNC / UNF

**Source: NBS Handbook H28 (1969) Part I, Table 2.7**, transcribed from
<https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1969p1.pdf>, retrieved 2026-07-20.
**Primary, US Government, public domain.** Major diameters are as printed, in inches; the mm column
is **[D]** (× 25,4), computed here, not in the source.

| Basic major dia. (in) | (mm) **[D]** | UNC tpi | UNF tpi |
| --- | --- | --- | --- |
| 0,060 | 1,524 | — | 80 |
| 0,073 | 1,854 | 64 | 72 |
| 0,086 | 2,184 | 56 | 64 |
| 0,099 | 2,515 | 48 | 56 |
| 0,112 | 2,845 | 40 | 48 |
| 0,125 | 3,175 | 40 | 44 |
| 0,138 | 3,505 | 32 | 40 |
| 0,164 | 4,166 | 32 | 36 |
| 0,190 | 4,826 | 24 | 32 |
| 0,216 | 5,486 | 24 | 28 |
| 0,250 | 6,350 | 20 | 28 |
| 0,3125 | 7,938 | 18 | 24 |
| 0,375 | 9,525 | 16 | 24 |
| 0,4375 | 11,113 | 14 | 20 |
| 0,500 | 12,700 | 13 | 20 |
| 0,5625 | 14,288 | 12 | 18 |
| 0,625 | 15,875 | 11 | 18 |
| 0,750 | 19,050 | 10 | 16 |
| 0,875 | 22,225 | 9 | 14 |
| 1,000 | 25,400 | 8 | 12 |
| 1,125 | 28,575 | 7 | 12 |
| 1,250 | 31,750 | 7 | 12 |
| 1,375 | 34,925 | 6 | 12 |
| 1,500 | 38,100 | 6 | 12 |

**Note the collisions with BSW/BSF that this creates, and that they are the whole reason the finder
exists:** 1/4" UNC (6,350 mm, 20 tpi) and 1/4" BSW (6,350 mm, 20 tpi) are **numerically identical
in diameter and pitch** and differ only in thread *angle* (60° vs 55°) **[D]** — which the Applet's
two inputs cannot see. **The Applet must return both and say it cannot distinguish them.** Likewise
3/8" UNC (16 tpi) vs 3/8" BSW (16 tpi) **[D]**. Any ranking that silently picks one is wrong.

**UNC / UNF tap drills** are in ISO 2306 Tables 3 and 4, retrieved **[S]** (e.g. 1/4-20 UNC →
5,10 mm; 5/16-18 → 6,60 mm; 3/8-16 → 8,00 mm; 1/2-13 → 10,80 mm; No. 10-24 → 3,90 mm). These are
**metric drills for inch threads**, which is a deliberate feature of ISO 2306 — the standard
tabulates metric drills throughout **[S]**, and Guhring notes the same convenience: it "allows for
the combining of inch and metric taps and drills where convenient to do so" **[S]**. The OCR of
Tables 3 and 4 is visibly damaged (§6) and these must be transcribed from page images.

### 5.6 BSPP (G-series)

**Source: ISO 228-1:2000 Table 1**, columns 1–7, transcribed from the preview PDF, retrieved
2026-07-20. **Primary.**

| Designation | Threads / 25,4 mm | Pitch *P* | Major *d=D* | Pitch *d₂=D₂* | Minor *d₁=D₁* |
| --- | --- | --- | --- | --- | --- |
| G 1/16 | 28 | 0,907 | 7,723 | 7,142 | 6,561 |
| G 1/8 | 28 | 0,907 | 9,728 | 9,147 | 8,566 |
| G 1/4 | 19 | 1,337 | 13,157 | 12,301 | 11,445 |
| G 3/8 | 19 | 1,337 | 16,662 | 15,806 | 14,950 |
| G 1/2 | 14 | 1,814 | 20,955 | 19,793 | 18,631 |
| G 5/8 | 14 | 1,814 | 22,911 | 21,749 | 20,587 |
| G 3/4 | 14 | 1,814 | 26,441 | 25,279 | 24,117 |
| G 7/8 | 14 | 1,814 | 30,201 | 29,039 | 27,877 |
| G 1 | 11 | 2,309 | 33,249 | 31,770 | 30,291 |
| G 1 1/8 | 11 | 2,309 | 37,897 | 36,418 | 34,939 |
| G 1 1/4 | 11 | 2,309 | 41,910 | 40,431 | 38,952 |
| G 1 1/2 | 11 | 2,309 | 47,803 | 46,324 | 44,845 |
| G 1 3/4 | 11 | 2,309 | 53,746 | 52,267 | 50,788 |
| G 2 | 11 | 2,309 | 59,614 | 58,135 | 56,656 |

(the standard's table continues to G 6; sizes above G 2 omitted here as out of workshop scope)

**A ranking hazard, found this session:** G 1/2 (20,955 × 1,814) and BSW 7/16" (11,113 × 1,814)
share a pitch *exactly* — both are 14 tpi Whitworth-form **[D]** — so a pitch-first ranker
(§4 Option B) puts them adjacent despite a 9,8 mm diameter gap. Worth a fixture.

---

## 6. What I tried to retrieve and could not

| Target | URL / route attempted | Outcome |
| --- | --- | --- |
| **BS 84** (BSW/BSF) | <https://knowledge.bsigroup.com/products/parallel-screw-threads-of-whitworth-form-requirements> | **Paywalled.** Product page reached; abstract retrieved verbatim: *"This British Standard specifies limits of sizes, and tolerances, for single start parallel screw threads of Whitworth form, for general engineering use."* **No table data.** No price displayed. BS 84:1956 shown as withdrawn, superseded by BS 84:2007. |
| **BS 93** (BA) | <https://knowledge.bsigroup.com/products/british-association-b-a-screw-threads-requirements> | **Paywalled.** Status Current, published 30 Sep 2008. Summary only, no table data, no price displayed. |
| **BS 1580** (Unified, UK) | Searched; BS 1580-1:2007 and BS 1580-3:2007 product pages located on BSI Knowledge | **Paywalled.** |
| BS 1580-3:2007 preview | <https://webstore.ansi.org/preview-pages/BSI/preview_30158493.pdf> | **HTTP 403.** Blocked. |
| **BS 2779** (BSPP) | Referenced only, via Gage Crib | **Not attempted directly** — superseded by ISO 228, which *was* retrieved in full. |
| **BS 21** (BSPT) | Not attempted | Out of scope once BSPT was deferred. |
| **ISO 261 / 262 / 724 / 965-1 / 228-1 / 2306** — official ISO pages | <https://www.iso.org/standard/4165.html> etc. | **HTTP 403** on every iso.org page attempted. |
| ISO Online Browsing Platform preview | <https://www.iso.org/obp/ui/#iso:std:iso:724:en> | **HTTP 200 but content-free** — the OBP is a Vaadin JavaScript application; the served HTML is a loader shell with `<noscript>You have to enable javascript…`. **Preview is not retrievable without a browser.** Records as *preview-only / JS-gated*, not as paywalled. |
| **ASME B1.13M-2005** (M profile, the normative US metric table) | Located a full-text PDF on a third-party site (`fpg-co.com`) | **Deliberately not used.** It is an apparently unauthorised copy of a copyrighted ASME standard. DNS resolution also failed from this environment. **Not cited, not transcribed.** The needed data came from ISO 261 instead. |
| **FED-STD-H28/21B** (US federal metric screw threads) | <https://everyspec.com/FED-STD/FED-STD-H28_21B_40274/> → downloaded successfully | **Retrieved but does not answer the question.** Its §5.1.2 says: *"Only the diameter/pitch combinations listed in tables 4 and 5 of ANSI/ASME B1.13M-1983 are applicable"* — it **refers out** to the paywalled ASME standard and does not reproduce the M-profile table. **Its own Tables XXI.1/XXI.2 are the MJ profile** (aerospace, rounded root), a different and narrower series. The OCR renders "MJ" as "W"/"M", which would have made this an easy and completely wrong substitution. **Recorded as a near-miss, not used.** |
| **FED-STD-H28/2** (Unified) | everyspec download URL guessed | **HTTP 404.** Not pursued; NBS H28-1969 covered it. |
| Machinery's Handbook, public-domain editions | Searched archive.org via web search | **Not found.** Only commercial reprints of the 1914 first edition surfaced. **No public-domain scan opened, nothing cited from it.** |
| NBS H28 (1944) BSW/BSF numeric tables | PDF pages 261–262, rendered to image and read | **Retrieved and legible, but wrong quantity** — the major-diameter columns are *American Truncated Whitworth*, not BSW basic. Sizes and tpi are usable; major diameters are not. |
| NASA RP-1228 *Fastener Design Manual* | Surfaced in search | **Not opened** — the search result itself indicated thread standards are excluded from it. Not cited. |
| **Confirmation that ISO 2306:1972 is current or withdrawn** | iso.org | **Not retrieved** (403). The Applet should record the edition as 1972 and flag that its currency is unverified. **[—]** |

### OCR damage found in retrieved sources — the transcription hazard, documented

Three of the five scanned/preview PDFs contain visible OCR corruption in exactly the tables that
matter. **Nothing in §5 should be trusted until checked against a page image.**

- **NBS H28-1944 Tables 149/150 (BSW/BSF) and 158/159 (tap drills)**: the extracted text is
  scrambled beyond use — sizes render as `H-40`, `]A-20`, `6/ie-18`, and a dimension as `0.09G7`.
  The **page images are legible** (verified by rendering PDF page 261) but the table is printed
  rotated 90°.
- **ISO 724:1993**: `0,8` renders as `08` and `W3`; `1,5` as `L5`; `2,5` as `25` and `215`.
- **ISO 2306:1972 Tables 3–5**: `3/8` BSP minor-diameter max renders as `16.395` where the pattern
  and ISO 228-1's `D₁ = 14,950` require `15.395`; `0.706` renders as `IL706`; `8.082` as `%A082`;
  `31.00` as `31 .oo`.
- **FED-STD-H28/21B**: the entire document renders words without spaces (`Standardtolerancethreads`)
  and **misreads the profile designation `MJ` as `W`**, which is how a careless read produces a
  metric table that is actually an aerospace subset.

---

## 7. Verification performed this session

| Check | Sources compared | Result |
| --- | --- | --- |
| ISO 724 minor diameter vs. ISO 2306 "min" column, M6 | 4,917 vs 4,917 | ✅ two independent standards agree |
| ISO 724 formula `D₁ = D − 1,0825 P` reproduces its own table, M6 | 6 − 1,0825 = 4,9175 → 4,917 | ✅ |
| ISO 262 selection is a subset of ISO 261 Table 2 | all 34 rows | ✅ every ISO 262 row and pitch appears in ISO 261 |
| BA pitch column vs `p = 0,9ⁿ` (H28-1944) | 0 BA → 1,000; 5 BA → 0,590; 10 BA → 0,349; 16 BA → 0,185 | ✅ matches chart to its rounding, all 17 rows |
| BA major diameter vs `D = 6 p^(6/5)` (H28-1944, exponent reconstructed) | 0 BA → 6,000; 1 BA → 5,287 vs 5,300; 5 BA → 3,189 vs 3,200; 10 BA → 1,695 vs 1,700; 16 BA → 0,794 vs 0,790 | ✅ fits all 17 rows to the standard's rounding — **strong independent check on a secondary table** |
| BSW/BSF pitch vs `25,4 / tpi` | 1/16" 60 tpi → 0,4233 vs 0,423; 3/16" 24 tpi → 1,0583 vs 1,058; 1/2" 12 tpi → 2,1167 vs 2,117 | ✅ pitch column is internally consistent |
| BSW major diameter vs `nominal × 25,4` | 1/4" → 6,350 ✅; 5/8" → 15,875 vs chart 15,876 ⚠️; 3/16" → 4,7625 vs chart 4,762 (BSW) / 4,763 (BSF) ⚠️ | ⚠️ inconsistent rounding across the two charts |
| BSW tpi vs NBS H28-1944 Table 149 (page image) | 1/8→40, 3/16→24, 1/4→20, 5/16→18, 3/8→16, 7/16→14, 1/2→12 | ✅ agree; H28 **additionally** lists 9/16 (12) and 11/16 (11) |
| `D − P` vs ISO 2306 Table 1, all 37 coarse rows | 33 agree, 4 differ by ±0,05 | ✅ quantified (§3.2) |
| `D − P` engagement on H28's definition | `(P/2) ÷ (0,6495 P)` = 77,0 % | ✅ consistent with Guhring's "approximate 75 percent" |
| H28-1944 Table 23 percentage column reconstructed | 1/4-20: #9 → 83,1 (H28: 83); #8 → 78,5 (H28: 79); 13/64 → 72,2 (H28: 72) | ✅ confirms the 0,6495 P reference height |
| ISO 228-1 `D₁ = D − 1,280 654 P`, G 1/2 | 20,955 − 1,280654 × 1,814 = 18,632 vs table 18,631 | ✅ (0,001 rounding) |

---

## 8. Open questions — for the owner, not for more research

These are the points where the sources terminate. Per #13, they should be answered from the bench,
not by picking the best-sourced guess.

1. **What is the ranking metric?** §4. Sub-questions the owner can answer and the sources cannot:
   what do you measure pitch with, and is "no confident match" an acceptable answer?
2. **How should a genuine tie be rendered?** 1/4" UNC and 1/4" BSW are identical in both inputs
   **[D]**; 13 BA and M1,2 likewise **[D]**. The Applet needs a first-class "cannot distinguish —
   check the thread angle" result. This is a UI decision, not a data one.
3. **Does BS 84 include 9/16" and 11/16" BSW?** NBS H28-1944 lists them **[S]**, the Gage Crib chart
   omits them **[S]**, and BS 84 was not retrieved **[—]**. If the owner has a copy of BS 84 or
   Zeus/Tubal Cain tables on the bench, one look settles it.
4. **Is a BA tap drill column wanted at all?** No retrieved source publishes one. **[—]** If yes,
   it must come from a named bench source and be labelled as such, never computed.
5. **Should the table show thread angle (55° / 60° / 47,5°) as a column?** It is the only thing that
   separates several of the collisions above, and the user *can* often see it with a thread gauge.
   Adding it would change the Applet's input model, so it is a scope decision.
6. **Is ISO 2306:1972 still current?** Not established (iso.org 403) **[—]**. If it is withdrawn,
   the tap-drill recommendation still stands on its own merits but the citation needs a note.

## Sources and trust

**High trust — primary standards, retrieved in full via publisher-side free preview PDFs:**

- [ISO 261:1998 — *ISO general purpose metric screw threads — General plan*](https://cdn.standards.iteh.ai/samples/4165/ec50482690954e82931c52fdce3bc8bb/ISO-261-1998.pdf) —
  Table 2 (nominal diameter/pitch, 1–300 mm) retrieved complete, plus the §5 selection rules.
- [ISO 262:1998 — *Selected sizes for screws, bolts and nuts*](https://cdn.standards.iteh.ai/samples/4167/365d2316ebbe496e87cc7e365bdc8331/ISO-262-1998.pdf) —
  Table 1 (1–64 mm) retrieved complete. **The recommended shipping table for ISO metric.**
- [ISO 724:1993 — *Basic dimensions*](https://cdn.standards.iteh.ai/samples/4958/a73f8e6490d34e8d87367cc863514fcf/ISO-724-1993.pdf) —
  Table 1 and the formulas `D₂ = D − 0,6495 P`, `D₁ = D − 1,0825 P`. OCR-damaged.
- [ISO 2306:1972 — *Drills for use prior to tapping screw threads*](https://cdn.standards.iteh.ai/samples/7135/5bef5f85e78040d6b848307ffd62d83f/ISO-2306-1972.pdf) —
  **the key source for §3.** Tables 1–2 (ISO metric), 3–4 (UNC/UNF), 5 (BSPP).
- [ISO 228-1:2000 — *Pipe threads where pressure-tight joints are not made on the threads*](https://cdn.standards.iteh.ai/samples/33777/842b7c5409454ceba69c7dad9c308be1/ISO-228-1-2000.pdf) —
  scope statement and Table 1 retrieved complete.

**High trust — US Government, public domain, free:**

- [NBS Handbook H28 (1969) Part I](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1969p1.pdf) —
  Table 2.7, the Unified standard series (UNC/UNF). Clean OCR.
- [NBS Handbook H28 (1944)](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1944.pdf) —
  the BA generating formulas and the BS 93-1919 reference (p.264–265); the tap-drill philosophy and
  percentage-of-thread-depth data (§4, pp.42–43, Table 23); Whitworth sizes and tpi
  (Tables 149–150, pp.249–252). **Its Whitworth major diameters are the American *Truncated*
  form and must not be used as BSW basic values.**
- [FED-STD-H28/21B (1984)](https://everyspec.com/FED-STD/FED-STD-H28_21B_40274/) — retrieved and
  **rejected** as a source for ISO metric: it refers out to ASME B1.13M and its own tables are the
  MJ profile. Recorded so the trap is not re-entered.

**Medium trust — manufacturer engineering data, cited to a standard, used where no primary was retrievable:**

- [Gage Crib Worldwide — BSW chart](https://www.ring-plug-thread-gages.com/PDChart/BSW-thread-data.html),
  [BSF chart](https://www.ring-plug-thread-gages.com/PDChart/BSF-thread-data.html),
  [BA chart](https://www.ring-plug-thread-gages.com/PDChart/BA-thread-data.html),
  [Whitworth form overview](https://www.ring-plug-thread-gages.com/ti-bs-Whitworth-screw-thread-form.htm),
  [BS 93 overview](https://www.ring-plug-thread-gages.com/ti-spec-BS-93.htm) — all retrieved
  2026-07-20. The site states its own limitation: *"a brief overview of the standard and for general
  information only"*, and recommends consulting the copyrighted standard.
- [Guhring Inc. — Tap Drill Calculator](https://guhring.com/Tech/tapdrill) — the source for the
  ~75 %-thread convention and the 100 %-vs-75 % strength/torque comparison.

**Paywalled — attempted, not retrieved (abstracts only):**

- [BS 84:2007](https://knowledge.bsigroup.com/products/parallel-screw-threads-of-whitworth-form-requirements),
  [BS 93:2008](https://knowledge.bsigroup.com/products/british-association-b-a-screw-threads-requirements),
  BS 1580-1/-3:2007, ASME B1.13M.

**Not used:**

- An apparently unauthorised full-text PDF of ASME B1.13M-2005 found on a third-party host.
  Located, not fetched, not cited.
- Wikipedia, fastener-retailer thread charts, forum threads and any table that did not name the
  standard it came from. Several appeared in searches. **None was used as evidence for any claim or
  any row in this document.**
