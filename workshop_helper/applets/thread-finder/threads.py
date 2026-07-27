"""Thread series reference data for the finder (#25).

**This is content, not framework** (spec §11.3). A thread standard is not a
property of your bench, so under §5.1's boundary it is not calibration: it is
plain Python data inside the Applet's own package, and no Host contract depends
on a single figure below. The ranking in ``applet.py`` is written so that a
corrected figure changes an answer and never the logic.

**Provenance is carried per row, not per table** — the direct lesson of #22.
Dimensions and tap drills come from different documents for the same fastener:
ISO 262 and ISO 2306 for metric, NBS H28 and ISO 2306 for the unified series, one
manufacturer chart for both halves of Whitworth. Merging them into one unlabelled
column is how two rows on two surfaces become one column nobody can audit.

⚠ **Not yet bench-verified.** Every table here was transcribed from a retrieved
source in the #25 research session, and §6 of that document records visible OCR
damage in four of the sources. The owner's spot-check against the source page
images is outstanding (#35's last acceptance criterion). Nothing is derived: a
size with no published drill carries ``None`` and renders as an em dash, because
an empty cell is honest where ``major − pitch`` dressed as a lookup is not
(#25 §3.4).

Pitch is the axis the finder gates on, so for the inch-based series it is
computed as ``25.4 / tpi`` rather than transcribed: the published millimetre
columns are rounded restatements of exactly that reciprocal, and the rounding is
noise on the one axis that must stay exact (#27).
"""

from typing import NamedTuple

MM_PER_INCH = 25.4

METRIC = "ISO metric"
METRIC_FINE = "ISO metric fine"
UNC = "UNC"
UNF = "UNF"
BSW = "BSW"
BSF = "BSF"
BA = "BA"
BSPP = "BSPP (G)"

# Flank angle is fixed per series and is the discriminator a tied group names
# (§11.3). It is a column and never an Input: the flow is resolve-then-measure.
SIXTY = 60.0
WHITWORTH = 55.0
BA_ANGLE = 47.5

ISO_262 = "ISO 262 Table 1"
ISO_2306 = "ISO 2306"
NBS_H28 = "NBS H28-1969 Table 2.7"
ISO_228 = "ISO 228-1:2000 Table 1"
GAGE_BS84 = "Gage Crib chart citing BS 84 — secondary"
GAGE_BS93 = "Gage Crib chart citing BS 93 — secondary"
NO_DRILL = "no published drill"
PIPE_THREAD = "pipe thread — drill withheld"


class Thread(NamedTuple):
    """One thread the finder can offer, with the provenance of its own figures.

    ``metric`` is what ``metric_only`` suppresses on: the ISO metric series and
    nothing else. BA is millimetre-dimensioned and still not metric in this
    sense — it is a different standard with its own flank angle.
    """

    series: str
    designation: str
    major_mm: float
    pitch_mm: float
    flank_angle: float
    tap_drill_mm: float | None
    provenance: str
    metric: bool = False


# --- ISO metric (ISO 262 Table 1; drills from ISO 2306 Table 1) --------------

# (nominal diameter, coarse pitch, fine pitches in ISO 262's order)
_METRIC_SIZES: tuple[tuple[float, float, tuple[float, ...]], ...] = (
    (1, 0.25, ()),
    (1.2, 0.25, ()),
    (1.4, 0.3, ()),
    (1.6, 0.35, ()),
    (1.8, 0.35, ()),
    (2, 0.4, ()),
    (2.5, 0.45, ()),
    (3, 0.5, ()),
    (3.5, 0.6, ()),
    (4, 0.7, ()),
    (5, 0.8, ()),
    (6, 1, ()),
    (7, 1, ()),
    (8, 1.25, (1,)),
    (10, 1.5, (1.25, 1)),
    (12, 1.75, (1.5, 1.25)),
    (14, 2, (1.5,)),
    (16, 2, (1.5,)),
    (18, 2.5, (2, 1.5)),
    (20, 2.5, (2, 1.5)),
    (22, 2.5, (2, 1.5)),
    (24, 3, (2,)),
    (27, 3, (2,)),
    (30, 3.5, (2,)),
    (33, 3.5, (2,)),
    (36, 4, (3,)),
    (39, 4, (3,)),
    (42, 4.5, (3,)),
    (45, 4.5, (3,)),
    (48, 5, (3,)),
    (52, 5, (4,)),
    (56, 5.5, (4,)),
    (60, 5.5, (4,)),
    (64, 6, (4,)),
)

