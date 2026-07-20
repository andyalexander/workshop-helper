# Authoring a calculator with modes

A `calculator` Applet can offer more than one **mode** — a named way of using the
same tool, where the Inputs *and* the Outputs both change. The pipe-bender is one
tool in the hand, but you either pull a single bend or set out a step; each needs
different Inputs and produces a different headline number. Modes let one Applet
carry both without splitting into two.

This guide is the pattern to copy. The contract behind it is decided in
[issue #12](https://github.com/andyalexander/workshop-helper/issues/12); the rules
here follow [ADR-0004](../adr/0004-declarative-manifest-owns-input-schema.md)
(the Manifest owns the schema, Python is pure compute),
[ADR-0006](../adr/0006-unit-is-a-display-label.md) (`unit` is a display label), the
input-schema contract in
[issue #5](https://github.com/andyalexander/workshop-helper/issues/5), and the
calibration contract in
[issue #15](https://github.com/andyalexander/workshop-helper/issues/15).

## The one thing to remember

**Simplicity is the absence of the `[modes]` section.** If your calculator does
one thing, declare Inputs and Outputs at the top level and never type the word
"mode" (see [Single-mode calculators](#single-mode-calculators-the-common-case)).
Reach for modes *only* when the same tool genuinely has two shapes.

## The shape

Modes build on three ideas:

1. **Define every Input once**, in an `[inputs.*]` pool.
2. **Each mode references a subset** of those Inputs by name, and declares its own
   Outputs.
3. **The Host derives the mode selector** from the modes you declare — you never
   write the selector yourself.

Here is the pipe-bender, complete:

```toml
# Top-level scalars must appear before the first table header — see
# "The ordering rule" below. This is TOML's rule, and it fails silently.
default_mode = "single_bend"

[applet]
type   = "calculator"
name   = "Pipe-bender setback"
author = "andy"
tags   = ["plumbing", "copper", "pipe-bending"]

# --- The Input pool: every Input this Applet can use, declared once. ---

[inputs.size]
kind    = "choice"
label   = "Pipe size"
choices = ["15mm", "22mm"]   # only sizes with a *measured* former (see below)
default = "15mm"

[inputs.angle]
kind    = "number"
label   = "Bend angle"
unit    = "°"
min     = 0
max     = 180
step    = 1        # step = 1 makes it an integer (see issue #5)
default = 90

[inputs.offset]
kind    = "number"
label   = "Offset (step height)"
unit    = "mm"
min     = 0
default = 50

# --- Calibration: measured off the bender in *your* workshop, keyed by
#     the Input that selects it. See "Calibration" below. ---

[calibration]
keyed_by = "size"

[calibration.values.15mm]
r_centreline = 70.0

[calibration.values.22mm]
r_centreline = 110.0

# --- The modes: each names its Inputs and its Outputs. ---

[modes.single_bend]
label   = "Single bend"
inputs  = ["size", "angle"]
outputs = [
  { name = "setback",      label = "Setback",             unit = "mm", primary = true },
  { name = "r_centreline", label = "Radius (centreline)", unit = "mm" },
]

[modes.step]
label   = "Step (offset)"
inputs  = ["size", "angle", "offset"]
outputs = [
  { name = "mark_distance",    label = "Distance between marks", unit = "mm", primary = true },
  { name = "setback_per_bend", label = "Setback per bend",       unit = "mm" },
  { name = "min_step",         label = "Smallest step at this angle", unit = "mm" },
]
```

### Why Inputs live in a pool

`size` and `angle` are used by both modes. Declaring them once and referencing them
by name means they are *the same Input* — same kind, same unit, same validation —
in every mode that uses them. "The angle means *the* bend in one mode and *each*
bend in the other" is a difference of meaning you explain in prose or a label, never
a difference the schema has to track. There is no way for the two modes to disagree
about what `angle` is, because there is only one `angle`.

### Outputs are declared, per mode

Within a mode the Output set is fixed — you list exactly the Outputs that mode
produces. Each Output carries its `label` and `unit` (the Host formats it; ADR-0006)
and the list order is the display order. Exactly one Output per mode is marked
`primary = true`: the Host renders it large, the rest small. The headline changes
between modes because each mode names its own primary — `setback` for a single bend,
`mark_distance` for a step — and that is authored, not guessed.

### The selector is derived — don't declare it

You do **not** write a `mode` Input. The Host reads your `[modes.*]` sections and
renders the selector from their `label`s automatically. This keeps the modes as the
single source of truth: you cannot declare a mode and forget to add it to a
selector, because there is no separate selector to keep in sync. Set `default_mode`
to the mode active when the Applet opens (it defaults to the first one declared).

### The ordering rule — the trap that costs an afternoon

`default_mode` is a **top-level scalar**, and so is `outputs` on a single-mode
calculator. Both must be written **before the first table header in the file**.

This is TOML's own rule, not the Host's, and it fails in the worst possible way.
Once `[calibration.values.22mm]` is opened, every bare key that follows belongs to
*that* table — so a `default_mode` written below it parses as
`calibration.values.22mm.default_mode`. That is **valid TOML producing no error**:
the Host simply sees no `default_mode` and silently opens on the first mode, while
the calibration key quietly grows a field its siblings lack, breaking the
same-fields rule below.

**You cannot see the difference by reading your own file.** The Host therefore
rejects unrecognised keys inside `[inputs.*]`, `[modes.*]` and
`[calibration.values.*]` as a malformed Manifest, so the mistake surfaces at
discovery rather than at the bench.

## The compute function

`compute()` is told which mode is active and branches on it. It receives every
Input **of the active mode**, already validated and never `None` (issue #5), plus
the resolved `calibration` for the current key, and returns a `Result` whose named
Outputs match that mode's declared Outputs.

```python
from workshop_utils import Result, InvalidInput

# Reference data: universal, identical for every user, never corrected.
# 15mm pipe is 15mm outside diameter in every workshop on earth — so this
# stays in Python. Contrast r_centreline, which is calibration (see below).
OD = {"15mm": 15.0, "22mm": 22.0}


def compute(mode: str, inputs: dict, calibration: dict) -> Result:
    """Return the Result for the active mode."""
    size = inputs["size"]
    angle = inputs["angle"]
    # Already resolved for the selected size, and guaranteed present.
    r_centreline = calibration["r_centreline"]

    if mode == "single_bend":
        setback = r_centreline * tan(radians(angle) / 2)
        return Result(outputs={
            "setback": setback,
            "r_centreline": r_centreline,
        })

    if mode == "step":
        offset = inputs["offset"]
        mark_distance = offset / sin(radians(angle))
        # A step can be geometrically impossible: refuse, don't round (issue #8).
        min_step = ...  # smallest achievable step at this angle; uses OD[size]
        if offset < min_step:
            raise InvalidInput(
                f"Offset must be at least {min_step:.0f}mm at {angle}°.",
                inputs=["offset"],
            )
        return Result(outputs={
            "mark_distance": mark_distance,
            "setback_per_bend": r_centreline * tan(radians(angle) / 2),
            "min_step": min_step,
        })
```

Rules the Host enforces around this:

- **The returned Output names must match the active mode's declared Outputs.** A
  missing or unexpected name is a malformed-Applet condition, surfaced like any
  other broken Applet (issue #8) — not a silent gap.
- **Refuse valid-typed but impossible input with `InvalidInput`**, naming the
  offending Input(s). The Host renders the message inline against that Input. This
  is a healthy refusal, not a crash (issue #8).
- **Never inspect `mode` for anything but branching.** It selects the calculation;
  it is not a data value to compute *with*.

## Calibration

**Calibration is data measured off the physical kit in the user's own workshop.**
The bender in your garage has the former radius it has; the one in mine may differ
by a couple of millimetres, and the way that difference shows up is a mis-cut pipe.

The test for whether something is calibration is one question:

> **Does the owner need to correct this for their own kit?**

If yes, it goes in `[calibration]` in the Manifest, so they can fix it **without
editing your code**. If no — if the value is the same in every workshop on earth —
it is *reference data* and stays a plain dict in `applet.py`. In the pipe-bender,
`r_centreline` is calibration and `OD` is reference data. A thread-pitch table
(`25.4 / TPI`) or a tap drill chart is reference data too: nobody ever needs to
correct the pitch of M8.

Do not put reference data in `[calibration]`. The section is narrow on purpose;
widening it into "author constants" turns it into a junk drawer and removes the
Host's ability to know what the user may override.

### Keyed and unkeyed

Calibration is **keyed** when the value depends on which piece of kit is selected.
`keyed_by` names the `choice` Input that selects it — and for the bender that is
`size`, because **the former *is* the radius**: 22mm pipe can only be bent on a
22mm former, so choosing the pipe already fully specifies it. There is no separate
"which bender" Input, and adding one would be a modelling error — it would let
someone select a combination that cannot physically exist.

If there is only ever one value, omit `keyed_by` and write a flat table:

```toml
[calibration]
backlash = 0.04
```

**Exactly one key.** There is no `keyed_by = ["size", "grade"]` — a two-dimensional
table is a lookup table, which is reference data, which belongs in Python.

### What the Host checks, and what it cannot

At discovery the Host verifies that `keyed_by` names an Input that exists, that it
is a `choice`, that **the calibration keys and the choice values match exactly in
both directions**, and that every key offers **the same field names**. Any of these
failing is a malformed Manifest: the Applet is greyed out and cannot be opened
(issue #8).

**Both directions is the demanding half, and it decides what your Inputs may
offer.** The bender above lists `15mm` and `22mm` only, because those are the two
formers that have been measured. There is no `28mm` row — and therefore `28mm`
cannot be a `choice`. The temptation is to fill the gap from the textbook
(`4 × OD = 112`), and that is exactly the move to refuse: **never derive one
calibration row from another.** These are measurements of specific lumps of steel,
not samples of a formula — on this bender the ratio is 4.667 where the book says
5.000, so a derived row is a guess wearing a measurement's clothes and the Host
cannot tell the difference. **Either you have measured it, or it is not a choice.**

That last rule — same fields for every key — is why `compute()` can index
`calibration["r_centreline"]` without a guard. If one former carried a field the
others lacked, the Applet would work for whoever owns *that* bender and crash for
everyone else, which is precisely the bug that never shows up in your own testing.

**Nothing checks that your numbers are right.** The Host has no idea what
`r_centreline` means. Only a test bend does.

### The user's correction, and one wart

When the owner corrects a value, it is written to the Host's Overlay — **never back
into your Manifest**. Your Applet can be updated, re-cloned or replaced and their
correction survives; equally, they can discard the Overlay and get your values back.
The Applet page carries a **Calibration** disclosure showing the fields for the
currently selected key, with a reset to your value.

**The wart, worth knowing:** the Overlay is per-machine. `r_centreline` describes a
lump of steel, not a computer — so someone who corrects their bender on one machine
still has the old value on another. It surfaces as a mis-cut pipe. If your Applet's
calibration is safety- or cost-relevant, say so near the value.

## Single-mode calculators (the common case)

Most calculators do one thing. They declare no `[modes]` section at all — just a
top-level `[inputs]` and `[outputs]` — and the Host renders no selector:

```toml
[applet]
type = "calculator"
name = "Tap drill size"

[inputs.thread]
kind    = "choice"
label   = "Thread"
choices = ["M3", "M4", "M5", "M6", "M8", "M10"]
default = "M6"

[[outputs]]
name    = "drill"
label   = "Tapping drill"
unit    = "mm"
primary = true
```

`compute()` for a single-mode Applet omits the `mode` argument:

```python
def compute(inputs: dict) -> Result:
    ...
```

### Your signature is whatever you declared

There is one rule behind all of this: **you receive what you declared, in
declaration order.** Both `[modes]` and `[calibration]` are optional, so there are
four possible signatures — but you never choose between them, your Manifest does:

| `[modes]` | `[calibration]` | Signature |
|-----------|-----------------|-----------------------------------|
| —         | —               | `compute(inputs)`                 |
| —         | ✓               | `compute(inputs, calibration)`    |
| ✓         | —               | `compute(mode, inputs)`           |
| ✓         | ✓               | `compute(mode, inputs, calibration)` |

If your function's signature does not match what your Manifest declares, that is a
malformed Applet and the Host says so (issue #8) — it will not quietly adapt.

Internally the Host treats this as one anonymous mode, so everything above still
holds — a single-mode calculator is just the degenerate case with the selector
hidden. **If in doubt, start here and add modes only when a second genuine shape
appears.**

## Checklist

- [ ] Do I really have two *shapes*, or just two sets of numbers? If the Inputs are
      the same, it is one mode with more Outputs, not two modes.
- [ ] Every Input declared once in `[inputs.*]`, referenced by name per mode.
- [ ] Each mode lists its Outputs, exactly one `primary = true`.
- [ ] `default_mode` set (or first mode is intended as the default).
- [ ] `default_mode` — and `outputs` on a single-mode calculator — written **above
      the first `[table]` header**. Below one, it silently parses into that table.
- [ ] Every calibration key is a value you **measured**, not one you derived from
      another row or from a textbook ratio.
- [ ] `compute()`'s signature matches what the Manifest declares — `mode` first if
      there are modes, `calibration` last if there is calibration.
- [ ] Every value the owner might need to correct for their own kit is in
      `[calibration]`, not a Python constant.
- [ ] Every value that is the same in every workshop is a Python constant, **not**
      in `[calibration]`.
- [ ] `keyed_by` names a `choice` Input, and the calibration keys match its choices
      exactly — no spare formers, no missing ones.
- [ ] Every calibration key offers the same field names.
- [ ] Returned Output names match the active mode exactly.
- [ ] Impossible-but-typed input raises `InvalidInput`, not a bare error.
