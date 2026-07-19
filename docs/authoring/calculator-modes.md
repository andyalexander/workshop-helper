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
[ADR-0006](../adr/0006-unit-is-a-display-label.md) (`unit` is a display label), and
the input-schema contract in
[issue #5](https://github.com/andyalexander/workshop-helper/issues/5).

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
[applet]
type   = "calculator"
name   = "Pipe-bender setback"
author = "andy"
tags   = ["plumbing", "copper", "pipe-bending"]

# --- The Input pool: every Input this Applet can use, declared once. ---

[inputs.size]
kind    = "choice"
label   = "Pipe size"
choices = ["15mm", "22mm", "28mm"]
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

# --- The modes: each names its Inputs and its Outputs. ---

default_mode = "single_bend"

[modes.single_bend]
label   = "Single bend"
inputs  = ["size", "angle"]
outputs = [
  { name = "setback",       label = "Setback",             unit = "mm", primary = true },
  { name = "r_outside",      label = "Radius (outside)",    unit = "mm" },
  { name = "r_centreline",   label = "Radius (centreline)", unit = "mm" },
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

## The compute function

`compute()` is told which mode is active and branches on it. It receives every
Input **of the active mode**, already validated and never `None` (issue #5), and
returns a `Result` whose named Outputs match that mode's declared Outputs.

```python
from workshop_utils import Result, InvalidInput

# Per-installation calibration: the former radius keyed off pipe size.
# The former *is* the radius, so the pipe size fully specifies it (issue #15).
R_OUTSIDE = {"15mm": 70.0, "22mm": 99.0, "28mm": 130.0}
OD = {"15mm": 15.0, "22mm": 22.0, "28mm": 28.0}


def compute(mode: str, inputs: dict) -> Result:
    """Return the Result for the active mode."""
    size = inputs["size"]
    angle = inputs["angle"]
    r_outside = R_OUTSIDE[size]

    if mode == "single_bend":
        setback = r_outside * tan(radians(angle) / 2)
        return Result(outputs={
            "setback": setback,
            "r_outside": r_outside,
            "r_centreline": r_outside - OD[size] / 2,
        })

    if mode == "step":
        offset = inputs["offset"]
        mark_distance = offset / sin(radians(angle))
        # A step can be geometrically impossible: refuse, don't round (issue #8).
        min_step = ...  # smallest achievable step at this angle
        if offset < min_step:
            raise InvalidInput(
                f"Offset must be at least {min_step:.0f}mm at {angle}°.",
                inputs=["offset"],
            )
        return Result(outputs={
            "mark_distance": mark_distance,
            "setback_per_bend": r_outside * tan(radians(angle) / 2),
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
- [ ] `compute(mode, inputs)` branches on `mode`; single-mode uses `compute(inputs)`.
- [ ] Returned Output names match the active mode exactly.
- [ ] Impossible-but-typed input raises `InvalidInput`, not a bare error.
