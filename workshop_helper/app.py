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

The Overlay is merged into the indexed Applet in exactly one place,
:func:`_calculator`. Below that line the form, the round-trip and ``compute()``
see one Applet and never learn that part of it came from the user rather than
the author (§8). The three write routes — Compute, save-as-defaults, the
Calibration disclosure — are three ``formaction``s on **one form**, which is why
the values on screen ride along with every one of them and why none of it needs
JavaScript to work.
"""

from collections.abc import Mapping

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.wrappers import Response

from workshop_helper.browse import (
    ROOT_PARAM,
    TAG_PARAM,
    TEXT_PARAM,
    Query,
    promote,
    read_query,
    results,
    sidebar,
    vocabulary,
)
from workshop_helper.discovery import Applet, Index
from workshop_helper.errors import error_surface
from workshop_helper.form import Form, build_form, computes_on_open, refuse
from workshop_helper.loader import AppletFault, run_compute
from workshop_helper.manifest import DOCUMENTATION, MODE, Mode
from workshop_helper.overlay import (
    Overlay,
    calibration_view,
    overlaid,
    submitted_calibration,
)
from workshop_helper.render import Computation, figure
from workshop_utils import InvalidInput, render_markdown

ASSETS_PREFIX = "assets"
FACETS_PREFIX = "facets"
COMPUTE_PREFIX = "compute"
DEFAULTS_PREFIX = "defaults"
CALIBRATION_PREFIX = "calibration"
HTMX_HEADER = "HX-Request"
MODE_FIELD = "mode_field"

# The Host's own field for "put this back the way the author had it" — carried
# by the button that was pressed, which is how one route serves both a save and
# its undo without a second URL.
RESET = "reset"
RESET_FIELD = "reset_field"


def asset_base(applet: Applet) -> str:
    """Where ``applet``'s own folder is mounted, for scoping relative URLs.

    The trailing slash matters: without it ``urljoin`` drops the last segment.
    """
    return f"/a/{applet.id}/{ASSETS_PREFIX}/"


def create_app(index: Index, overlay: Overlay) -> Flask:
    """Build the Host's Flask application over a resolved ``index``."""
    app = Flask(__name__)
    app.config["INDEX"] = index

    def require_applet(applet_id: str) -> Applet:
        applet = index.applet(applet_id)
        if applet is None:
            abort(404)
        return applet

    def require_calculator(applet_id: str) -> Applet:
        """An Applet that has a form to post to; a documentation page has none."""
        applet = require_applet(applet_id)
        if applet.type == DOCUMENTATION:
            abort(404)
        return applet

    def _page(template: str, **context: object) -> str:
        """Render a full page — every one of them carries the sidebar (§9).

        The filter is read back off the URL rather than threaded through, which
        is what makes "the sidebar persists on the Applet page" a property of the
        link that got you there rather than of any state the Host keeps.
        """
        query = read_query(request.args)
        # Text that reaches here matched no tag, so it is both the filter and
        # what is still in the box — the hint says which of the two it is.
        view = sidebar(index, query, typed=query.text)
        return render_template(template, sidebar=view, **context)

    @app.route("/")
    def browse() -> str | Response:
        query = read_query(request.args)
        promoted = promote(query.text, vocabulary(index.applets))
        if promoted is not None:
            # ↵ over a matching prefix places a chip; it does not search. The
            # redirect is what clears the box and settles the filter into the
            # URL, so `imp↵cop↵` lands two chips with no JavaScript at all.
            return _redirect(query.with_tag(promoted).without_text())
        # Faults render alongside the cards, never instead of them: a greyed card
        # is a card (§10.1). `require_applet` cannot reach one, so every route
        # below is un-openable for a faulty id by construction.
        left = results(index, query)
        return _page("browse.html", applets=left.applets, faults=left.faults)

    def _redirect(query: Query) -> Response:
        return redirect(query.href(url_for("browse")))

    @app.route(f"/{FACETS_PREFIX}")
    def facets() -> str:
        """The ↵ preview, live (§9).

        The box holds a half-written token, so it narrows the **candidates** and
        never the results: the counts have to say what the chip would leave, not
        what the half-word matches as text. Without htmx this route is simply
        never called and the same lists render with the page.
        """
        asked = read_query(request.args)
        return render_template(
            "facets.html",
            view=sidebar(index, asked.without_text(), typed=asked.text),
        )

    @app.route("/a/<applet_id>")
    def applet_page(applet_id: str) -> str:
        applet = require_applet(applet_id)
        if applet.type != DOCUMENTATION:
            return _page("calculator.html", **_calculator(applet, None))
        return _page(
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
        return _answer(require_calculator(applet_id), request.form)

    @app.route(f"/a/<applet_id>/{DEFAULTS_PREFIX}", methods=["POST"])
    def save_defaults(applet_id: str) -> str:
        """The save-as-defaults strip under the Inputs (§9), and its undo.

        Saving is not computing, so an invalid field does not block it: every
        field that *does* hold a value is kept, which is how a partially-filled
        Applet becomes one that computes on open for this user (§4.6, §8).
        """
        authored = require_calculator(applet_id)
        if RESET in request.form:
            overlay.clear_defaults(applet_id)
            # Answered as if freshly opened — seeing the author's figures back in
            # the boxes is the whole point of the reset.
            return _answer(authored, submitted=None)

        applet = overlaid(authored, overlay)
        mode = applet.mode(request.form.get(MODE))
        overlay.save_defaults(applet_id, build_form(mode.inputs, request.form).supplied)
        return _answer(authored, request.form)

    @app.route(f"/a/<applet_id>/{CALIBRATION_PREFIX}", methods=["POST"])
    def save_calibration(applet_id: str) -> str:
        """The Calibration disclosure's writes: correct a field, or reset one.

        Both act on the **active key only** (§5.5) — the slice the user is
        looking at is the bender they are standing at.
        """
        authored = require_calculator(applet_id)
        applet = overlaid(authored, overlay)
        mode = applet.mode(request.form.get(MODE))
        form = build_form(mode.inputs, request.form)
        view = calibration_view(authored.calibration, applet.calibration, form)
        if view is not None:
            field = request.form.get(RESET)
            if field is None:
                overlay.save_calibration(
                    applet_id, view.key, submitted_calibration(view, request.form)
                )
            else:
                overlay.reset_calibration(applet_id, view.key, field)
        return _answer(authored, request.form)

    def _answer(authored: Applet, submitted: Mapping[str, str] | None) -> str:
        """Render the calculator: a fragment when htmx asked, else the page.

        Every write route ends here, so a saved default or a corrected
        calibration lands on screen through the same swap a Compute does — and
        the disclosure comes back with the form, out of band, because a reset
        changes a box that is not inside the Result fragment.
        """
        context = _calculator(authored, submitted)
        if request.headers.get(HTMX_HEADER) is None:
            return _page("calculator.html", **context)
        return render_template("_compute.html", **context)

    def _calculator(
        authored: Applet, submitted: Mapping[str, str] | None
    ) -> dict[str, object]:
        """Everything the calculator page shows, as *this user* sees it (§8).

        ``submitted is None`` is the Applet being opened, where a Result appears
        only if every Input has a default — the user's saved ones included, which
        is what makes compute-on-open user-dependent (§4.6).
        """
        applet = overlaid(authored, overlay)
        # The selector is the Host's own field, derived from `[modes.*]`; there
        # is no `mode` Input for it to collide with (§4.5).
        mode = applet.mode(None if submitted is None else submitted.get(MODE))
        form = build_form(mode.inputs, submitted)
        computation = Computation()
        if submitted is not None or computes_on_open(mode.inputs):
            form, computation = _run_applet(applet, mode, form)
        return {
            "applet": applet,
            "mode": mode,
            "form": form,
            "computation": computation,
            "calibration": calibration_view(
                authored.calibration, applet.calibration, form
            ),
        }

    @app.route(f"/a/<applet_id>/{ASSETS_PREFIX}/<path:filename>")
    def applet_asset(applet_id: str, filename: str) -> Response:
        applet = require_applet(applet_id)
        if applet.type != DOCUMENTATION:
            abort(404)
        # send_from_directory refuses to escape the Applet folder.
        return send_from_directory(applet.path, filename)

    app.add_template_filter(figure)
    # `keep` hangs the current filter off a URL. It is a global rather than a
    # passed variable because the form lives in an imported macro, and a POST
    # that loses the query string is a POST that loses the sidebar (§9).
    app.jinja_env.globals["keep"] = _keep
    # The filter's field names are the Host's, and each is one name: the sidebar
    # posts under it and `read_query` reads it back (the same rule the mode
    # selector follows above).
    app.jinja_env.globals["tag_param"] = TAG_PARAM
    app.jinja_env.globals["root_param"] = ROOT_PARAM
    app.jinja_env.globals["text_param"] = TEXT_PARAM
    # The selector's field name is the Host's, and it is one name: the template
    # posts under it and the route above reads it back. (`mode` itself is the
    # active Mode in every template, so the field name gets its own.)
    app.jinja_env.globals[MODE_FIELD] = MODE
    app.jinja_env.globals[RESET_FIELD] = RESET
    return app


def _keep(url: str) -> str:
    """``url`` with the current filter kept on it (§9).

    Self-perpetuating: the action was rendered through here, so the POST arrives
    carrying the query string, and the page it answers with renders through here
    again. That is the whole mechanism by which a no-JavaScript Compute comes
    back with the same chips still in the sidebar.
    """
    return read_query(request.args).href(url)


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
