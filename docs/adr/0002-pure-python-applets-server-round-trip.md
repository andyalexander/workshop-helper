# Applets are pure Python; interactivity via server round-trip

Applets must be authorable by a Python developer (often with Claude Code) and hand-editable afterwards. We decided that interactive Applets recompute via a round-trip to the local Host — the browser sends changed inputs, the Applet's Python recomputes, and the Host returns fresh markup to swap in — so **an Applet author never writes JavaScript**. Because the Host is on localhost, the round-trip is sub-millisecond and feels instant.

## Considered Options

- **Client-side JavaScript** — rejected: faster for continuous interactions (e.g. dragging a slider at 60fps), but forces every contributor to write JS and risks formulae being expressed twice or in the wrong language.
- **Hybrid (Python compute, JS for polish)** — rejected: "when do I need JS?" becomes a judgement call for every contributor, which is the kind of ambiguity that kills a plugin ecosystem.

## Consequences

A continuously-dragged input that redraws a diagram would round-trip per frame. On localhost this is expected to be acceptable at this scale, but it is the trade-off being made.
