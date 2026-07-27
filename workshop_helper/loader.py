"""The lazy import of an Applet, and the call into ``compute()`` (spec §7.2).

Import is **lazy — on open, never at scan**, and the module is imported **as a
package named by the Applet id**. Both halves matter:

- Nothing here runs while the index is built, which is what keeps discovery cheap
  and safe (ADR-0004) and what makes a contributed Applet *listable* without
  being *executable*.
- The id names the module, so two Roots' ``helpers.py`` are
  ``…thread-finder.helpers`` and ``…mates-finder.helpers`` — never one entry in
  ``sys.modules`` silently running the other Root's code. An Applet's own
  submodules are reached with a relative import (``from .threads import ROWS``);
  a bare ``import threads`` does not resolve, which is the collision closing
  itself.

The id is namespaced under :data:`NAMESPACE` rather than used bare, because
``sys.modules`` is one flat table shared with the Host's own imports: a folder
named ``math`` would otherwise not merely collide with the stdlib, it would
*replace* it for the whole process. The prefix keeps everything §7.2 asks for —
one module name per Applet id — and is invisible to authors, who write relative
imports either way.

Everything that can go wrong from here is a **compute-time fault** (§10.2): the
card looked normal in the browse view, because none of this is visible without
importing, which is exactly what the Host refuses to do at scan.
"""

import importlib.util
import sys
import traceback
from collections.abc import Callable
from types import ModuleType

from workshop_helper.discovery import APPLET_MODULE_FILENAME, Applet
from workshop_helper.manifest import Output
from workshop_utils import Cell, Result

COMPUTE = "compute"
NAMESPACE = "workshop_applets"


def module_name(applet_id: str) -> str:
    """The ``sys.modules`` name one Applet id owns, and nothing else does."""
    return f"{NAMESPACE}.{applet_id}"


class AppletFault(Exception):
    """A fault only reachable by importing or running the Applet (§10.2).

    ``details`` is what the collapsed Details disclosure shows — a full traceback
    where there is one, since it is your own machine and the trust model is out
    of scope (§10.3).
    """

    def __init__(self, summary: str, details: str) -> None:
        super().__init__(summary)
        self.summary = summary
        self.details = details


def run_compute(
    applet: Applet, values: dict[str, Cell], outputs: tuple[Output, ...]
) -> Result:
    """Import ``applet``, run its ``compute()``, and check what came back.

    ``values`` has already passed static validation (§4.3), so ``compute()``
    receives every declared Input, validated and never ``None``.
    """
    compute = _compute_function(applet)
    try:
        result = compute(values)
    except Exception as error:
        # Any exception escaping compute() is an unplanned crash (§10.2). The one
        # healthy refusal, InvalidInput, arrives with its consumer in #36.
        raise _crashed(f"{COMPUTE}() raised {type(error).__name__}") from error

    if not isinstance(result, Result):
        raise AppletFault(
            summary=f"{COMPUTE}() returned {type(result).__name__}, not a Result",
            details=f"{COMPUTE}() must return a workshop_utils.Result (spec §6).",
        )
    _check_output_names(result, outputs)
    return result


def _check_output_names(result: Result, outputs: tuple[Output, ...]) -> None:
    """Returned names must be the declared ones — never a silent gap (§4.5)."""
    declared = {output.name for output in outputs}
    returned = set(result.outputs)
    if returned == declared:
        return
    raise AppletFault(
        summary=f"{COMPUTE}() returned the wrong Outputs",
        details=(
            f"Declared: {_names(declared)}. Returned: {_names(returned)}. "
            "Every declared Output must come back, and nothing else (spec §4.5)."
        ),
    )


def _names(names: set[str]) -> str:
    """List Output names for the Details disclosure, or say there were none."""
    return ", ".join(sorted(names)) or "nothing"


def _compute_function(applet: Applet) -> Callable[[dict[str, Cell]], object]:
    """Import the Applet and hand back its ``compute()``."""
    module = _import_module(applet)
    compute = getattr(module, COMPUTE, None)
    if not callable(compute):
        raise AppletFault(
            summary=f"{APPLET_MODULE_FILENAME} defines no {COMPUTE}()",
            details=(
                f"A calculator must define {COMPUTE}() in "
                f"{APPLET_MODULE_FILENAME} (spec §3.2)."
            ),
        )
    return compute


def _import_module(applet: Applet) -> ModuleType:
    """Import ``applet.py`` under the Applet's id, once per process.

    A failed import is **not** left in ``sys.modules``: half a module is not an
    Applet, and the author fixing the file and reopening the page should get a
    real second attempt rather than the cached wreckage of the first.
    """
    name = module_name(applet.id)
    cached = sys.modules.get(name)
    if cached is not None:
        return cached

    path = applet.path / APPLET_MODULE_FILENAME
    spec = importlib.util.spec_from_file_location(
        name, path, submodule_search_locations=[str(applet.path)]
    )
    if spec is None or spec.loader is None:
        raise AppletFault(
            summary=f"{APPLET_MODULE_FILENAME} could not be loaded",
            details=f"No import machinery accepted {path}.",
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        del sys.modules[name]
        raise _crashed(
            f"{APPLET_MODULE_FILENAME} raised {type(error).__name__} on import"
        ) from error
    return module


def _crashed(summary: str) -> AppletFault:
    """Wrap the exception being handled, keeping its traceback for Details."""
    return AppletFault(summary=summary, details=traceback.format_exc())
