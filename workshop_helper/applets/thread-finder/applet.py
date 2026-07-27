"""Find the thread on an unknown fastener from a caliper and a pitch gauge.

Spec §11.3, resolving #25 and #27.

**The instruments decide the design.** A caliper reads diameter — noisy,
continuous, ±0.1mm on a good day. A pitch gauge reads pitch — near-exact, and
discrete, because you are matching a leaf. So the two axes are different *kinds*
of measurement, and everything below falls out of that asymmetry:

- every series is normalised to **pitch-length in mm** (metric and BA native,
  the inch series through ``25.4 / tpi``);
- **pitch gates hard** — a near miss is dropped, not ranked low;
- **diameter orders** whatever survives.

Filtering on the exact axis and ranking on the noisy one is the one metric that
works **system-blind**, which is the whole point of an *unknown* fastener. ISO
261's coarse/fine and choice-order preferences are consciously not used: §5.2
forbids preferring coarse, and this Applet's ties are genuine physical
collisions, not orderings a preference list should paper over.

**Where it cannot tell, it says so.** 1/4" UNC and 1/4" BSW are identical in both
measurements and differ only in flank angle; so are 13 BA and M1.2. They come
back as a flagged tied group naming the discriminator — never a silent winner.
Flank angle is therefore a column and not an Input: the flow is
**resolve-then-measure**, and compute-on-open stays intact.

**The headline is the normalised pitch, not a best match.** A winner in the large
type would be the silent winner this Applet exists not to give; the pitch it
actually searched on is the number the user can check against their own gauge,
and it is where the reciprocal conversion becomes visible.
"""

from workshop_utils import Result, Row, Table

from .threads import MM_PER_INCH, THREADS, Thread

COLUMNS = (
    "Series",
    "Designation",
    "Major Ø (mm)",
    "Pitch (mm)",
    "Flank angle",
    "Tap drill (mm)",
    "Provenance",
)

TPI = "TPI"

# How hard the gate bites. A gauge reading is near-exact, so the window tracks
# the gauge's own precision rather than a user's arithmetic: 0.25mm admits
# ±0.02, 3.5mm admits ±0.07. A hand-converted 20 TPI typed as "1.3" misses 1.27
# and is dropped — which is precisely the noise `pitch_unit` exists to prevent.
PITCH_TOLERANCE = 0.02
PITCH_FLOOR_MM = 0.02

# What a caliper can actually separate. Two candidates closer than this in
# diameter are not ranked against each other; they are declared tied.
CALIPER_RESOLUTION_MM = 0.1

FLANK_ANGLE_TIE = (
    "Indistinguishable on Ø + pitch — these differ only in flank angle; "
    "check it with a gauge"
)
SERIES_TIE = (
    "Indistinguishable on Ø + pitch at caliper resolution — and they share a "
    "flank angle; the series themselves are the difference"
)


def compute(inputs: dict) -> Result:
    """Rank the candidate threads for one measurement."""
    pitch_mm = _pitch_mm(inputs["pitch"], inputs["pitch_unit"])
    candidates = _ranked(
        diameter_mm=inputs["diameter"],
        pitch_mm=pitch_mm,
        metric_only=inputs["metric_only"],
    )
    return Result(
        outputs={"pitch_mm": pitch_mm, "candidates": len(candidates)},
        table=_table(candidates) if candidates else None,
    )


def _pitch_mm(pitch: float, unit: str) -> float:
    """Convert the reading to pitch-length in mm — reciprocally, for TPI (§4.4).

    This is the conversion the Host deliberately does not own: `unit` is a
    display label, and a generic table of multipliers would be silently wrong
    here in the worst possible shape, because coarse-versus-fine is a small
    difference and a plausible-looking wrong answer is the dangerous one.
    """
    return MM_PER_INCH / pitch if unit == TPI else pitch


def _ranked(diameter_mm: float, pitch_mm: float, metric_only: bool) -> list[Thread]:
    """Gate on pitch, then order what is left by distance in diameter."""
    tolerance = max(PITCH_FLOOR_MM, PITCH_TOLERANCE * pitch_mm)
    survivors = [
        thread
        for thread in THREADS
        if abs(thread.pitch_mm - pitch_mm) <= tolerance
        and (thread.metric or not metric_only)
    ]
    return sorted(
        survivors, key=lambda t: (abs(t.major_mm - diameter_mm), t.designation)
    )


def _table(candidates: list[Thread]) -> Table:
    """Lay the candidates out, flagging each run the measurements cannot split."""
    rows: list[Row] = []
    for group in _tied_groups(candidates):
        flag = _tie_flag(group) if len(group) > 1 else None
        rows.extend(Row(_cells(thread), flag=flag) for thread in group)
    return Table(columns=COLUMNS, rows=rows)


def _tied_groups(candidates: list[Thread]) -> list[list[Thread]]:
    """Split the ranking wherever a caliper could actually tell two rows apart.

    The list is already ordered by distance in diameter, so a tie is a run of
    neighbours within caliper resolution of the run's own first row — comparing
    against the leader rather than the previous row, so that a long gentle slope
    of diameters does not chain into one enormous "tie".
    """
    groups: list[list[Thread]] = []
    for thread in candidates:
        if groups and abs(thread.major_mm - groups[-1][0].major_mm) <= (
            CALIPER_RESOLUTION_MM
        ):
            groups[-1].append(thread)
        else:
            groups.append([thread])
    return groups


def _tie_flag(group: list[Thread]) -> str:
    """Name the discriminator, which is what makes declining an answer (§11.3)."""
    if len({thread.flank_angle for thread in group}) > 1:
        return FLANK_ANGLE_TIE
    return SERIES_TIE


def _cells(thread: Thread) -> tuple[str | float | None, ...]:
    """The fixed column set (#25, #27), in order.

    Raw values: the Host formats them, and a `None` tap drill renders as an em
    dash rather than a computed figure dressed up as a lookup (#25 §3.4).
    """
    return (
        thread.series,
        thread.designation,
        round(thread.major_mm, 3),
        round(thread.pitch_mm, 3),
        f"{thread.flank_angle:g}°",
        thread.tap_drill_mm,
        thread.provenance,
    )
