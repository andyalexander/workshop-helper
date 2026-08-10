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
from werkzeug.wrappers import Request, Response

from workshop_helper import prototype  # PROTOTYPE — throwaway; delete with it.
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

# Methods that change nothing, so nothing needs proving about where they came
# from. Everything else must show it came from the Host's own pages.
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
SAME_ORIGIN = "same-origin"
# A request the user began themselves — a typed URL, a bookmark, a drag onto the
# window. No other site is involved, so it is not the case this gate is for.
NO_ORIGIN = "none"


def asset_base(applet: Applet) -> str:
    """Where ``applet``'s own folder is mounted, for scoping relative URLs.

    The trailing slash matters: without it ``urljoin`` drops the last segment.
    """
    return f"/a/{applet.id}/{ASSETS_PREFIX}/"


def create_app(index: Index, overlay: Overlay) -> Flask:
    """Build the Host's Flask application over a resolved ``index``."""
    app = Flask(__name__)
    app.config["INDEX"] = index

    @app.before_request
    def same_origin_only() -> None:
        """Refuse any write that cannot show it came from the Host's own pages.

        **Binding to 127.0.0.1 is not a mitigation for this class.** The request
        is made by the user's own browser, which is inside that boundary; a plain
        form post triggers no preflight, and the Host holds no session it could
        withhold. So any page the user happens to have open could otherwise
        rewrite calibration — figures measured off their own kit, which come
        back out as marks on a pipe.

        A gate over every unsafe method rather than a decorator per route: a
        write route added later is then covered by construction, instead of by
        whoever adds it remembering. That is the failure this ticket came from.
        """
        if request.method not in SAFE_METHODS and not _same_origin(request):
            # Deliberately bare: §10's error surface names an author to blame,
            # and no Applet misbehaved here.
            abort(403)

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
        # PROTOTYPE hook (workshop_helper/prototype.py). Off unless
        # WORKSHOP_HELPER_PROTOTYPE=1; delete with the prototype.
        variant = prototype.chosen(request.args)
        promoted = promote(query.text, vocabulary(index.applets))
        if promoted is not None:
            # ↵ over a matching prefix places a chip; it does not search. The
            # redirect is what clears the box and settles the filter into the
            # URL, so `imp↵cop↵` lands two chips with no JavaScript at all.
            return _redirect(query.with_tag(promoted).without_text(), variant)
        # Faults render alongside the cards, never instead of them: a greyed card
        # is a card (§10.1). `require_applet` cannot reach one, so every route
        # below is un-openable for a faulty id by construction.
        left = results(index, query)
        if variant is not None:
            extra = prototype.render_args(variant)
            return _page(
                extra.pop("template"),  # type: ignore[arg-type]
                applets=left.applets,
                faults=left.faults,
                **extra,
            )
        return _page("browse.html", applets=left.applets, faults=left.faults)

    def _redirect(query: Query, variant: str | None = None) -> Response:
        url = query.href(url_for("browse"))
        if variant is not None:  # PROTOTYPE: keep ↵ inside the variant.
            url = prototype.stick(url, variant)
        return redirect(url)

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
            return _page("calculator.html", **_calculator(applet, None, None))
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
            # the boxes is the whole point of the reset. The **mode** survives it
            # regardless: a reset is about the values, and the mode is not one of
            # them. Dropping it would change what exists on screen (§4.5) under
            # someone who asked only for the author's numbers back.
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
        if view is None:
            # Nothing to write to: either this Applet declares no calibration at
            # all, or the submitted key resolves to no slice. Neither is
            # reachable from the Host's own pages — the disclosure is rendered
            # from this same view, and `keyed_by` is checked at scan to be a
            # `choice` whose choices are exactly the calibration keys, rendered
            # as a select with no blank option. So the request did not come from
            # the disclosure, and answering 200 would report a save that did not
            # happen.
            abort(400)

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

        Every caller is a POST, so the mode is read from the form here — in one
        place rather than four. It is read **separately from** ``submitted``
        because a reset passes no values and must still come back in the mode it
        was pressed in.
        """
        context = _calculator(authored, submitted, request.form.get(MODE))
        if request.headers.get(HTMX_HEADER) is None:
            return _page("calculator.html", **context)
        return render_template("_compute.html", **context)

    def _calculator(
        authored: Applet, submitted: Mapping[str, str] | None, mode_name: str | None
    ) -> dict[str, object]:
        """Everything the calculator page shows, as *this user* sees it (§8).

        ``submitted is None`` is the Applet being opened, where a Result appears
        only if every Input has a default — the user's saved ones included, which
        is what makes compute-on-open user-dependent (§4.6).

        ``mode_name`` is a **separate argument rather than read out of**
        ``submitted``, because the two are independent: a reset throws the values
        away and keeps the mode. A mode decides *what exists* (§4.5), so it
        outlives an operation that is only about what those things hold.
        """
        applet = overlaid(authored, overlay)
        # The selector is the Host's own field, derived from `[modes.*]`; there
        # is no `mode` Input for it to collide with (§4.5).
        mode = applet.mode(mode_name)
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


def _same_origin(incoming: Request) -> bool:
    """Whether ``incoming`` can show it came from the page the Host served.

    ``Sec-Fetch-Site`` is the browser's own account of where the request began
    and cannot be set from script, so it is preferred; ``Origin`` is the older
    signal and is compared against the host that answered.

    **Neither header present means refuse.** Absence is not evidence of
    same-origin, and every browser that could be turned against the Host has
    sent ``Sec-Fetch-Site`` since around 2020 — so trusting silence would leave
    the gate open to exactly the ancient client most likely to be used against
    it. A curl against a write route has to say so explicitly, which is a fair
    price for a tool whose stored numbers are measured off physical kit.
    """
    site = incoming.headers.get("Sec-Fetch-Site")
    if site is not None:
        return site in (SAME_ORIGIN, NO_ORIGIN)
    origin = incoming.headers.get("Origin")
    if origin is not None:
        return origin == f"{incoming.scheme}://{incoming.host}"
    return False


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
