"""Setback and offset marks for a fixed-former lever bender (spec §11.2).

Resolving #4, #17, #18 and #22.

**The number has been wrong three times, and every time it was a *reference
surface*, not arithmetic.** `R × tan(θ/2)` was never in doubt; which surface `R`
is measured to, and which point the tape runs back to, is where a bender
calculator silently produces a plausible wrong figure. So one convention is
committed here and named in every label:

- `R_c` is the **centreline** radius of the former, and it is **calibration** —
  measured off the tool in this workshop, 70.0mm on the 15mm bender and 110.0mm
  on the 22mm. The textbook `4 × OD` is a setting-out convention, not a
  measurement of anything (#22).
- **`setback = R_c · tan(θ/2)`, back to the vertex of the two centrelines** —
  the mid-line, not the corner, which is how the owner marks and what falsified
  the earlier outside-edge reading at the bench (#17).
- **Offsets use the UK trade convention: both marks on straight pipe, marked
  before any bending, `mark gap = D · cosec θ − 1 × gain`.** Emitting two
  conventions was refused: exactly one Output is primary (§4.5), so two unranked
  headline numbers would hand a convention judgement to someone standing at a
  bench holding a pipe.

**What this Applet is actually worth is the multiplier it does not transpose.**
The multipliers in circulation swap 30° and 60° — `1.2` taught for 30°, where
`1/sin 30°` is `2` — which is a 31–64mm error against a ±2mm trade tolerance,
and it is **invisible at 45°**, the fixed point of the swap and the only angle
ever demonstrated. The gain correction is the smaller half of the story (0.9mm
at 30°, 11.8mm at 22mm/60°), and it is emitted as a secondary Output rather than
folded away silently — a number is showing your working, and §6.2 has no channel
for prose that would say the same thing less safely.

**The minimum step is the geometry's, not the tool's, and it says so.** `2·R_c·(1
− cos θ)` is where the two arcs meet and no straight pipe is left between them.
The owner's *measured* minimums are higher at every angle but one — 150mm against
110mm on the 22mm bender at 60° — because a lever bender needs real straight pipe
to grip and to swing the arm through. That figure is **not modelled**: it varies
with size *and* angle, and a two-dimensional table is a lookup table wearing a
hat, which §5.2 refuses as calibration by the side door. So the Output is named
for what it is, and the refusal says the bender will want more.

**Accepted cost, and why the graphic is not decoration.** Someone who bends,
measures, then bends again pays no gain, so this answer is one gain long for
them — up to 6.7mm at 60°. Nothing in the number says which method it assumes.
The picture does: it shows both marks on straight pipe, before either bend, so a
user who works the other way can see that it is not what they are doing (§1.5).
"""

from math import cos, radians, sin, tan

from workshop_utils import InvalidInput, Result

from .graphic import offset_svg, single_bend_svg

SINGLE_BEND = "single_bend"

# Reference data, not calibration: 15mm copper is 15mm outside diameter in every
# workshop on earth, so nobody ever corrects it and it stays in Python (§5.1).
# It draws the pipe; it does not enter the geometry — the wall thickness and the
# outside surface are exactly what the centreline convention removed (#4).
OUTSIDE_DIAMETER_MM = {"15mm": 15.0, "22mm": 22.0}


def compute(mode: str, inputs: dict, calibration: dict) -> Result:
    """Return the Result for the active mode.

    ``mode`` selects the calculation and is never computed *with*; ``calibration``
    arrives already resolved for the selected size (§5.4).
    """
    size = inputs["size"]
    angle = inputs["angle"]
    theta = radians(angle)
    r_centreline = calibration["r_centreline"]
    setback = r_centreline * tan(theta / 2)

    if mode == SINGLE_BEND:
        return Result(
            outputs={"setback": setback, "r_centreline": r_centreline},
            graphic=single_bend_svg(
                outside_diameter=OUTSIDE_DIAMETER_MM[size],
                r_centreline=r_centreline,
                angle=angle,
                setback=setback,
            ),
        )

    offset = inputs["offset"]
    min_step = 2 * r_centreline * (1 - cos(theta))
    if offset < min_step:
        # Refuse, don't round (§10.2). Below this the two arcs meet and there is
        # no straight left between them: the step is not tight, it is impossible,
        # and the honest answer names the two Inputs that decide it.
        raise InvalidInput(
            f"A {offset:g}mm step is not achievable at {angle:g}° on the {size} "
            f"former — the two bends would run into each other. The geometry "
            f"stops at {min_step:.0f}mm, and the bender wants more than that "
            "again to grip.",
            inputs=["offset", "angle"],
        )

    # `gain` is the whole difference between the trade's vertex-to-vertex figure
    # and a mark gap you can measure on straight pipe: the arc is shorter than
    # the two tangent legs it replaces, and marking both points first pays it
    # exactly once.
    gain = 2 * setback - r_centreline * theta
    mark_distance = offset / sin(theta) - gain
    return Result(
        outputs={
            "mark_distance": mark_distance,
            "gain": gain,
            "min_step": min_step,
        },
        graphic=offset_svg(
            outside_diameter=OUTSIDE_DIAMETER_MM[size],
            r_centreline=r_centreline,
            angle=angle,
            offset=offset,
            # The straight between the two arcs. `mark_distance` is the same
            # length seen from the other side — the arc plus this diagonal — so
            # the drawing and the headline cannot disagree.
            diagonal=(offset - min_step) / sin(theta),
            mark_distance=mark_distance,
        ),
    )
