#!/usr/bin/env bash
# Launch Workshop Helper.
#
# Syncs dependencies, then starts the Host in the foreground. Any arguments are
# passed straight through to the `workshop-helper` command, so `--port` works:
#
#     ./scripts/run.sh
#     ./scripts/run.sh --port 9000
#
# The Host is a foreground process, never a daemon: it holds this terminal until
# you stop it with Ctrl-C.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v uv >/dev/null 2>&1; then
    echo "error: uv is not installed, and it is the only supported way to run this project." >&2
    echo "Install it from https://docs.astral.sh/uv/ and try again." >&2
    exit 1
fi

# Keep the environment in step with uv.lock. Cheap and idempotent once warm.
uv sync --quiet

exec uv run workshop-helper "$@"
