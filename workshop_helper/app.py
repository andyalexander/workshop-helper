"""The Flask application and its routes (spec §2.8).

Three surfaces are specified — Browse, Applet page, Compute — and all three ship
here. The app is built from an already-resolved
:class:`~workshop_helper.discovery.Index` so routing stays a pure function of
discovery.

**Un-openable is a property of the index, not of a check here.** A faulty Applet
lives in ``index.faults``, which no lookup consults, so a greyed card has no page
to reach even by hand-typed URL (§10.1).

The ``documentation`` pipeline is the whole of ADR-0005's contract for that type:
read ``content.md``, render it through ``workshop_utils.render_markdown``, serve
the folder's assets. **No Applet Python is imported. Ever.**

Assets are served under ``/a/<id>/assets/<file>``. Authors write ordinary relative
links — ``![](thread-form.svg)`` — and ``render_markdown`` scopes them onto that
mount, so an Applet folder stays readable on its own and never hard-codes a Host
URL. That rewrite is why markdown-it-py was chosen (``library-stack.md`` §3).

The ``calculator`` pipeline is form → validate → import → ``compute()`` → render,
and the **validate step is a gate, not a stage**: without
:attr:`~workshop_helper.form.Form.values` there is nothing to import anything
for. The round-trip is htmx over a form that posts on its own, so the same route
answers both — a fragment when htmx asked, the whole page when a browser did.
"""

import math
from dataclasses import dataclass

from flask import Flask, abort, render_template, request, send_from_directory
from werkzeug.wrappers import Response

from workshop_helper.discovery import Applet, Index
from workshop_helper.errors import ErrorSurface, error_surface
from workshop_helper.form import Form, build_form, computes_on_open
from workshop_helper.loader import AppletFault, run
from workshop_helper.manifest import DOCUMENTATION, Output
from workshop_utils import Cell, Result, render_markdown

ASSETS_PREFIX = "assets"
COMPUTE_PREFIX = "compute"
HTMX_HEADER = "HX-Request"
NOTHING = "—"


@dataclass(frozen=True)
class Computation:
    """What the Result region shows: a Result, a fault, or neither yet.

    Neither is not a failure state — it is a partly-filled form on an Applet that
    does not compute on open (§4.6), and the region says so rather than showing
    an empty answer.
    """

    result: Result | None = None
    surface: ErrorSurface | None = None

    def shown(self, outputs: tuple[Output, ...]) -> list[tuple[Output, Cell]]:
        """Declared Outputs paired with their values, in display order (§4.5)."""
        if self.result is None:
            return []
        return [(output, self.result.outputs[output.name]) for output in outputs]


def asset_base(applet: Applet) -> str:
    """Where ``applet``'s own folder is mounted, for scoping relative URLs.

    The trailing slash matters: without it ``urljoin`` drops the last segment.
    """
    return f"/a/{applet.id}/{ASSETS_PREFIX}/"


def create_app(index: Index) -> Flask:
    """Build the Host's Flask application over a resolved ``index``."""
    app = Flask(__name__)
    app.config["INDEX"] = index

    def require_applet(applet_id: str) -> Applet:
        applet = index.applet(applet_id)
        if applet is None:
            abort(404)
        return applet

    @app.route("/")
    def browse() -> str:
        # Faults render alongside the cards, never instead of them: a greyed card
        # is a card (§10.1). `require_applet` cannot reach one, so every route
        # below is un-openable for a faulty id by construction.
        return render_template(
            "browse.html", applets=index.applets, faults=index.faults
        )

    @app.route("/a/<applet_id>")
    def applet_page(applet_id: str) -> str:
        applet = require_applet(applet_id)
        if applet.type != DOCUMENTATION:
            return _calculator_page(applet)
        return render_template(
            "documentation.html",
            applet=applet,
            content=render_markdown(applet.body or "", asset_base=asset_base(applet)),
        )

    @app.route(f"/a/<applet_id>/{COMPUTE_PREFIX}", methods=["POST"])
    def compute(applet_id: str) -> str:
        """The round-trip: recompute from what was submitted (§2.8).

        htmx swaps the Result fragment and takes the re-rendered form with it,
        out of band, because a `min`/`max` failure belongs inline against its own
        field (§10.2) and the field is not inside the fragment. Without htmx this
        is an ordinary form POST and the answer is the whole page — the form
        works with no JavaScript at all, and htmx only upgrades it.
        """
        applet = require_applet(applet_id)
        if applet.type == DOCUMENTATION:
            abort(404)
        form = build_form(applet.inputs, request.form)
        computation = _compute(applet, form)
        if request.headers.get(HTMX_HEADER) is None:
            return _render_calculator(applet, form, computation)
        return render_template(
            "_compute.html", applet=applet, form=form, computation=computation
        )

    def _calculator_page(applet: Applet) -> str:
        """Open a calculator: the form, and a Result iff it can have one (§4.6)."""
        form = build_form(applet.inputs, submitted=None)
        computation = Computation()
        if computes_on_open(applet.inputs):
            computation = _compute(applet, form)
        return _render_calculator(applet, form, computation)

    def _render_calculator(applet: Applet, form: Form, computation: Computation) -> str:
        return render_template(
            "calculator.html", applet=applet, form=form, computation=computation
        )

    @app.route(f"/a/<applet_id>/{ASSETS_PREFIX}/<path:filename>")
    def applet_asset(applet_id: str, filename: str) -> Response:
        applet = require_applet(applet_id)
        if applet.type != DOCUMENTATION:
            abort(404)
        # send_from_directory refuses to escape the Applet folder.
        return send_from_directory(applet.path, filename)

    app.add_template_filter(figure)
    return app


def _compute(applet: Applet, form: Form) -> Computation:
    """Run the Applet, or carry the fault it produced onto its own page (§10.2).

    Static validation is the gate: no ``values`` means nothing is imported and
    nothing is run, so ``compute()`` cannot be reached with a value it would have
    to check for itself (§4.3).
    """
    if form.values is None:
        return Computation()
    try:
        return Computation(result=run(applet, form.values, applet.outputs))
    except AppletFault as fault:
        return Computation(
            surface=error_surface(
                name=applet.name,
                root_name=applet.root.name,
                details=f"{fault.summary}\n\n{fault.details}",
                author=applet.author,
            )
        )


def figure(value: Cell) -> str:
    """Format one value for display — the Host's job, never the Applet's (§6).

    A missing cell is an em dash and not a zero: the thread finder's BA rows have
    no published tap drill, and an empty cell is honest where a computed one
    would be a lookup that never happened (#25 §3.4).
    """
    if value is None:
        return NOTHING
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int | float):
        if not math.isfinite(value):
            return NOTHING
        # `g` drops the trailing zeros an exact figure does not have: 8.0 is 8,
        # and 1.250 is 1.25, without rounding 20.955 to something tidier.
        return f"{value:g}"
    return value