# ISO 2306 Table 1's recommended stocked drill, by nominal diameter. Four of
# these disagree with `major − pitch`, which is exactly why the table ships and
# the formula does not (#25 §3.2).
_METRIC_COARSE_DRILLS: dict[float, float] = {
    1: 0.75,
    1.2: 0.95,
    1.4: 1.10,
    1.6: 1.25,
    1.8: 1.45,
    2: 1.60,
    2.5: 2.05,
    3: 2.50,
    3.5: 2.90,
    4: 3.30,
    5: 4.20,
    6: 5.00,
    7: 6.00,
    8: 6.80,
    10: 8.50,
    12: 10.20,
    14: 12.00,
    16: 14.00,
    18: 15.50,
    20: 17.50,
    22: 19.50,
    24: 21.00,
    27: 24.00,
    30: 26.50,
    33: 29.50,
    36: 32.00,
    39: 35.00,
    42: 37.50,
    45: 40.50,
    48: 43.00,
    52: 47.00,
    56: 50.50,
}

# Only the fine-series drills #25 confirmed row-by-row; the rest of ISO 2306
# Table 2 is behind OCR its own research flagged as unusable (#25 §5.2, §6).
_METRIC_FINE_DRILLS: dict[tuple[float, float], float] = {
    (10, 1.25): 8.80,
    (12, 1.25): 10.80,
}


def _metric_rows() -> list[Thread]:
    rows: list[Thread] = []
    for diameter, coarse, fines in _METRIC_SIZES:
        drill = _METRIC_COARSE_DRILLS.get(diameter)
        rows.append(
            Thread(
                series=METRIC,
                designation=f"M{_trim(diameter)} × {_trim(coarse)}",
                major_mm=float(diameter),
                pitch_mm=float(coarse),
                flank_angle=SIXTY,
                tap_drill_mm=drill,
                provenance=f"{ISO_262}; {ISO_2306 if drill else NO_DRILL}",
                metric=True,
            )
        )
        for fine in fines:
            fine_drill = _METRIC_FINE_DRILLS.get((diameter, fine))
            rows.append(
                Thread(
                    series=METRIC_FINE,
                    designation=f"M{_trim(diameter)} × {_trim(fine)}",
                    major_mm=float(diameter),
                    pitch_mm=float(fine),
                    flank_angle=SIXTY,
                    tap_drill_mm=fine_drill,
                    provenance=f"{ISO_262}; {ISO_2306 if fine_drill else NO_DRILL}",
                    metric=True,
                )
            )
    return rows


# --- Unified (NBS H28-1969 Table 2.7; drills from ISO 2306 Tables 3-4) -------

# (designation stem, basic major diameter in inches, UNC tpi, UNF tpi)
_UNIFIED_SIZES: tuple[tuple[str, float, int | None, int | None], ...] = (
    ("No. 0", 0.060, None, 80),
    ("No. 1", 0.073, 64, 72),
    ("No. 2", 0.086, 56, 64),
    ("No. 3", 0.099, 48, 56),
    ("No. 4", 0.112, 40, 48),
    ("No. 5", 0.125, 40, 44),
    ("No. 6", 0.138, 32, 40),
    ("No. 8", 0.164, 32, 36),
    ("No. 10", 0.190, 24, 32),
    ("No. 12", 0.216, 24, 28),
    ("1/4", 0.250, 20, 28),
    ("5/16", 0.3125, 18, 24),
    ("3/8", 0.375, 16, 24),
    ("7/16", 0.4375, 14, 20),
    ("1/2", 0.500, 13, 20),
    ("9/16", 0.5625, 12, 18),
    ("5/8", 0.625, 11, 18),
    ("3/4", 0.750, 10, 16),
    ("7/8", 0.875, 9, 14),
    ("1", 1.000, 8, 12),
    ("1 1/8", 1.125, 7, 12),
    ("1 1/4", 1.250, 7, 12),
    ("1 3/8", 1.375, 6, 12),
    ("1 1/2", 1.500, 6, 12),
)

