# Workshop Helper — Host framework specification

**Status:** build-ready. **Audience:** whoever implements the Host (likely Claude Code).

This document states the **contracts**. It does not re-argue the decisions behind
them — each one links its ADR or its ticket, and those hold the reasoning. If you
find yourself disagreeing with a rule here, read the linked source before changing
it: most of these rules exist because the obvious alternative was tried on paper
and failed for a structural reason.

Vocabulary is [`CONTEXT.md`](../../CONTEXT.md). Use those terms — Host, Applet,
Applet type, Manifest, Overlay, Root, Input, Result, Output, Designation — and do
not drift to synonyms.

---

## 1. The invariants

Seven rules govern everything below. They are stated once, here, because each has
been arrived at more than once from different directions, and each will be pushed
on again during implementation.

### 1.1 The Manifest declares structure; it never expresses logic

The Manifest says *what exists*. It never says *what to do*. Concretely:

- Modes are **structural** — which Inputs and Outputs exist — never a conditional
  expression ([#12](https://github.com/andyalexander/workshop-helper/issues/12),
  rejecting `show_if`).
- Validation is `min` / `max` / `step`, never a cross-field rule
  ([#5](https://github.com/andyalexander/workshop-helper/issues/5),
  [#8](https://github.com/andyalexander/workshop-helper/issues/8)).
- Calibration is a keyed lookup, never a computed table
  ([#15](https://github.com/andyalexander/workshop-helper/issues/15), refusing
  multi-key).
- Documentation renders markdown, never a template (#15).
- There is no declarative drawing model; a graphic is a string the Applet builds
  ([#18](https://github.com/andyalexander/workshop-helper/issues/18)).
- There is no `provenance` metadata vocabulary
  ([#23](https://github.com/andyalexander/workshop-helper/issues/23)).

Any of those, taken alone, looks like a local judgement call. They are not: this
is **one door being pushed on six times**, and the sixth push arrived dressed as
metadata rather than as logic. The moment the Manifest gains an expression — a
condition, a formula, a template, a rule — the Host stops knowing what an Applet
is, and every generic affordance it provides (form rendering, validation, saved
defaults, consistent formatting) becomes conditional on evaluating that
expression.

**When a seventh push arrives, recognise it as the seventh.** The tell is always
the same: something that *could* be data is proposed as something the Manifest
evaluates.

### 1.2 Every calibration row is a measurement of one specific physical tool

A calibration figure describes a lump of steel, not a computer and not a
standard. Therefore:

**No calibration row may ever be derived from another, by any formula, ever.**

This is not conservatism. `R_c / OD` is **4.667 on the 15mm bender and 5.000 on
the 22mm** — measured, both of them (#17, #22). There is no scaling law. A
two-point fit would confidently "predict" 144.3mm at 28mm, and that number is
worthless. The calibration table is a table **because it cannot be a formula**.

The corollary bites the input schema, not just the data: **if you have not
measured a size, that size is not a `choice`.** See §5.3 rule 3 — the key set must
equal the choice set exactly, so an unmeasured size cannot be silently carried as
an empty row or a guessed one. It is simply absent until someone measures it.

And the reason behind the rule, which #23 folded in after refusing to build a
mechanism for it: **the Host cannot tell you whether a row was measured or
guessed.** No field records it, and none should. That the Host is blind here is
*precisely why* it must never derive one row from another — a derived row is
indistinguishable from a measured one at exactly the moment it matters.

### 1.3 Structured Outputs are the norm; `html` is the pressure valve

A calculator's Result is **named Outputs**. The `html` channel exists for the long
tail that ADR-0005 declined to give a new Applet type, and it is **not an equal
option**.

An escape hatch that is easier than the structured path becomes the default path.
If contributors reach for `html` first, the Host's generic formatting dies — and
with it every reason the Host knows anything about Outputs at all.

Sharper, from #24: **a pressure valve that is being exercised is failing.** The
correct usage count for `html` among the worked examples is **zero**, and it is
deliberately shipped with no runnable coverage (§11).

### 1.4 Modes change what exists; Inputs change what things are

The line between "this should be a mode" and "this should be an Input" is not a
matter of taste:

- If it changes **which Inputs or Outputs exist**, it is a mode.
- If it changes **a value**, it is an Input — or it is not in the Manifest at all.

#18 settled a real case with this: bending *sequence* (mark-both-then-bend vs
measure-bend-measure-bend) changes neither the Input set nor the Output set, only
a number. So it is not a mode. It became a committed convention plus a secondary
Output.

### 1.5 The graphic is where reference surfaces live

For any Applet with a geometry, **the image shows what direction to measure from
what point; the number is how far.** Neither alone is the deliverable.

This is a framework claim, not a quirk of one Applet. The pipe-bender's number has
been wrong **three times** — #4 inferred the outside edge, #17 falsified it at the
bench, #22 found a third surface printed in the same paragraph as the second —
and every one of those was a *"from what point, in what direction"* failure, and
**every one was invisible in the number**. A setback of 70.0mm looks identical
whether it is measured to a corner, an outside edge, or a projected centreline.

The graphic also carries a second property no Output can: the **sequence** in
which operations happen. Two independent properties, neither expressible as a
number, is what makes this a rule rather than an observation.

### 1.6 A contract may ship uncovered iff its specification surface is nil

The bar for the worked examples is **contract coverage**, not "minimal but
complete" (retired by #18).

- Coverage requires something **runnable**. Inline TOML in this document shows a
  *configuration*; it never covers a *contract*.
- The test for every feature of every worked example is: **does this map to a
  contract nothing else covers?** If not, cut it — see §1.7.
- A contract may ship with zero coverage **only if specifying it requires no
  detail** — that is, if there is nothing an implementer could get wrong by
  inference.

The principle underneath the rule: **coverage matters because specification detail
is where unchecked inference hides.** `html`'s entire contract is *"the Applet
returns a string; the Host embeds it verbatim and promises nothing"* — no
validation, no sanitisation, no rendering rules — so it passes. `pattern` did not
(regex flavour, anchoring, escaping, interaction with `choice`, failure
rendering: five places to hide), so `text` and `pattern` were **cut** (#24).

### 1.7 No ceremony in the flagship

**No contract is covered by bolting something onto an Applet that does not
genuinely need it.** The pipe-bender is the only calculator anyone will ever copy,
so anything decorative in it propagates forever.

This is why the third worked example exists at all: when the `table` Result
channel was found to have no runnable consumer, the answer was a **thread finder**
the owner actually wanted, not a spurious table bolted onto the bender.

---

## 2. Architecture

### 2.1 What the Host is

A foreground CLI process that binds a fixed port on `127.0.0.1`, opens the user's
default browser at it, serves a local web UI, and exits on Ctrl-C
([ADR-0001](../adr/0001-local-browser-ui-foreground-process.md)).

It is **not a daemon**. Nothing is installed as a service; nothing listens when
the Host is not running. "Minimal footprint" for this project means **operational
simplicity** — nothing in the background, one command to start — never byte size
or dependency count.

Applet authors never write JavaScript. Interactivity is a **round-trip to the
local Host**: the browser posts changed Inputs, the Applet's Python recomputes,
the Host returns fresh markup to swap in
([ADR-0002](../adr/0002-pure-python-applets-server-round-trip.md)). On localhost
this is sub-millisecond.

### 2.2 Library stack

Decided in [#3](https://github.com/andyalexander/workshop-helper/issues/3);
detail in [`docs/research/library-stack.md`](../research/library-stack.md).

| Concern | Choice | Note |
|---|---|---|
| Web framework | **Flask 3.1.3** | FastAPI rejected — its Pydantic validation reads *static* annotations, which structurally conflicts with ADR-0004's runtime-derived schema, and costs ~2.5× startup for machinery you would route around. |
| Round-trip | **htmx 2.0.10, vendored** | Served from the Host, not a CDN. Layered over a form that works with no JS at all. |
| Markdown | **markdown-it-py 4.2.0** | Reached only through `workshop_utils` (§7.3). |
| TOML | **`tomllib`** (stdlib, 3.11+) | Read-only by construction. |
| JSON | **`json`** (stdlib) | The Overlay. |

`tomlkit` is **not** a dependency and must not become one — see §1 of ADR-0007.

### 2.3 Launch and lifecycle

- Installed with `uv tool install`. Never `pip`.
- One command starts it, in the foreground. Ctrl-C stops it.
- **Port is CLI-only**: a fixed, non-obvious default plus a `--port` override.
  There is deliberately **no config key for port**
  ([#10](https://github.com/andyalexander/workshop-helper/issues/10)) — port
  already has a complete solution, and adding a second way to set it buys nothing.
- **If the default port is busy, the most likely cause is that the Host is already
  running.** Opening the browser at it beats starting a second copy. Do that,
  print one line saying so, and exit 0.

> **The one free choice in this spec.** The default port number was never decided
> by a ticket. Pick one in the high private range and hard-code it; `8731` is
> suggested. Everything else in this document is settled.

Startup sequence:

1. Resolve the Host home directory (§2.4).
2. Read `config.toml` if present.
3. Scan Roots and build the index (§2.5, §2.6) — reading text files only, importing
   nothing.
4. Load the Overlay (§8).
5. Emit a **one-line console summary**: `Loaded 12 Applets; 1 failed.` No new UI,
   no per-failure spam — failures are visible in the UI as greyed cards (§9).
6. Bind, open browser, serve.

### 2.4 Host home and configuration

**One folder, no XDG split** (#10 — the owner's call, to avoid polluting the
machine):

```
~/.workshop-helper/
├── config.toml      # hand-edited, TOML, read-only to the Host
├── applets/         # the user's own Root
└── overlay.json     # Host-written, JSON, safe to delete
```

`WORKSHOP_HELPER_HOME` overrides the location.

**Format signals ownership** (ADR-0007), and it falls out of the stdlib's own
asymmetry — `tomllib` reads TOML but cannot write it, while `json` does both:

- **TOML = hand-authored, read-only to the Host.** Manifests, `config.toml`.
- **JSON = machine-written, Host-owned, safe to delete.** `overlay.json`.

No `# DO NOT EDIT` banner is needed; the extension carries the meaning.

`config.toml` owns **exactly one thing** — the ordered list of *foreign* Root
paths:

```toml
roots = [
  "~/src/mate-collection/applets",
  "/mnt/shared/workshop-applets",
]
```

That is the whole file. Locale was **dropped entirely** (#10): #5 removed its only
real use, and the UK mixed-unit reality is precisely *why* one locale flag is too
blunt to help. The tool's UK-ness lives in its **content**, not in a Host setting.

> ADR-0007 names the Overlay file `overrides.json`. #10 is later and names the
> directory layout; the file is **`overlay.json`**.

### 2.5 Roots and discovery

An Applet is a **folder**. Roots are scanned PATH-style; folders are **flat within
each Root**, and no category ever appears in a path
([ADR-0003](../adr/0003-applets-are-folders-tags-not-hierarchy.md)). The
filesystem carries only what is genuinely single-valued: **identity** (the folder
name is the Applet id) and **provenance** (the Root).

**Root tiers are structural, not declared** — nothing is hand-categorised:

| Tier | Root | Source |
|---|---|---|
| 1 | `~/.workshop-helper/applets/` | convention directory |
| 2 | the wheel's built-in Root | ships inside the installed package |
| 3… | each path in `config.toml`'s `roots`, **in order** | foreign |

This ordering *is* #8's `own > built-in > foreign, foreigns by config order`
precedence. A missing or unreadable Root path is not an error; skip it and count
it in the startup summary.

**A folder with no `manifest.toml` is not an Applet** (ADR-0004) and correctly
never appears anywhere — not as a card, not as an error.

### 2.6 The index

Discovery is **cheap and safe**: the Host builds its index by reading small text
files and **imports no Applet Python at all** (ADR-0004). If metadata lived in
Python, startup would scale with the library, one bad import would take down the
Host, and — critically — *listing* a contributed Applet would *execute* it.

The index holds, per Applet: id, Root, type, name, description, tags, author, and
— for `documentation` Applets — **the body text of `content.md`**.

That last item is a real requirement, not an optimisation: #2's search falls back
to full text over name + description + tags + **content body**, so **the Host must
read Applet content, not just Manifests.**

### 2.7 Identity collision and shadowing

Ids are folder names, so two Roots can collide. Resolution is by the tier
precedence in §2.5: **the winner loads; the loser is greyed with a
"shadowed by Root 'X'" notice** (#8).

Built-in deliberately beats foreign: a cloned Root must not be able to shadow a
core tool by name-collision. This also keeps the Overlay key (§8, Applet id
alone) unambiguous.

### 2.8 Routing and the render pipeline

Three surfaces:

1. **Browse** (`/`) — the shell UI: facet sidebar plus card grid (§9).
2. **Applet page** (`/a/<id>`) — the Applet, rendered per its type.
3. **Compute** (`POST /a/<id>/compute`) — htmx target; returns the rendered
   Result fragment only.

Render pipeline by type (ADR-0005 — the Applet type **is** the rendering contract
the Host implements):

- **`documentation`** — read `content.md`, render it via
  `workshop_utils.render_markdown`, serve the folder's assets. **No Python is
  imported. Ever.**
- **`calculator`** — build the form from the Manifest's Inputs; lazily import
  `applet.py`; call `compute()`; render the Result.

---

## 3. Applet types

The set is **closed: `documentation` and `calculator`**
([ADR-0005](../adr/0005-applet-types-are-closed.md)). Adding a type is a change to
the Host. A contributor cannot add one, because doing so would mean shipping
rendering code into the Host, at which point the Host no longer knows what it is
rendering and every generic affordance stops working.

Closed is **reversible**; open is not.

### 3.1 `documentation`

```
thread-pitch/
├── manifest.toml
├── content.md
└── (assets: images, PDFs, anything)
```

**Zero code.** A stored manual or a manufacturer link page is exactly this, with
the PDF sitting in the folder.

- No Inputs, no Outputs, no `compute()`, **no `[calibration]`** — a documentation
  Applet has no `compute()` to receive it, and interpolating into `content.md`
  would be a template language (§1.1). A `[calibration]` section on a
  `documentation` Applet is **malformed, not ignored** (#15).
- Missing `content.md` is a discovery-time fault (§10).

### 3.2 `calculator`

```
pipe-bender/
├── manifest.toml
├── applet.py          # must define compute()
└── (any other .py in the package)
```

Calculators may be interactive or static; **the static calculator is the
zero-Input degenerate case**, not a separate thing (§4.6).

---

## 4. The Manifest

`manifest.toml`, sitting next to the Applet's Python. It owns the Applet's
metadata and, for calculators, the **full** Input schema (ADR-0004).

### 4.1 `[applet]`

```toml
[applet]
type        = "calculator"        # required; "documentation" | "calculator"
name        = "Pipe-bender setback"   # required; display name
description = "Setback and offset marks for a lever pipe bender."   # optional
author      = "andy"              # optional, free text
tags        = ["plumbing", "copper", "pipe-bending"]   # optional
```

`author` is **optional free text**, added by #8 for the error blame line (§10.3).
When absent it degrades to the Root name. It is not an identity, not validated,
and means nothing to the Host beyond display.

### 4.2 Tags

**The Host has no opinion on tag vocabulary**
([#11](https://github.com/andyalexander/workshop-helper/issues/11)). Tags are
free-form lowercase strings. The facet list is simply the tags present across the
loaded Applets — no blessed set, and an "unknown" tag is never rejected.

**One mechanical rule, and it is the semantic ceiling.** At scan the Host:

1. lowercases,
2. trims,
3. collapses internal whitespace runs to a single space.

**No kebab-casing, no stemming, no synonyms.** Anything past this needs a stemmer,
which is semantics, which is convention — not code.

Everything semantic is **unenforced authoring convention**:

- House style is **singular** (`fastener`, not `fasteners`) — reads right as a
  facet label, and is unenforceable by construction, so it could only ever have
  been convention.
- **Prefer tags that partition.** No Host floor or ceiling; #2's `leaves nothing`
  guard rail surfaces dead weight where the user can act on it.
- **`metric` / `imperial` are ordinary weak strings with no special status.** #5 is
  the sole home of unit semantics, and a unit tag would lie (BSP is
  imperial-*designated* yet metric-adjacent). The UK mixed-unit trap dissolves
  here the same way locale dissolved in #10 — by refusing to elevate unit systems
  above plain strings.

**Cross-Root collisions: accept the mess, one global flat pool.** `imp` and
`imperial` are simply two tags. Reconciliation is rejected (it is the blessed
model again); namespacing by Root is rejected as a **category error** — a tag has
no single Root, and namespacing would break the co-filtering that is the entire
point of tags.

There is **no authoring-time help, because there is no authoring surface**:
Manifests are hand-edited TOML, and the Host meets tags only at scan, so
autocomplete has nowhere to render. A non-enforcing vocabulary report is a
**deferred, evidence-gated follow-on** (§12).

### 4.3 Inputs

Declared in an `[inputs.*]` pool. Every Input the Applet can use is declared
**exactly once**, whatever modes reference it.

```toml
[inputs.size]
kind    = "choice"
label   = "Pipe size"
choices = ["15mm", "22mm"]
default = "15mm"

[inputs.angle]
kind    = "number"
label   = "Bend angle"
unit    = "°"
min     = 0
max     = 180
step    = 1
default = 90

[inputs.metric_only]
kind    = "bool"
label   = "Metric only"
default = false
```

**Kinds are a closed set: `number`, `choice`, `bool`.**

`text` and `pattern` were **cut** (#24), and the gap that led to cutting them is
structural rather than inconvenient: #5's **Designation** finding converts every
plausible `text` candidate into a `choice` on contact — thread designation, pipe
size, spanner size, drill size are all *names from a standard series*, not free
text. The one escape (a free-text designation on the thread finder) is subsumed by
the search itself: if you know it is M8×1.25, enter `8` and `1.25` and it ranks
first.

The decisive argument was **additive safety**: restoring `text` later breaks no
existing Manifest, whereas shipping an unexercised `text` + `pattern` means
specifying regex flavour, anchoring, escaping, `choice` interaction and #8 failure
rendering — five places for inference to hide, none testable by anything runnable.
And `pattern` only ever existed to plug a hole `text` itself opened, so removing
the hole takes the plug with it.

| Field | Applies to | Meaning |
|---|---|---|
| `kind` | all | `number` \| `choice` \| `bool`. Required. |
| `label` | all | Display label. Required. |
| `unit` | `number` | **Display label only** — see §4.4. |
| `default` | all | Optional. Must be valid against this Input's own constraints. |
| `min`, `max` | `number` | Inclusive bounds. |
| `step` | `number` | Increment. **`step = 1` means integer.** |
| `choices` | `choice` | Required, non-empty, list of strings. |

Rules:

- **There is no `required` field.** Every Input is required by definition.
  Therefore **`compute()` always receives every declared Input of the active mode,
  already validated, never `None`.**
- **An invalid author `default` is a malformed-Manifest error** (§10.1), not a
  silent fallback. Contrast the Overlay, where an invalid entry is **silently
  dropped** (§8) — the asymmetry is deliberate and appears three times in this
  spec: the author writes once for everyone and can be told; the user's own value
  must survive any restructuring.
- **Host-side static validation hard-gates `compute()`.** `min`/`max`/`step` and
  `choice` membership are checked before the Applet runs; `compute()` never
  executes on statically-invalid input. This is what preserves "validated, never
  `None`", and it leaves `InvalidInput` (§10.2) as the *sole* path for the
  undeclarable joint case.

### 4.4 `unit` is a display label

The Host **ships no unit model**
([ADR-0006](../adr/0006-unit-is-a-display-label.md)). `unit` is shown beside the
field and carried onto Outputs. The Host never interprets or converts it.
`compute()` receives what the user entered, in the unit the Manifest declared.

Where an Applet genuinely needs dual-unit entry, it declares a unit `choice` Input
like any other and converts **inside `compute()`**.

The reason this is not an omission: most workshop "units" are **Designations**,
which have no quantity to convert. Of the true measurements that remain, thread
pitch converts **reciprocally** (`pitch_mm = 25.4 / tpi`), so the obvious generic
model — a table of multipliers per dimension — would be silently wrong in the one
calculator that needs conversion at all, and wrong in the worst possible shape:
coarse-versus-fine is a small difference, so the bad answer looks *plausible*
rather than obviously broken.

**There is no unit preference, global or per-Applet.** Save-as-defaults already
delivers the stickiness at finer-than-global granularity — imperial on the thread
finder, metric everywhere else.

### 4.5 Modes

**Simplicity is the absence of the `[modes]` section.** Modes are the general
case; a single-mode calculator declares no modes at all (§4.6).

```toml
default_mode = "single_bend"        # top-level — see the ordering rule below

[modes.single_bend]
label   = "Single bend"
inputs  = ["size", "angle"]
outputs = [
  { name = "setback", label = "Setback", unit = "mm", primary = true },
  { name = "r_centreline", label = "Radius (centreline)", unit = "mm" },
]
```

- **Inputs are referenced by name** from the pool. A shared Input is genuinely
  *one* Input — same kind, same unit, same validation — in every mode. "Does
  `angle` mean *the* bend or *each* bend?" is prose or a label, never schema
  drift, because there is only one `angle`.
- **Outputs are declared per mode**, in display order, each with `label` and
  optional `unit`. **Exactly one carries `primary = true`**: the Host renders it
  large and the rest small. The headline changes between modes because each mode
  *names* its own primary — authored, not guessed.
- **The mode selector is derived by the Host** from the `[modes.*]` sections and
  their labels. **You never declare a `mode` Input.** Modes are the single source
  of truth; there is no separate selector to fall out of sync.
- `default_mode` names the mode active on open; it defaults to the first declared.
- `compute()` receives the active mode and branches on it. **Never inspect `mode`
  for anything but branching** — it selects a calculation; it is not a value to
  compute with.
- Returned Output names that do not match the active mode's declared Outputs are a
  **malformed-Applet** condition (§10.2), not a silent gap.

Python stays pure compute: it returns values, the Host formats and ranks them.
This **strengthens** ADR-0004.

#### The ordering rule for top-level keys

Two keys in this schema are **top-level scalars**: `default_mode`, and `outputs`
on a single-mode calculator (§4.6).

> **They must appear before the first table header in the file.**

This is TOML's own rule, not the Host's, and it fails in the worst possible way.
Once `[inputs.angle]` is opened, every subsequent bare key belongs to *that*
table — so a `default_mode` written after the `[calibration.values.*]` sections
parses as `calibration.values.22mm.default_mode`. That is **valid TOML and a
silently wrong document**: no parse error, and the Host simply sees no
`default_mode`.

The Host must therefore **reject an unrecognised key inside `[inputs.*]`,
`[modes.*]` and `[calibration.values.*]` as a malformed Manifest** (§10.1), rather
than ignoring it. That check is what converts this from a silent misparse into a
greyed card naming the file. It is cheap, and it is the only defence — the author
cannot see the difference by reading their own file.

### 4.6 The degenerate cases

Three of this spec's contracts are defined so that the simple thing is the
*absence* of a section, not a second mechanism:

| Simple case | How |
|---|---|
| Single-mode calculator | No `[modes]`; top-level `inputs` + `outputs`; `compute(inputs)`. |
| Uncalibrated calculator | No `[calibration]`; `compute()` takes no `calibration` argument. |
| Unkeyed calibration | `[calibration]` with no `keyed_by`; a flat table. |
| **Static** calculator | **Zero Inputs.** It computes on open and shows a Result. |

**The Host computes on open iff every Input has a default** — which makes the
static calculator fall out of the general rule rather than needing its own path.
Note that an Overlay value counts as a default (§8), so **compute-on-open is
user-dependent**: use a partially-defaulted Applet once, save defaults, and
thereafter it computes on open for you and not for someone else. That is what
save-as-defaults is *for*, but the behaviour must be implemented knowingly.

---

## 5. Calibration

### 5.1 What calibration is

**Data measured off the physical kit in the user's own workshop.** The
discriminator is one question:

> **Must the owner correct this for their own kit?**

If yes, it is calibration and it belongs in the Manifest, where the user can
override it (§8). If no, it is **reference data and stays a plain dict in
Python**.

The word is load-bearing: **`calibration`, not `constants`**. A "constant" the
user is expected to edit is a contradiction, and the name would attract a junk
drawer.

The boundary this draws:

| Example | Where | Why |
|---|---|---|
| Bender radius `r_centreline` | `[calibration]` | Your bender is 25% off the textbook figure (#22). |
| Copper OD per size (`15mm` → 15.0) | Python dict | 15mm pipe is 15mm everywhere on earth. |
| Thread pitch tables, tap drill sizes | Python dict | A thread standard is not a property of your bench. |

### 5.2 Schema

```toml
[calibration]
keyed_by = "size"        # optional; names a `choice` Input

[calibration.values.15mm]
r_centreline = 70.0

[calibration.values.22mm]
r_centreline = 110.0
```

The fixed `values` level exists so a key can **never** collide with a metadata
field such as `keyed_by`.

`keyed_by` is **optional** — omitted means a flat table (§4.6). **Exactly one key
is permitted; multi-key is refused**, because a two-dimensional lookup is a lookup
*table* wearing a hat, which is reference data arriving by the side door (§1.1).

**The Host branches on `keyed_by`'s *presence*, never on the shape of what follows.**
A typo'd `keyd_by` must be loud, not silently treated as a flat table.

### 5.3 Discovery-time validation

Four rules, all producing a greyed card (§10.1):

1. `keyed_by` names an **existing** Input.
2. That Input is a **`choice`**.
3. **The key set equals the choice set exactly, in both directions.**
4. **The table is rectangular** — every key carries the same field names.

Rule 4 is the non-obvious one. A ragged table makes the *shape* of the resolved
dict depend on the user's selection — a `KeyError` that fires only for the person
who owns the other bender and never once in the author's own testing.

Rule 3 is where §1.2 lands in the schema: you cannot offer `28mm` in the `size`
choices and leave its calibration blank. **Either you have measured it or it is
not a choice.**

Nothing validates that `70.0` is a *plausible* radius. No Manifest rule ever
substitutes for a physical bender.

### 5.4 Resolution and arity

**The Host resolves the slice; `compute()` receives a flat dict.** Because rule 3
validated the key/choice match at discovery, `calibration[size]` **cannot** fail —
so making the Applet index it would hand back a `KeyError` path the validation had
just eliminated.

**Arity is Manifest-determined.** The Manifest declares and Python conforms
(ADR-0004); this is not signature introspection, and a mismatch is a
malformed-Applet condition (§10.2).

| `[modes]` | `[calibration]` | Signature |
|---|---|---|
| — | — | `compute(inputs)` |
| — | ✓ | `compute(inputs, calibration)` |
| ✓ | — | `compute(mode, inputs)` |
| ✓ | ✓ | `compute(mode, inputs, calibration)` |

This dodges both traps: four separate declared signatures, and the
always-pass-`{}` tax that would make every simple calculator pay for a feature it
does not use.

### 5.5 The Calibration UI, and the sync wart

A **Calibration UI is forced, not chosen.** ADR-0007 makes JSON Host-owned and
machine-written, so "just hand-edit `overlay.json`" would break that rule by its
own logic. Therefore:

- A **collapsed per-Applet Calibration disclosure**, showing the **active key
  only**, with **reset-to-the-author's-value** beside each field.
- **It carries no explanatory prose about provenance.** The affordance already
  says it: a control labelled *reset to the author's value*, sitting beside a box
  for your own measurement, has already told you the number might not be yours.
  And #18's test applies in miniature — **a sentence can be wrong about context in
  a way an editable field cannot** (#23).

**The sync wart, accepted knowingly.** `r_centreline` describes a lump of steel,
not a computer, but the Overlay is per-machine. Correct it on the Mac and the
Linux box is still wrong — **and the way that surfaces is a mis-cut pipe.**
Obvious in the design, baffling at the bench. Blast radius is one number,
re-corrected once per machine.

---

## 6. The Result contract

```python
Result(
    outputs={...},      # required: name -> value
    table=None,         # optional
    html=None,          # optional  — the pressure valve (§1.3)
    graphic=None,       # optional
)
```

- **`outputs`** — a dict of the active mode's declared Output names to values.
  Guaranteed present. The Host formats, labels, units and ranks them; the Applet
  returns raw values only.
- **`table`** — a header row plus rows, for genuinely tabular results. Rendered
  generically.
- **`html`** — a string embedded **verbatim**. The Host performs no validation, no
  sanitisation, and promises nothing about rendering. That nil specification
  surface is exactly why it may ship uncovered (§1.6). The trust model is out of
  scope (§12).
- **`graphic`** — an **SVG string**; a PNG data URI is also accepted. The Host
  embeds it and **ships no graphics dependency**.

**`compute()` only ever *returns* a `Result`.** Problems raise (§10.2). There is
no error variant of `Result`: an error variant forces a union return type on every
Applet and invites overuse.

### 6.1 Graphics: what `workshop_utils` owes authors

**Nothing.** An author builds SVG with f-strings and `<path>`.

A declarative diagram model is the small-language door on its fifth push — a
*drawing* language fails exactly the way a *logic* language does. Drawing
**primitives** are more defensible, and are refused **now** on this project's own
evidence-gated pattern: with exactly one Applet that has a geometry, primitives
extracted from a sample of one would be shaped like the pipe-bender, which is the
worst possible moment to fix an interface.

Hypothesis recorded so it is not re-argued from scratch:
*dimension-with-arrow-and-label is plausibly the only primitive every geometric
calculator wants — extract `workshop_utils.svg` when a second one needs it.*

### 6.2 There is no advisory channel

There is **no** channel for the Applet to say *"careful, this is approximate"* or
*"below tolerance, don't worry"*. Emit a **number** as a secondary Output instead.

A number in the existing model is **showing your working, not giving advice**, and
it fails safe, because **a number cannot be wrong about context the way a sentence
can**.

**Two tickets wanted an advisory-prose channel and both premises dissolved** —
#23's when both calibration rows turned out to be measured, and #18's when the
pipe-bender's case stopped being marginal. This is therefore recorded as a
**watched-for pressure with two dissolved instances**, so that a third arrival is
recognised *as the third push* rather than argued fresh. `html` remains the
pressure valve, and that is one of the two reasons it is not cut (§11).

---

## 7. The Applet contract

### 7.1 What an Applet may import

**stdlib + `workshop_utils`. Nothing else.** There is **no dependency mechanism,
and that is a decision, not an oversight**
([#6](https://github.com/andyalexander/workshop-helper/issues/6)).

`workshop_utils` is a **distinct top-level package**, shipped from the same
project (one wheel, two top-level packages). It is the **only** Host-owned name an
Applet may import, which puts the public/private boundary in the **namespace**
rather than only in prose: **if you typed `workshop_helper`, you are off
contract.**

**The Host's own dependencies are private implementation.** `import markdown_it`
will work, purely as an accident of sharing a process — and it is off-contract, so
it may break on any Host upgrade with no error and no warning. This is a
deliberate silent case. Blessing a subset would mean owing compatibility on
Flask's version: the tax that was refused, arriving by the back door.

**Vendoring is unblessed and unpoliced. There is no enforcement and no checker.**
An AST check over `sys.stdlib_module_names` stays a cheap follow-on if a
contributed Root ever justifies it (§12).

### 7.2 Packaging and import

Applets are **multi-file** and are **imported as a package named by the Applet
id**. Namespacing by id is what stops two Roots' `helpers.py` colliding in
`sys.modules` and one silently running the other's code.

Import is **lazy — on open, never at scan** (§2.6). There is deliberately **no
startup import check**: with no declared dependency list there is nothing to check
against, and checking would mean importing everything, which is the cost ADR-0004
exists to avoid.

### 7.3 The `workshop_utils` surface

`workshop_utils` **may be a facade over a Host dependency**, bound by the
**no-leak rule**:

> **No third-party type appears in any signature, return value, or exception.**

`render_markdown(text: str) -> str`, never `-> MarkdownIt`. This is what keeps the
underlying library swappable.

Minimum surface:

| Name | Purpose |
|---|---|
| `Result` | §6. |
| `InvalidInput(message, inputs=[...])` | §10.2. |
| `render_markdown(text: str) -> str` | Markdown → HTML, over markdown-it-py. |

---

## 8. The Overlay

**The Host never writes to a Manifest**
([ADR-0007](../adr/0007-manifests-read-only-user-overrides-in-overlay.md)). Every
user override goes to `overlay.json`.

**One rule beats a taxonomy: every Root is read-only to the Host** — built-in,
your own, and cloned alike. No writability probing, no per-Root declaration.

```json
{
  "pipe-bender": {
    "defaults":    { "size": "22mm", "angle": 45 },
    "calibration": { "22mm": { "r_centreline": 108.5 } }
  }
}
```

- **Keyed by Applet id alone**, no provenance in the key. Ids are already unique
  across the loaded set (§2.7).
- **Namespaced by override kind**, so calibration can land beside input defaults
  without colliding — an Applet may legitimately have both an Input and a
  calibration field named `r_centreline`.
- **Invalid or unrecognised entries are dropped. Silently. Never an error, never
  reported.** An Overlay entry can rot with nobody at fault: the author may rename
  a key, narrow `max` from 90 to 45, change a `number` to a `choice`, or drop the
  Input — all while the Manifest stays perfectly valid. The form already shows the
  value in use, and re-saving is one click.
- **Orphans are never pruned.** A missing Applet is not evidence it is gone — its
  Root may be unmounted, not yet cloned on this machine, or listed in config but
  absent.
- **No version field, and no migration story.** The drop rule *is* the migration
  strategy.

### 8.1 Calibration merges field-level

Calibration overrides merge **field by field, not slice replacement**. If the
author later adds a second field to the `22mm` slice, slice replacement would
silently strip every user's correction.

Overlay calibration is **sparse, and rule 4 of §5.3 pointedly does not apply to
it**: the Manifest is authored once for everyone, while the Overlay is one
person's measurement that must survive any restructuring the author performs.
**Sparse-and-silent is what makes "always safely discardable" true.**

### 8.2 The discardable invariant

**Deleting the Overlay returns the Host to a pristine working state.** Nothing the
Host cannot reconstruct from Manifests ever lives only in the Overlay.

This is what makes `git pull` and `uv tool upgrade` safe *by construction* rather
than by care: the worst a schema change can do is cost a saved value.

> **Known, deferred cost** (#10): the single-folder layout weakens this. Reset is
> now "delete `overlay.json`", not "delete the folder" — because the folder also
> holds your own Root and your config. Update-safety is unaffected; only the
> one-gesture reset is.

---

## 9. The shell UI

Decided in [#2](https://github.com/andyalexander/workshop-helper/issues/2), amended
by #11.

**A facet sidebar**, not a query-first command palette and not a tag-cloud landing
page.

- **The filter is a token input over the tag vocabulary, not a text box.** Type
  `imp` ↵ for `imperial`, `cop` ↵ for `copper`. **Prefix beats substring.**
  Backspace drops the last chip.
- **Facets AND** — with a guard rail. Each candidate shows what it would leave
  **before you commit**: `↵ copper — leaves nothing`. A dead end recovers in one
  click. This guard rail is not a nicety: ADR-0003 leaves **no hierarchy to fall
  back on**, so an empty result set has no natural "go up a level".
- **Unmatched text falls back to full text** over name + description + tags + the
  **`content.md` body** (§2.6).
- **Root is a single-valued facet** (#11) — provenance is single-valued, which is
  the textbook case for a facet. It AND-combines with #2's existing machinery,
  giving "filter to a Root's Applets and their tags" for free with no new control.
- **Own-Root tags carry an inline marker** — badge primary, colour reinforcing
  (colourblind-safe). Display-only; **filtering stays global**.
- **The sidebar persists on the Applet page**, so you jump sideways rather than
  going "back".
- **Save-as-defaults is an explicit strip under the Inputs** — the same place on
  every calculator.
- The **Calibration disclosure** (§5.5) sits below that, collapsed.

> The prototype at [`prototype/shell-ui`](https://github.com/andyalexander/workshop-helper/tree/prototype/shell-ui)
> is **known-stale and deliberately not re-cut**: it exposes `R_outside` as a user
> Input, which #15 ruled out (it is calibration, not an Input). Read it as a
> *receipt* for the shell UI decision, **never** as a source of truth for the input
> schema.

---

## 10. Error handling

**Broken Applets and healthy refusals share one channel: blessed exceptions from
`workshop_utils`.** Nothing vanishes silently — but **the Host only greys what it
can detect at scan.**

### 10.1 Discovery-time faults → greyed, un-openable card

Detected while building the index, without importing anything:

- malformed or incomplete `manifest.toml`
- unknown Applet type
- missing `content.md` (documentation) or `applet.py` (calculator)
- invalid author `default` (§4.3)
- any calibration rule from §5.3
- `[calibration]` on a `documentation` Applet (§3.1)
- shadowed by a higher-tier Root (§2.7) — *"shadowed by Root 'X'"*

The card is **greyed and un-openable**, and remains **searchable by folder name**
even when the Manifest will not parse — which is the only handle left when there
is no name to search.

### 10.2 Open- and compute-time faults → error on the Applet page

Detected only when the Applet is actually opened or run:

- `ImportError` from the lazy import (§7.2)
- a raise at import time
- `compute()` crashing
- returned Output names not matching the mode's declared Outputs (§4.5)
- `compute()` arity not matching what the Manifest declared (§5.4)

The card looks normal in the browse view. **Detecting these at scan would mean
eagerly importing and running every Applet, which is precisely what ADR-0004 and
#6 refused.**

**`InvalidInput(message, inputs=[...])` is the one healthy refusal.** It is
deliberately **field-targeted** — the Host renders the message inline against the
named Input(s), exactly like a `min`/`max` failure. This is *"refuse, don't
round"*: a geometrically impossible step gets a specific message against `offset`,
not a plausible wrong number.

**Any other exception is an unplanned crash.**

`InvalidInput` exists because there is exactly one gap that static validation
cannot reach: a **cross-field** condition. That is not expressible in the Manifest
(§1.1) and the Result has no channel to report it (§6). So it is an exception, and
it is the *only* dynamic rejection path — Host-side static validation hard-gates
`compute()`, so everything declarable has already been caught (§4.3).

### 10.3 The error surface

**One layered surface, not two audiences.** A local single-user tool cannot
authenticate "user" versus "author", and pretending otherwise produces two
half-surfaces:

```
⚠ Pipe-bender setback — from Root 'mate-collection', by dave

  ▸ Details
```

- A plain **blame line**: *"[Applet] from Root '[root]', by [author]"*. `author`
  falls back to the Root name when absent.
- A **collapsed Details disclosure** carrying the **full traceback**. It is your
  own machine; there is no leak concern, and the trust model is out of scope
  (§12).

### 10.4 Deliberate silent cases

Recorded so they are not "fixed" by mistake:

| Case | Why silent |
|---|---|
| Invalid Overlay entry (§8) | Nobody is at fault; the form shows the value in use. |
| Orphaned Overlay entry (§8) | Absence is not evidence of removal. |
| `import markdown_it` breaking on upgrade (§7.1) | Off-contract by construction; there is no contract to report against. |
| A folder with no `manifest.toml` (§2.5) | It is not an Applet. |

---

## 11. The worked examples

Three Applets ship in the built-in Root. They exist to **validate the contracts**,
and each feature in each of them earns its place by covering a contract nothing
else covers (§1.6, §1.7).

### 11.1 `thread-pitch` — `documentation`

`manifest.toml` + `content.md` + assets, **zero code**. Covers the documentation
rendering contract, markdown rendering via `workshop_utils`, asset serving, and
the content-body indexing that #2's full-text fallback depends on (§2.6).

### 11.2 `pipe-bender` — `calculator`, the kitchen sink

**Deliberately the kitchen sink.** This is not a failure of restraint — the bar is
contract coverage (§1.6), and this Applet is the *only* thing exercising modes,
`keyed_by`, Overlay field-level merge, `InvalidInput`, the graphic, `min`/`max`/
`step`, compute-on-open, and the **four-argument `compute(mode, inputs,
calibration)` that nothing else in the project reaches**.

If an example must be this big to cover the surface, **that is evidence about the
framework's surface area, not about the example's size.**

The domain content it commits to:

- **`setback = R_c × tan(θ/2)`**, measured **to the vertex of the two
  centrelines**. `R_c` is the **centreline** radius. The earlier "outside edge"
  reading was inference and was **falsified at the bench** (#17).
- **Calibration: `r_centreline` — 15mm = 70.0, 22mm = 110.0. Both measured.**
- **`28mm` is not offered**, because nobody has measured one, and §1.2 forbids
  deriving it. `R_c/OD` is 4.667 and 5.000 on the two known benders — a two-point
  fit would "predict" 144.3mm, and that number is worthless.
- **One committed offset convention, the UK trade one**:
  `mark gap = D·cosec θ − 1×gain`, marks on straight pipe, mark-both-then-bend.
  Emitting both conventions was rejected: #12 requires exactly one `primary`, so
  two unranked headline numbers means the Applet **declined to answer** and handed
  a convention judgement to someone standing at a bench holding a pipe. It is not
  free either — 0.3mm at 22.5°, but **2.7mm at 45° and 6.7mm at 60°**, so above
  30° "just pick one" blows the ±2mm trade tolerance.
- **`gain` is a secondary Output** — showing your working (§6.2).
- **The Applet's real value is emitting a multiplier that is not transposed.** The
  multipliers circulating in the trade are transposed at 30°/60° (`1.2` taught for
  30° where `1/sin 30° = 2`), which is a **31–64mm** error against a ±2mm
  tolerance — and it is **invisible at 45°**, the fixed point of the swap and the
  only angle ever demonstrated.
- **Accepted cost:** a Measure-Bend user is wrong by one `gain`, up to 6.7mm at
  60°, and **the graphic is the only safeguard** — it shows both marks on straight
  pipe, so if that is not how you work, the picture does not match what you are
  doing.

### 11.3 `thread-finder` — `calculator`

`diameter` (number, mm) + `pitch` (number, mm) + **`metric_only` (bool, default
`false`)** → a ranked **`table`** of nearest thread candidates with tap drill
sizes.

Covers the **`table`** Result channel and the **`bool`** Input kind — the two
contracts that had no runnable consumer (#24). The owner asked for this Applet;
the coverage hole did not manufacture it (§1.7).

**The default is load-bearing, and it is the UK mixed-unit reality doing the
work.** The finder's real job is an *unknown* fastener off old kit, so BSW, BA and
UNF must show unless suppressed. Default-off also keeps compute-on-open intact
(§4.6). A series `choice` was rejected as the route: it is trivially available
under #5 anyway and leaves the `bool` gap exactly where it was.

> **Its reference data is not settled** — see
> [#25](https://github.com/andyalexander/workshop-helper/issues/25). That is
> **content, not framework**: under §5.1's boundary a thread standard is not a
> property of your bench, so it is a plain Python dict, and no contract in this
> document depends on it.

### 11.4 The simple path is inline, not a fourth Applet

The kitchen sink is the only calculator anyone will copy, which leaves the simple
path demonstrated by nothing. It is shown **here, as inline TOML**, and **that is
not coverage** (§1.6) — every contract inside it is already exercised by the
pipe-bender.

**This is also a complete calculator:**

```toml
# Top-level keys come first — see §4.5's ordering rule.
outputs = [
  { name = "allowance", label = "Bend allowance", unit = "mm", primary = true },
]

[applet]
type = "calculator"
name = "Sheet metal bend allowance"
tags = ["metalwork"]

[inputs.thickness]
kind    = "number"
label   = "Material thickness"
unit    = "mm"
min     = 0.1
default = 1.5

[inputs.angle]
kind    = "number"
label   = "Bend angle"
unit    = "°"
min     = 0
max     = 180
step    = 1
default = 90
```

```python
from workshop_utils import Result

def compute(inputs: dict) -> Result:
    ...
    return Result(outputs={"allowance": allowance})
```

No `[modes]`, no `[calibration]`, `compute(inputs)`, every Input defaulted so it
computes on open. Three sections and one function.

### 11.5 Coverage matrix

The test for #9, and for any future example: **does every feature map to a
contract nothing else covers?**

| Contract | Covered by |
|---|---|
| `documentation` render, assets, content indexing | `thread-pitch` |
| `calculator` render, form, round-trip | all three |
| `number` Input, `min`/`max`/`step` | `pipe-bender`, `thread-finder` |
| `choice` Input | `pipe-bender` |
| `bool` Input | **`thread-finder`** |
| Modes, derived selector, per-mode primary | `pipe-bender` |
| `[calibration]` + `keyed_by` | `pipe-bender` |
| Four-argument `compute(mode, inputs, calibration)` | **`pipe-bender` only** |
| Overlay defaults | all calculators |
| Overlay calibration, field-level merge | `pipe-bender` |
| `InvalidInput` | `pipe-bender` |
| Result `outputs` | all calculators |
| Result `table` | **`thread-finder`** |
| Result `graphic` (SVG) | `pipe-bender` |
| Compute-on-open | `pipe-bender`, `thread-finder`, inline example |
| Single-mode / uncalibrated degenerate path | inline TOML — **not coverage** |
| Result `html` | **nothing, deliberately** — §11.6 |

### 11.6 Why `html` ships uncovered

Two reasons, and both are stronger than "we ran out of examples".

1. **It passes the nil-surface test** (§1.6). Its entire contract is *"the Applet
   returns a string; the Host embeds it verbatim and promises nothing."* There is
   no validation, no sanitisation and no rendering rule for an implementer to
   infer wrongly.
2. **It is already load-bearing in decisions that are made.** #23 and #18 *both*
   disposed of a demand for an advisory-prose channel by pointing at it (§6.2).
   **Cut `html` and that tripwire has nothing behind it**, so the third push would
   force a brand-new contract to be designed under pressure.

And it inverts the usual reading of coverage: a flagship example using `html`
would *cause* the exact failure §1.3 is guarding against. **Its correct coverage
count is zero.**

---

## 12. Deliberately not specified

Not oversights. Each is either ruled out of scope or gated on evidence that does
not exist yet.

| Item | Status |
|---|---|
| **Trust model for contributed Applet code** | **Open, unresolved.** A `calculator` runs arbitrary Python from a cloned Root, and #6 *widened* this: Applets are multi-file packages and vendoring is unpoliced, so a cloned Root may carry unauditable copied code. Accepted knowingly (the author is overwhelmingly the user), but it is now the only thing standing between a cloned Root and arbitrary execution. |
| **Collection distribution and versioning** | Out of scope. How a foreign Root is updated over time is unsolved. |
| **A stdlib-only AST checker** (#6) | Evidence-gated follow-on, ~30 lines. Build it when a contributed Root justifies it. |
| **A tag vocabulary report** (#11) | Evidence-gated follow-on — `doctor`-style, or a line in the startup summary. Non-enforcing by definition. |
| **`workshop_utils.svg` drawing primitives** (#18) | Extract when a *second* Applet with a geometry needs them, not before (§6.1). |
| **An authoring skill** (#12) | Deferred. The authoring guide is the current form. |
| **Calibration rows for unmeasured kit** (#23) | Left as fog. A 28mm owner guessing `4 × OD = 112` creates a textbook row the Host cannot distinguish from a measured one — attacked at the *mechanism* (§1.2 forbids the derivation that generates the guess) rather than at the state. |
| **Restoring `text` / `pattern`** (#24) | Additive-safe. Breaks no existing Manifest, so it can wait for a real case. |
| **Overlay sync between machines** (#15) | Accepted wart (§5.5). |
| **A default port number** | The one free implementation choice (§2.3). |

### 12.1 Two watched-for pressures

Recorded so a third arrival is recognised as the third push, not argued fresh:

1. **An advisory-prose channel on the Result.** Two instances, **both premises
   dissolved** — #23's when both calibration rows turned out to be measured, and
   #18's when the pipe-bender's case stopped being marginal (§6.2).
2. **A small language in the Manifest.** Six pushes, six refusals (§1.1). The next
   one will not look like the last one; it will look like data that just needs
   evaluating.

---

## 13. Source index

Reasoning lives in these; this document restates only their conclusions.

**ADRs** — [0001](../adr/0001-local-browser-ui-foreground-process.md) ·
[0002](../adr/0002-pure-python-applets-server-round-trip.md) ·
[0003](../adr/0003-applets-are-folders-tags-not-hierarchy.md) ·
[0004](../adr/0004-declarative-manifest-owns-input-schema.md) ·
[0005](../adr/0005-applet-types-are-closed.md) ·
[0006](../adr/0006-unit-is-a-display-label.md) ·
[0007](../adr/0007-manifests-read-only-user-overrides-in-overlay.md)

**Decision tickets** — [#2](https://github.com/andyalexander/workshop-helper/issues/2) shell UI ·
[#3](https://github.com/andyalexander/workshop-helper/issues/3) library stack ·
[#4](https://github.com/andyalexander/workshop-helper/issues/4) setback geometry ·
[#5](https://github.com/andyalexander/workshop-helper/issues/5) input schema ·
[#6](https://github.com/andyalexander/workshop-helper/issues/6) dependencies ·
[#7](https://github.com/andyalexander/workshop-helper/issues/7) Overlay ·
[#8](https://github.com/andyalexander/workshop-helper/issues/8) error handling ·
[#10](https://github.com/andyalexander/workshop-helper/issues/10) Host config ·
[#11](https://github.com/andyalexander/workshop-helper/issues/11) tags ·
[#12](https://github.com/andyalexander/workshop-helper/issues/12) modes ·
[#13](https://github.com/andyalexander/workshop-helper/issues/13) offset convention ·
[#15](https://github.com/andyalexander/workshop-helper/issues/15) calibration ·
[#17](https://github.com/andyalexander/workshop-helper/issues/17) bench test ·
[#18](https://github.com/andyalexander/workshop-helper/issues/18) graphic + coverage bar ·
[#22](https://github.com/andyalexander/workshop-helper/issues/22) calibration surface ·
[#23](https://github.com/andyalexander/workshop-helper/issues/23) provenance ·
[#24](https://github.com/andyalexander/workshop-helper/issues/24) uncovered contracts

**Research** — [`library-stack.md`](../research/library-stack.md) ·
[`pipe-bender-setback.md`](../research/pipe-bender-setback.md) ·
[`pipe-bender-offset.md`](../research/pipe-bender-offset.md)

**Authoring** — [`calculator-modes.md`](../authoring/calculator-modes.md)
(⚠️ predates #17/#22 — its `r_outside` field name and its `28mm` row are both
superseded by §11.2).
