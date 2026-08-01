"""The drawings, built with f-strings and ``<path>`` (spec §6.1).

``workshop_utils`` owes authors **nothing** here, and this module is what that
costs: about a hundred lines of arithmetic and string building, in the Applet,
where a drawing model extracted from a sample of one would have been shaped like
this Applet forever.

**These are not illustrations.** §1.5 is a framework claim earned by this exact
Applet: the setback has been wrong three times, every time about *which point in
which direction*, and every time invisible in the number — 70.0mm looks identical
measured to a corner, an outside edge or a projected centreline. So each drawing
carries the two things no Output can:

1. the **point and direction** the tape runs from, marked on the geometry;
2. the **sequence** — for an offset, that both marks go on straight pipe before
   either bend is pulled, which is the assumption the trade formula makes and the
   one a Measure-Bend user needs to see they are not making.

Everything is drawn in millimetres and the viewBox is fitted to the geometry, so
a 22mm former at 60° and a 15mm at 30° both fill the frame. Strokes are
``currentColor``: the Host ships no graphics dependency and the drawing should
not ship a palette.
"""

from math import cos, radians, sin

# Room for the labels and dimension lines that sit outside the pipe itself.
MARGIN_MM = 34.0
# How far a dimension line stands off the geometry it measures.
STANDOFF_MM = 22.0
# The lead-in and run-out of straight pipe either side of a bend: enough to read
# as pipe rather than as a stub, on the smallest former.
LEAD_MM = 45.0

Point = tuple[float, float]


def single_bend_svg(
    outside_diameter: float, r_centreline: float, angle: float, setback: float
) -> str:
    """One bend: where the bend starts, and where the setback is measured to.

    The dashed legs run out to the **vertex of the two centrelines** and stop
    there, because that is the point the figure is measured back to — the
    mid-line, not the corner (#17).
    """
    theta = radians(angle)
    out = (cos(theta), -sin(theta))
    vertex = (0.0, 0.0)
    bend_start = (-setback, 0.0)
    bend_end = (setback * out[0], setback * out[1])
    tail = (bend_start[0] - LEAD_MM, 0.0)
    head = _along(bend_end, out, LEAD_MM)

    pipe = (
        f"M {_xy(tail)} L {_xy(bend_start)} "
        # Turning up-screen from a rightward run is counter-clockwise: sweep 0.
        f"A {r_centreline:.2f} {r_centreline:.2f} 0 0 0 {_xy(bend_end)} "
        f"L {_xy(head)}"
    )
    extent = [tail, head, bend_start, bend_end, vertex]
    font = _font(extent)
    vertex_label = "vertex of the two centrelines"
    extent.append(_ends(vertex, vertex_label, font))
    body = [
        *_pipe(pipe, outside_diameter, font),
        # The two tangent legs, to the vertex they cross at.
        _path(
            f"M {_xy(bend_start)} L {_xy(vertex)} L {_xy(bend_end)}",
            font * 0.09,
            f'stroke-dasharray="{font * 0.4:.1f} {font * 0.3:.1f}"',
        ),
        _dot(vertex, font * 0.22),
        _dot(bend_start, font * 0.22),
        *_dimension(bend_start, vertex, STANDOFF_MM, f"setback {setback:.1f}mm", font),
        # Both labels sit clear of the outgoing leg, which sweeps through
        # everything above the vertex as the angle opens up.
        _text((vertex[0] + font * 0.6, vertex[1] + font * 1.3), vertex_label, font),
        _text(
            (bend_start[0] - font * 0.4, bend_start[1] - font),
            "bend starts here",
            font,
            anchor="end",
        ),
    ]
    caption = (
        f"{angle:g}° on a {r_centreline:g}mm centreline former — measure back "
        "from the vertex to the start of the bend"
    )
    return _svg(body, extent, caption, font)


