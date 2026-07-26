"""The Flask application and its routes (spec §2.8).

Three surfaces are specified — Browse, Applet page, Compute. Browse and the
``documentation`` half of the Applet page ship here; the calculator form and
``POST /a/<id>/compute`` arrive with #35. The app is built from an
already-resolved :class:`~workshop_helper.discovery.Index` so routing stays a
pure function of discovery.

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
"""

from flask import Flask, abort, render_template, send_from_directory
from werkzeug.wrappers import Response

from workshop_helper.discovery import Applet, Index
from workshop_helper.manifest import DOCUMENTATION
from workshop_utils import render_markdown

ASSETS_PREFIX = "assets"


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
            # Calculators render from the Manifest's Inputs — that is #35.
            abort(501, f"{applet.type} Applets are not renderable yet.")
        return render_template(
            "documentation.html",
            applet=applet,
            content=render_markdown(applet.body or "", asset_base=asset_base(applet)),
        )

    @app.route(f"/a/<applet_id>/{ASSETS_PREFIX}/<path:filename>")
    def applet_asset(applet_id: str, filename: str) -> Response:
        applet = require_applet(applet_id)
        if applet.type != DOCUMENTATION:
            abort(404)
        # send_from_directory refuses to escape the Applet folder.
        return send_from_directory(applet.path, filename)

    return app
