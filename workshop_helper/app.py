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

from flask import Flask, abort, render_template, request, send_from_directory
from werkzeug.wrappers import Response

from workshop_helper.discovery import Applet, Index
from workshop_helper.errors import error_surface
from workshop_helper.form import Form, build_form, computes_on_open, refuse
from workshop_helper.loader import AppletFault, run_compute
from workshop_helper.manifest import DOCUMENTATION, MODE, Mode
from workshop_helper.render import Computation, figure
from workshop_utils import InvalidInput, render_markdown

ASSETS_PREFIX = "assets"
COMPUTE_PREFIX = "compute"
HTMX_HEADER = "HX-Request"
MODE_FIELD = "mode_field"


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
        # The selector is the Host's own field, derived from `[modes.*]`; there
        # is no `mode` Input for it to collide with (§4.5).
        mode = applet.mode(request.form.get(MODE))
        form = build_form(mode.inputs, request.form)
        form, computation = _run_applet(applet, mode, form)
        if request.headers.get(HTMX_HEADER) is None:
            return _render_calculator(applet, mode, form, computation)
        return render_template(
            "_compute.html",
            applet=applet,
            mode=mode,
            form=form,
            computation=computation,
        )

    def _calculator_page(applet: Applet) -> str:
        """Open a calculator: the form, and a Result iff it can have one (§4.6)."""
        mode = applet.mode()
        form = build_form(mode.inputs, submitted=None)
        computation = Computation()
        if computes_on_open(mode.inputs):
            form, computation = _run_applet(applet, mode, form)
        return _render_calculator(applet, mode, form, computation)

    def _render_calculator(
        applet: Applet, mode: Mode, form: Form, computation: Computation
    ) -> str:
        """The whole page: the form, and whatever the Result region has to show."""
        return render_template(
            "calculator.html",
            applet=applet,
            mode=mode,
            form=form,
            computation=computation,
        )

    @app.route(f"/a/<applet_id>/{ASSETS_PREFIX}/<path:filename>")
    def applet_asset(applet_id: str, filename: str) -> Response:
        applet = require_applet(applet_id)
        if applet.type != DOCUMENTATION:
            abort(404)
        # send_from_directory refuses to escape the Applet folder.
        return send_from_directory(applet.path, filename)

    app.add_template_filter(figure)
    # The selector's field name is the Host's, and it is one name: the template
    # posts under it and the route above reads it back. (`mode` itself is the
    # active Mode in every template, so the field name gets its own.)
    app.jinja_env.globals[MODE_FIELD] = MODE
    return app


def _run_applet(applet: Applet, mode: Mode, form: Form) -> tuple[Form, Computation]:
    """Run the Applet, or carry back what it refused or how it broke (§10.2).

    Static validation is the gate: no ``values`` means nothing is imported and
    nothing is run, so ``compute()`` cannot be reached with a value it would have
    to check for itself (§4.3).

    The form comes back as well as the Result because a healthy refusal lands on
    a *field*, not in the Result region — an ``InvalidInput`` renders exactly
    where a `min`/`max` failure would.
    """
    if form.values is None:
        return form, Computation()
    calibration = (
        None if applet.calibration is None else applet.calibration.resolve(form.values)
    )
    try:
        result = run_compute(applet, mode, form.values, calibration)
    except InvalidInput as refusal:
        return refuse(form, refusal), Computation()
    except AppletFault as fault:
        return form, Computation(
            surface=error_surface(
                name=applet.name,
                root_name=applet.root.name,
                details=f"{fault.summary}\n\n{fault.details}",
                author=applet.author,
            )
        )
    return form, Computation(result=result)