def offset_svg(
    outside_diameter: float,
    r_centreline: float,
    angle: float,
    offset: float,
    diagonal: float,
    mark_distance: float,
) -> str:
    """A step, in two panels: the shape you want, and the pipe you mark.

    The lower panel is the load-bearing one. Both marks go on **straight pipe**,
    before either bend, and they are the points where each bend *starts* — mark
    both, bend ①, move along, bend ②. Anyone who bends and then measures for the
    second mark is working to a different figure by one gain, and this is where
    they can see it.
    """
    theta = radians(angle)
    rise = r_centreline * (1 - cos(theta))
    run = r_centreline * sin(theta)
    first = (0.0, 0.0)
    turned = (run, rise)
    straightened = (
        turned[0] + diagonal * cos(theta),
        turned[1] + diagonal * sin(theta),
    )
    second = (straightened[0] + run, straightened[1] + rise)
    tail = (-LEAD_MM, 0.0)
    head = (second[0] + LEAD_MM, second[1])

    shape = (
        f"M {_xy(tail)} L {_xy(first)} "
        f"A {r_centreline:.2f} {r_centreline:.2f} 0 0 1 {_xy(turned)} "
        f"L {_xy(straightened)} "
        f"A {r_centreline:.2f} {r_centreline:.2f} 0 0 0 {_xy(second)} "
        f"L {_xy(head)}"
    )

    # The straight pipe, laid out below the finished shape, at the same scale.
    base = second[1] + STANDOFF_MM * 3
    mark_one = (0.0, base)
    mark_two = (mark_distance, base)
    pipe_ends = ((-LEAD_MM, base), (mark_distance + LEAD_MM, base))
    extent = [tail, head, (mark_distance + LEAD_MM, base + STANDOFF_MM * 2)]
    font = _font(extent)
    step_label = f"step {offset:g}mm"
    # The step dimension stands to the right of the shape, and its label stands
    # to the right of that; the frame has to hold both.
    extent.append(_ends((head[0] + STANDOFF_MM, offset), step_label, font))

    body = [
        *_pipe(shape, outside_diameter, font),
        *_pipe(f"M {_xy(pipe_ends[0])} L {_xy(pipe_ends[1])}", outside_diameter, font),
        *_dimension(
            (head[0] + STANDOFF_MM, 0.0),
            (head[0] + STANDOFF_MM, offset),
            0.0,
            step_label,
            font,
        ),
        *_dimension(
            mark_one, mark_two, STANDOFF_MM, f"marks {mark_distance:.1f}mm apart", font
        ),
        _numbered(first, "1", font),
        _numbered(straightened, "2", font),
        _numbered(mark_one, "1", font),
        _numbered(mark_two, "2", font),
    ]
    caption = (
        "Mark both points on straight pipe first, then bend ① and ② — "
        "each mark is where that bend starts"
    )
    return _svg(body, extent, caption, font)


def _pipe(path: str, outside_diameter: float, font: float) -> list[str]:
    """The pipe itself: a soft body at its real diameter over its centreline.

    Drawing the body at the true outside diameter is what keeps the picture
    honest about scale — a 22mm tube on a 110mm former looks like what it is.
    """
    return [
        _path(path, outside_diameter, 'stroke-linecap="round" stroke-opacity="0.25"'),
        _path(path, font * 0.12),
    ]


def _path(d: str, width: float, extra: str = "") -> str:
    """One stroked path. Nothing in these drawings is ever filled."""
    return (
        f'<path d="{d}" fill="none" stroke="currentColor" '
        f'stroke-width="{width:.2f}" {extra} />'
    )


