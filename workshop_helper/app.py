"""The Flask application and its routes (spec §2.8).

Three surfaces are specified — Browse, Applet page, Compute — but the walking
skeleton serves only Browse, and only its empty state. The app is built from an
already-resolved :class:`~workshop_helper.discovery.Index` so routing stays a
pure function of discovery.
"""

from flask import Flask, render_template

from workshop_helper.discovery import Index


def create_app(index: Index) -> Flask:
    """Build the Host's Flask application over a resolved ``index``."""
    app = Flask(__name__)
    app.config["INDEX"] = index

    @app.route("/")
    def browse() -> str:
        return render_template("browse.html")

    return app