# The five ISO 2306 rows #25 read off the page rather than the OCR. They are
# metric drills for inch threads, which is the standard's own convention.
_UNIFIED_DRILLS: dict[str, float] = {
    "No. 10-24": 3.90,
    "1/4-20": 5.10,
    "5/16-18": 6.60,
    "3/8-16": 8.00,
    "1/2-13": 10.80,
}


def _unified_rows() -> list[Thread]:
    rows: list[Thread] = []
    for stem, inches, coarse_tpi, fine_tpi in _UNIFIED_SIZES:
        for series, tpi in ((UNC, coarse_tpi), (UNF, fine_tpi)):
            if tpi is None:
                continue
            designation = f"{stem}-{tpi}"
            drill = _UNIFIED_DRILLS.get(designation)
            rows.append(
                Thread(
                    series=series,
                    designation=f"{designation} {series}",
                    major_mm=inches * MM_PER_INCH,
                    pitch_mm=MM_PER_INCH / tpi,
                    flank_angle=SIXTY,
                    tap_drill_mm=drill,
                    provenance=f"{NBS_H28}; {ISO_2306 if drill else NO_DRILL}",
                )
            )
    return rows


# --- Whitworth (Gage Crib charts citing BS 84 — secondary) -------------------

# (size, major diameter in mm, tpi, tap drill in mm)
_BSW_SIZES: tuple[tuple[str, float, int, float | None], ...] = (
    ('1/16"', 1.587, 60, 1.15),
    ('3/32"', 2.381, 48, 1.90),
    ('1/8"', 3.175, 40, 2.50),
    ('5/32"', 3.969, 32, 3.20),
    ('3/16"', 4.762, 24, 3.70),
    ('7/32"', 5.556, 24, 4.50),
    ('1/4"', 6.350, 20, 5.10),
    ('5/16"', 7.938, 18, 6.50),
    ('3/8"', 9.525, 16, 7.90),
    ('7/16"', 11.113, 14, 9.20),
    ('1/2"', 12.700, 12, 10.40),
    ('5/8"', 15.876, 11, 13.40),
    ('3/4"', 19.051, 10, 16.25),
    ('7/8"', 22.226, 9, 19.25),
    ('1"', 25.400, 8, 22.00),
    ('1 1/8"', 28.576, 7, 24.50),
    ('1 1/4"', 31.751, 7, 27.25),
    ('1 3/8"', 34.926, 6, 30.25),
    ('1 1/2"', 38.100, 6, 33.50),
)

_BSF_SIZES: tuple[tuple[str, float, int, float | None], ...] = (
    ('3/16"', 4.763, 32, 4.00),
    ('7/32"', 5.556, 28, 4.60),
    ('1/4"', 6.350, 26, 5.30),
    ('9/32"', 7.142, 26, 6.10),
    ('5/16"', 7.938, 22, 6.80),
    ('3/8"', 9.525, 20, 8.30),
    ('7/16"', 11.113, 18, 9.70),
    ('1/2"', 12.700, 16, 11.10),
    ('9/16"', 14.288, 16, 12.70),
    ('5/8"', 15.875, 14, 14.00),
    ('11/16"', 17.463, 14, 15.50),
    ('3/4"', 19.050, 12, 16.75),
    ('13/16"', 20.638, 12, 18.25),
    ('7/8"', 22.225, 11, 19.75),
    ('1"', 25.400, 10, 22.75),
)


