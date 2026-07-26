"""The Host's command-line entry point (spec §2.3).

One foreground command launches the Host. It resolves the home directory, reads
``config.toml`` if present, and builds the index, then hands off to
:func:`~workshop_helper.lifecycle.serve`, which emits the startup summary and
binds — or defers to an already-running copy on a busy port.
"""

import argparse

from workshop_helper.discovery import build_index
from workshop_helper.home import load_config_roots, resolve_home
from workshop_helper.lifecycle import DEFAULT_PORT, serve


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the CLI. Port is the only knob, and it lives here — never in config."""
    parser = argparse.ArgumentParser(
        prog="workshop-helper",
        description="Browse and run small, pluggable workshop reference tools.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind on 127.0.0.1 (default: {DEFAULT_PORT}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the startup sequence and serve the Host."""
    args = parse_args(argv)

    home = resolve_home()
    roots = load_config_roots(home)
    index = build_index(roots)

    return serve(index, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
