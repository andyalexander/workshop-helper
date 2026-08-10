#!/usr/bin/env bash
# PROTOTYPE — throwaway. Launch the Host with the Browse restyle variants on.
#
#     ./scripts/prototype.sh
#
# Then open http://127.0.0.1:8765/?variant=A and use the floating bar at the
# bottom (or ← / →) to flip between A, B and C.
#
# Delete this script with the rest of the prototype.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

uv sync --quiet
WORKSHOP_HELPER_PROTOTYPE=1 exec uv run workshop-helper "$@"