def _whitworth_rows(
    series: str, sizes: tuple[tuple[str, float, int, float | None], ...]
) -> list[Thread]:
    return [
        Thread(
            series=series,
            designation=f"{size} {series}",
            major_mm=major,
            pitch_mm=MM_PER_INCH / tpi,
            flank_angle=WHITWORTH,
            tap_drill_mm=drill,
            provenance=f"{GAGE_BS84}{'' if drill is not None else f'; {NO_DRILL}'}",
        )
        for size, major, tpi, drill in sizes
    ]


# --- BA (Gage Crib chart citing BS 93 — secondary; no drills published) ------

# (number, pitch in mm, major diameter in mm). BA pitch is natively metric, so
# nothing here is a reciprocal conversion.
_BA_SIZES: tuple[tuple[int, float, float], ...] = (
    (0, 1.00, 6.000),
    (1, 0.90, 5.300),
    (2, 0.81, 4.700),
    (3, 0.73, 4.100),
    (4, 0.66, 3.600),
    (5, 0.59, 3.200),
    (6, 0.53, 2.800),
    (7, 0.48, 2.500),
    (8, 0.43, 2.200),
    (9, 0.39, 1.900),
    (10, 0.35, 1.700),
    (11, 0.31, 1.500),
    (12, 0.28, 1.300),
    (13, 0.25, 1.200),
    (14, 0.23, 1.000),
    (15, 0.21, 0.900),
    (16, 0.19, 0.790),
)


def _ba_rows() -> list[Thread]:
    return [
        Thread(
            series=BA,
            designation=f"{number} BA",
            major_mm=major,
            pitch_mm=pitch,
            flank_angle=BA_ANGLE,
            tap_drill_mm=None,
            provenance=f"{GAGE_BS93}; {NO_DRILL}",
        )
        for number, pitch, major in _BA_SIZES
    ]


# --- BSPP (ISO 228-1:2000 Table 1) ------------------------------------------

# A pipe thread, and it ships for one reason: the user cannot know a priori what
# they are holding, and G 1/2 measures 20.955 mm — nothing in "1/2" predicts
# that. Excluded, the finder would answer confidently and wrongly (#25 §1.2).
# The size is a nominal *bore*, never a diameter, so the designation is never
# rendered as an inch measurement.
_BSPP_SIZES: tuple[tuple[str, int, float], ...] = (
    ("G 1/16", 28, 7.723),
    ("G 1/8", 28, 9.728),
    ("G 1/4", 19, 13.157),
    ("G 3/8", 19, 16.662),
    ("G 1/2", 14, 20.955),
    ("G 5/8", 14, 22.911),
    ("G 3/4", 14, 26.441),
    ("G 7/8", 14, 30.201),
    ("G 1", 11, 33.249),
    ("G 1 1/8", 11, 37.897),
    ("G 1 1/4", 11, 41.910),
    ("G 1 1/2", 11, 47.803),
    ("G 1 3/4", 11, 53.746),
    ("G 2", 11, 59.614),
)


def _bspp_rows() -> list[Thread]:
    return [
        Thread(
            series=BSPP,
            designation=designation,
            major_mm=major,
            pitch_mm=MM_PER_INCH / tpi,
            flank_angle=WHITWORTH,
            # ISO 2306 does tabulate these, but tapping a G thread is not a
            # normal workshop operation and offering the number invites it.
            tap_drill_mm=None,
            provenance=f"{ISO_228}; {PIPE_THREAD}",
        )
        for designation, tpi, major in _BSPP_SIZES
    ]


def _trim(value: float) -> str:
    """Write a nominal size the way the standard does: M8, not M8.0."""
    return f"{value:g}"


THREADS: tuple[Thread, ...] = tuple(
    _metric_rows()
    + _unified_rows()
    + _whitworth_rows(BSW, _BSW_SIZES)
    + _whitworth_rows(BSF, _BSF_SIZES)
    + _ba_rows()
    + _bspp_rows()
)