def _dimension(
    start: Point, end: Point, standoff: float, label: str, font: float
) -> list[str]:
    """An arrowed line measuring ``start`` to ``end``, offset clear of the pipe."""
    from_ = (start[0], start[1] + standoff)
    to = (end[0], end[1] + standoff)
    middle = ((from_[0] + to[0]) / 2, (from_[1] + to[1]) / 2)
    width = font * 0.09
    ticks = "".join(
        _path(
            f"M {_xy(point)} L {_xy((point[0], point[1] - standoff))}",
            width,
            'stroke-dasharray="2 2"',
        )
        for point in (from_, to)
        if standoff
    )
    # A vertical dimension takes its label beside the line; a horizontal one
    # takes it underneath, where neither can sit on top of the pipe.
    upright = from_[0] == to[0]
    at = (
        (middle[0] + font * 0.5, middle[1])
        if upright
        else (middle[0], middle[1] + font)
    )
    return [
        ticks,
        _path(
            f"M {_xy(from_)} L {_xy(to)}",
            width,
            'marker-start="url(#arrow)" marker-end="url(#arrow)"',
        ),
        _text(at, label, font, anchor="start" if upright else "middle"),
    ]


def _numbered(at: Point, number: str, font: float) -> str:
    """A circled step number, which is how the sequence is carried (§1.5)."""
    return (
        f'<circle cx="{at[0]:.2f}" cy="{at[1]:.2f}" r="{font * 0.7:.2f}" '
        'fill="none" stroke="currentColor" stroke-width="1" />'
        + _text((at[0], at[1] + font * 0.35), number, font, anchor="middle")
    )


def _dot(at: Point, radius: float) -> str:
    """A filled point, for somewhere the eye has to land exactly."""
    return f'<circle cx="{at[0]:.2f}" cy="{at[1]:.2f}" r="{radius:.2f}" />'


def _text(at: Point, label: str, font: float, anchor: str = "start") -> str:
    """One label. Every string reaching here is the Applet's own."""
    return (
        f'<text x="{at[0]:.2f}" y="{at[1]:.2f}" font-size="{font:.2f}" '
        f'text-anchor="{anchor}">{label}</text>'
    )


def _svg(body: list[str], extent: list[Point], caption: str, font: float) -> str:
    """Fit the viewBox to the geometry and wrap it up.

    Fitting rather than fixing is what lets a 110mm former at 60° and a 70mm at
    30° both fill the frame — the drawing is per-compute, so it can be.
    """
    left = min(x for x, _ in extent) - MARGIN_MM
    right = max(x for x, _ in extent) + MARGIN_MM
    top = min(y for _, y in extent) - MARGIN_MM
    bottom = max(y for _, y in extent) + MARGIN_MM
    # The caption is a whole sentence and the frame is as wide as the geometry
    # happens to be, so it is sized to fit rather than left to run off the edge.
    caption_font = min(font * 0.9, (right - left) / (0.55 * len(caption)))
    bottom += caption_font * 2.4
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'viewBox="{left:.1f} {top:.1f} {right - left:.1f} {bottom - top:.1f}" '
        f'fill="currentColor" stroke="none">'
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" /></marker></defs>'
        + "".join(body)
        + _text((left + MARGIN_MM / 2, bottom - caption_font), caption, caption_font)
        + "</svg>"
    )


def _ends(at: Point, label: str, font: float) -> Point:
    """Roughly where a label starting at ``at`` runs out to.

    Text has no measurable width without a font engine, and the Host ships no
    graphics dependency (§6.1) — so this is an estimate, and the frame carries a
    margin on top of it.
    """
    return (at[0] + len(label) * font * 0.55, at[1])


def _font(extent: list[Point]) -> float:
    """A text size in millimetres that stays legible whatever the frame holds."""
    span = max(x for x, _ in extent) - min(x for x, _ in extent) + 2 * MARGIN_MM
    return max(6.0, span / 32)


def _along(point: Point, direction: Point, distance: float) -> Point:
    """``distance`` further along ``direction`` from ``point``."""
    return (point[0] + direction[0] * distance, point[1] + direction[1] * distance)


def _xy(point: Point) -> str:
    """One point, as SVG path coordinates."""
    return f"{point[0]:.2f} {point[1]:.2f}"
