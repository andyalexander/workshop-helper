# Library stack: web framework, round-trip mechanism, markdown renderer

Resolves [issue #3](https://github.com/andyalexander/workshop-helper/issues/3).

**Date:** 2026-07-15. All versions below were read from the PyPI/npm JSON APIs and
upstream repositories on that date. Claims marked **[verified]** were checked by running
the code on this machine (Python 3.14.6), not taken from memory or from secondary write-ups.

**Constraint applied throughout:** per ADR-0001, "minimal footprint" for this project means
*operational simplicity* — no background processes, one command to start — **not** dependency
byte size. Nothing below is rejected for being big.

## Summary

| Decision | Choice | Version (2026-07-15) |
| :--- | :--- | :--- |
| Web framework | **Flask** | 3.1.3 (2026-02-19) |
| Round-trip | **htmx, vendored**, over a form that works without it | 2.0.10 (2026-04-21) |
| Markdown | **markdown-it-py** | 4.2.0 (2026-05-07) |

Supporting: `jinja2` 3.1.6 (via Flask), `tomlkit` 0.15.0 (manifest write-back, per ADR-0004).

---

## 1. Web framework

### What this project actually is

Measured against the Host's real shape, not a generic "Python web app":

- It serves **HTML fragments**, never JSON (ADR-0002).
- It **starts and stops constantly** — a foreground CLI, alive until Ctrl-C (ADR-0001).
- Its input schema is **read from `manifest.toml` at runtime**, and the Host does its own
  validation and its own `default` write-back (ADR-0004).
- Applet compute is **plain synchronous Python** (ADR-0002).
- It must be **hand-editable** by a Python developer.

### Startup cost **[verified]**

Median of 7–9 subprocess runs, importing each realistic stack (Python 3.14.6, macOS):

| Stack | Median | Min |
| :--- | ---: | ---: |
| stdlib `http.server` + jinja2 | 31.5 ms | 29.7 ms |
| **Flask** (ships its own server) | **60.7 ms** | 56.5 ms |
| Starlette + jinja2 + uvicorn | 70.9 ms | 62.8 ms |
| FastAPI + uvicorn | 149.8 ms | 143.3 ms |

Bare imports: `fastapi` 141.5 ms vs `starlette` 45.6 ms vs `flask` 64.1 ms.

**Honest reading:** startup is a *weak* discriminator, and it does **not** point where one
might assume. Flask ships its own server, so it starts *faster* than Starlette+uvicorn — the
"Starlette is leaner" intuition is wrong once you count the ASGI server you must add back.
Flask vs Starlette is a ~10 ms difference: imperceptible next to launching a browser
(hundreds of ms). Only FastAPI's ~150 ms is a real, repeated tax — ~2.5x Flask, paid on every
single Host start, entirely for machinery this project does not use.

### Is FastAPI's headline strength relevant here? No — and it actively conflicts

FastAPI sells three things. Against this project:

1. **Generated OpenAPI docs** — *dead weight.* There is no API. Nothing consumes a schema;
   the client is one local browser receiving HTML fragments.
2. **Typed JSON APIs** — *dead weight.* The Host returns `text/html`. FastAPI's
   response-model serialisation is bypassed for every route.
3. **Pydantic validation** — *worse than dead weight; it structurally mismatches ADR-0004.*

Point 3 is the decisive one and deserves precision. FastAPI's validation works by reading
**static type annotations** on the endpoint signature. But ADR-0004 puts the input schema in
`manifest.toml`, discovered **at runtime**, and different for every Applet. There is no
signature to annotate. **[verified]** the workaround is to build a model per-Applet with
`pydantic.create_model()` — which produces a working validator but is invisible to FastAPI's
decorator/dependency-injection layer. You would be hand-rolling validation *anyway*, while
paying FastAPI's import cost and conceptual surface for a feature you had to route around.

ADR-0004 already commits the Host to owning manifest-driven validation so that Host features
stay generic. A framework whose validation story assumes compile-time-known schemas is
answering a question this project does not ask. **[verified]** the Host-owned equivalent is
about six lines of plain Python, and it returns an HTML error fragment — which is what the
browser needs anyway, and what a Pydantic `ValidationError` would have to be translated into.

### Why Flask over Starlette

Starlette is a genuinely strong candidate and this was close. It also cleared its biggest
historical objection during my knowledge gap: **Starlette 1.0.0 shipped 2026-03-22**, ending
eight years on ZeroVer ([release notes](https://raw.githubusercontent.com/encode/starlette/master/docs/release-notes.md)),
now at 1.3.1 (2026-06-12). Stability is no longer an argument against it. It also handles sync
endpoints correctly — **[verified]** `starlette/routing.py::request_response` wraps any
non-async callable in `run_in_threadpool`, so pure-Python compute works fine.

Flask still wins on this project's specific axes:

- **Operational simplicity (ADR-0001's actual definition).** Flask is one install with a
  server in the box. Starlette is `starlette` + `uvicorn` + `jinja2`, and a separate decision
  about how to run the ASGI app in-process. Fewer moving parts to explain and to start.
- **Hand-editability — and Starlette 1.0 regressed here.** The 1.0 release **removed
  `@app.route()`**, `@app.exception_handler()`, `@app.middleware()` and `on_event()`
  (see 1.0.0rc1 "Removed"). Routes must now be an explicit `routes=[Route(...)]` list. That is
  defensible design, but for a codebase whose selling point is that a Python developer can open
  it and edit it, Flask's `@app.get("/applet/<name>")` is the more legible idiom.
- **Sync all the way down.** Flask is WSGI and synchronous, which is exactly the shape of
  ADR-0002's compute model. Starlette is async-first and *bounces sync work to a threadpool* —
  correct, but a concept a contributor must hold that earns nothing here. There is no
  concurrency to exploit: one user, one browser, one calculation.
- **Familiarity.** The user is primarily a Python developer, and Flask is the most widely
  known Python web framework. For a project courting an Applet-contributor ecosystem, that
  matters more than elegance.
- **Templating included.** Jinja2 and `render_template` ship with Flask.

**The one real cost of Flask, and its fix [verified].** `app.run()` prints
`WARNING: This is a development server. Do not use it in a production deployment.` — confusing
noise in a workshop tool that is not, and will never be, a deployment. This is fully solvable
while *improving* the ADR-0001 lifecycle story:

```python
import logging, werkzeug.serving
logging.getLogger("werkzeug").setLevel(logging.ERROR)   # no per-request access log
srv = werkzeug.serving.make_server("127.0.0.1", PORT, app, threaded=True)
srv.serve_forever()          # Ctrl-C exits; srv.shutdown() for a clean stop
```

**[verified]** this yields no banner, no access-log spam, and a single Host-owned line
(`Workshop Helper running at http://127.0.0.1:PORT`), with a real server object to shut down.
`threaded=True` keeps a slow Applet from blocking asset requests. `waitress` 3.0.2 is an
alternative WSGI server with no dev-warning, but its last release was 2024-11-16 (20 months
ago) and it adds a dependency to solve a problem five lines already solve.

### RECOMMENDATION 1

**Use Flask 3.1.3**, served via `werkzeug.serving.make_server(..., threaded=True)` so the Host
owns its own console output and shutdown. Use Jinja2 (bundled) for the shell UI and fragments.

**Rejected:**

- **FastAPI 0.139.0** — all three headline strengths are irrelevant (no JSON API, no OpenAPI
  consumer) or structurally mismatched: ADR-0004's runtime-discovered TOML schema cannot be
  expressed as the static annotations FastAPI's validation and DI are built on, so its central
  feature would be routed around via `create_model()` while still costing ~150 ms per start
  (2.5x Flask) and a large conceptual surface. It is the wrong tool, not merely a heavy one.
- **Starlette 1.3.1** — a close, credible second, now genuinely stable post-1.0. Rejected
  because it needs uvicorn bolted back on (making it *slower to start than Flask*, not faster),
  because its async-first model earns nothing for single-user sync compute, and because 1.0's
  removal of `@app.route()` cuts against the hand-editability this project sells.
  **Revisit if** the Host ever needs streaming/SSE or long-lived connections.
- **stdlib `http.server`** — no routing, no templating (you would add Jinja2 regardless), and
  **[verified]** `cgi.FieldStorage`, the stdlib form parser, no longer exists: `import cgi`
  fails on Python 3.14.6, removed in 3.13 per [PEP 594](https://peps.python.org/pep-0594/).
  `urllib.parse.parse_qs` covers urlencoded forms, so this is survivable — but the endpoint is
  hand-rolling a small framework and maintaining it forever. That is more code and more debt
  than Flask, which contradicts "Less Code = Less Debt". The stdlib docs also caution
  `http.server` "only implements basic security checks".

---

## 2. Round-trip mechanism

ADR-0002 fixes the model — browser sends inputs, Python recomputes, Host returns fresh markup —
and the binding constraint: **an Applet author never writes JavaScript**.

### The key insight: the constraint binds *authors*, not the *Host*

ADR-0004 already makes the **Host** render the calculator form from the manifest schema. So the
`hx-*` attributes live in **Host-owned templates**. An Applet author never types one, never sees
one, and could not tell you which mechanism was chosen. **[verified]** end-to-end — the author's
entire surface stays:

```python
def compute(diameter: float, pitch: float) -> dict: ...   # pure Python, sync, no JS
```

while the Host emits:

```html
<form hx-post="/compute" hx-target="#result" hx-swap="innerHTML"
      hx-trigger="input changed delay:150ms from:find input">
```

This reframes the question. htmx's author-facing complexity here is **zero**, because authors
never touch the markup layer. The cost is borne once, by the Host.

### Do plain form POSTs suffice?

They work, and they should remain the **baseline**: a plain `<form method="post">` needs no JS
at all. But for the actual interaction — tweaking a diameter, reading a number, tweaking again —
a full-page POST reloads the document, loses focus and scroll position, and flashes on every
keystroke-triggered recompute. ADR-0002 promises interactivity that "feels instant"; a full
navigation per edit does not deliver that, even at sub-millisecond server time.

The good outcome is both: **[verified]** the form renders and computes correctly with no
JavaScript executing at all (server-rendered defaults + a plain POST), and htmx upgrades it to
fragment-swapping when present. Progressive enhancement, not dependence.

### Serving htmx locally (no CDN — this runs offline in a workshop)

- htmx **2.0.10** (2026-04-21), **[verified]** `htmx.min.js` = **51,238 bytes**, single file,
  **dependency-free** ([docs](https://htmx.org/docs/)).
- **[verified]** licensed **0BSD** — the most permissive license there is, explicitly allowing
  redistribution "with or without fee" and requiring **no attribution notice**. Vendoring the
  file into the repo is unambiguously fine and carries no ongoing obligation.
- Commit `htmx.min.js` to the Host's static directory and serve it from Flask's `/static`.
  No CDN, no npm, no build step, no network at runtime. Upgrades are "replace one file".

**[verified]** against the official docs, the two behaviours the Host relies on:

- **Form serialisation** — for non-GET requests htmx includes "the values of all inputs within"
  the enclosing form, keyed by `name` ([htmx docs, Parameters](https://htmx.org/docs/#parameters)).
  That is exactly ADR-0002's "browser sends the inputs".
- **Debounced recompute** — `hx-trigger="input changed delay:150ms"`: `delay` resets on each new
  event, `changed` suppresses firing when the value did not actually change
  ([hx-trigger reference](https://htmx.org/attributes/hx-trigger/)). This directly mitigates the
  trade-off ADR-0002 flagged (a dragged input round-tripping per frame) — with no Applet
  involvement.

### RECOMMENDATION 2

**Vendor htmx 2.0.10 as a single 0BSD-licensed file** served from the Host's own static
directory, and generate `hx-*` attributes in Host templates only. Build the form so it
**works with no JavaScript** (plain POST) and htmx upgrades it to fragment swaps — the
mechanism stays an implementation detail the Host can change later without touching a
single Applet.

**Rejected:**

- **Plain form POSTs alone** — the honest zero-dependency baseline, and worth keeping *as* the
  baseline, but a full-page reload per input edit loses focus and scroll and flashes, which
  fails ADR-0002's "feels instant" on the repeat-tweak loop that is a calculator's whole use.
- **Alpine.js 3.15.12** — solves a different problem (client-side state/behaviour), and does it
  by putting JS expressions into markup. Even confined to Host templates, it pulls compute-shaped
  logic toward the client, which is precisely the "formulae expressed twice or in the wrong
  language" failure ADR-0002 rejected.
- **Unpoly 3.14.3** — a legitimate server-driven option, but **[verified]** 179,176 bytes (3.5x
  htmx) and built around progressively enhancing *full-page navigation* (layers, targets,
  history). Rejected for concept count, not size: it is a larger model than "swap this fragment".
- **Datastar (datastar-py 1.0.2)** — signals + SSE-first. Reactive signals are more machinery
  than a form round-trip needs, the SSE model fits streaming rather than request/response, and
  its community is far smaller — a real risk for a tool meant to still work in ten years.
- **Vanilla `fetch`** — genuinely viable, and worth naming explicitly because the no-JS rule
  binds authors, not the Host: ~20 lines of Host-owned JS could do this. Rejected because those
  20 lines grow — debounce, request cancellation, error states, out-of-band swaps, race
  handling — into a worse-tested reimplementation of htmx's semantics. Adopting a stable
  51 KB 0BSD file is *less* code and less debt than maintaining a bespoke one.

---

## 3. Markdown renderer

All three candidates are pure Python. **[verified]** all three render the worked example — a
thread-pitch reference table with per-column alignment — correctly, emitting proper
`<table>/<thead>/<tbody>` with `text-align` on every cell:

| Renderer | Version | Tables | Invocation |
| :--- | :--- | :--- | :--- |
| markdown-it-py | 4.2.0 (2026-05-07) | ✅ + alignment | `MarkdownIt("commonmark").enable("table")` |
| mistune | 3.3.3 (2026-07-09) | ✅ + alignment | `create_markdown(plugins=["table"])` |
| Python-Markdown | 3.10.2 (2026-02-09) | ✅ + alignment | `markdown(src, extensions=["tables"])` |

**So tables do not decide this.** The decision rests on the other two things the ticket names:
relative-link/asset handling, and extensions.

### Relative links to PDFs in the Applet's own folder — the real discriminator

A documentation Applet writes `[datasheet](./tables/iso-metric.pdf)`. That file sits in the
Applet's folder, so the Host must rewrite the URL to wherever it mounts that Applet's assets
(e.g. `/applets/thread-pitch/assets/...`) while leaving absolute and external URLs alone. This
is a Host-side rewrite, and how cleanly each renderer supports it matters more than tables.

**[verified]** markdown-it-py does this cleanly via its token stream, using a **core rule** that
mutates tokens before rendering:

```python
def scope_assets(state):
    for tok in state.tokens:
        for child in (tok.children or []):
            attr = {"link_open": "href", "image": "src"}.get(child.type)
            if attr and (v := child.attrGet(attr)) and is_relative(v):
                child.attrSet(attr, urljoin(BASE, v))

md = MarkdownIt("commonmark", {"html": False}).enable("table")
md.core.ruler.push("scope_assets", scope_assets)
```

**[verified]** output — relative link and image rewritten, external URL untouched, alt text
preserved:

```html
<p>See <a href="/applets/thread-pitch/assets/tables/iso-metric.pdf">datasheet</a> and
<img src="/applets/thread-pitch/assets/img/thread.png" alt="thread diagram" /> and
<a href="https://x.com/a.pdf">ext</a>.</p>
```

> **Gotcha worth recording [verified]:** the *obvious* markdown-it-py approach — overriding the
> `image` render rule and calling `renderToken` — **silently drops alt text** (`alt=""`), because
> the default image rule renders the token's children into `alt`. Use the core-rule token walk
> above, not a render-rule override. mistune's renderer subclass does not have this trap.

mistune handles it just as cleanly via an `HTMLRenderer` subclass overriding `link()`/`image()`
(**[verified]**, alt text preserved naturally). Python-Markdown requires a `Treeprocessor` —
workable but the most indirect of the three.

### Extensions

- **markdown-it-py** — `mdit-py-plugins` 0.6.1 **[verified]** provides `anchors`, `attrs`,
  `container`, `deflist`, `footnote`, `front_matter`, `tasklists`, `admon`, `colon_fence`,
  `dollarmath`, `texmath`, `field_list`, `gfm`, and more. Covers every plausible future need.
- **Python-Markdown** — the largest ecosystem; **[verified]** `tables`, `toc`, `attr_list`,
  `def_list`, `footnotes`, `admonition`, `fenced_code`, `md_in_html`, `abbr`, `meta` all
  built in, plus PyMdown Extensions.
- **mistune** — **[verified]** `table`, `footnotes`, `def_list`, `task_lists`, `abbr`, `math`,
  `strikethrough`, `mark`, `insert`, `spoiler`, `url` built in. Adequate, smallest of the three.

### Why markdown-it-py

- **CommonMark compliance.** markdown-it-py is a spec-tested port of the JS `markdown-it`.
  Applet authors will draft markdown and expect it to behave like it does on GitHub. Neither
  Python-Markdown (an implementation of Gruber's original, predating and diverging from
  CommonMark) nor mistune is CommonMark-spec-tested. For a *contributor ecosystem*,
  predictable-and-portable beats fast-or-featureful.
- **The token stream is the right architecture for the Host's asset rewriting**, which is a
  hard requirement, not a nice-to-have.
- **Safety lever for contributed content.** **[verified]** the `html` option defaults per preset:
  `commonmark` → `html=True`, `gfm-like` → `True`, `js-default` → `False`, `zero` → `False`.
  Passing `{"html": False}` escapes raw HTML in Applet markdown — **[verified]**
  `<script>alert('xss')</script>` renders inert. Applets are user-installed and semi-trusted, but
  an explicit lever is worth having, and ADR-0004 already establishes that merely *listing* a
  contributed Applet must not run its code.
- **High-trust maintenance.** It underpins MyST/Sphinx/Jupyter — a large, invested user base.

> **Trap worth recording [verified]:** do **not** reach for the `gfm-like` preset just to get
> tables. It enables `linkify`, which raises `ModuleNotFoundError: Linkify enabled but not
> installed.` at render time unless `linkify-it-py` is also installed. `MarkdownIt("commonmark")
> .enable("table")` gets GFM tables with no extra dependency and no runtime landmine.

### RECOMMENDATION 3

**Use markdown-it-py 4.2.0**, configured as `MarkdownIt("commonmark", {"html": False})
.enable("table")`, with a `core.ruler` rule to scope relative links/images onto the Applet's
asset mount. Add `mdit-py-plugins` only if/when a specific need (anchors, footnotes, admonitions)
actually arrives.

**Rejected:**

- **Python-Markdown 3.10.2** — biggest extension ecosystem, but not CommonMark (it implements
  Gruber's original), so author markdown will not always match GitHub's rendering. Two verified
  sharp edges: tables **silently degrade** to a paragraph of raw `|` pipes if the `tables`
  extension is forgotten (no error), and **[verified]** `attr_list` **corrupts the table** in the
  common `{: .ref-table }`-after-table position — the attribute line was swallowed and rendered
  as an extra table row. Link rewriting needs the most indirect API (`Treeprocessor`).
- **mistune 3.3.3** — the closest call, and the fastest (**[verified]** ~15 ms import vs
  markdown-it-py's ~23 ms; both irrelevant at this scale). Its renderer-subclass API is arguably
  the most pleasant for the rewriting job. Rejected for **predictability, not capability**: it is
  not CommonMark-spec-tested, its plugin set is the thinnest, and it has a track record of
  breaking API rewrites across majors (2.x → 3.x), which is a poor fit for a hand-editable tool
  meant to keep working untouched for years.

---

## Resulting dependency set

```toml
dependencies = [
    "flask>=3.1.3",        # web framework (bundles jinja2, werkzeug, click)
    "markdown-it-py>=4.2.0",  # documentation Applets
    "tomlkit>=0.15.0",     # manifest write-back (ADR-0004: tomllib reads, cannot write)
]
```

Vendored, not a dependency: `htmx.min.js` 2.0.10 (0BSD, 51 KB) in the Host's static directory.
Reading manifests uses stdlib `tomllib` (3.11+). Install with `uv add`, per project convention.

## Staleness notes

Today is 2026-07-15 and my training data predates several of these facts; everything above was
re-verified on the day rather than recalled. Two items were materially different from my prior
knowledge and are worth flagging for anyone re-reading this later:

- **Starlette reached 1.0.0 on 2026-03-22** (now 1.3.1), leaving ZeroVer after eight years, and
  in doing so **removed the `@app.route()` decorator** and the `on_event`/`on_startup` hooks.
  Any pre-2026 comparison of Starlette — including one drawn from memory — is out of date in
  both directions: more stable than it was, less decorator-friendly than it was.
- **`cgi` is gone from the stdlib** (removed 3.13, PEP 594), which changes the `http.server`
  calculus versus older advice that assumed `cgi.FieldStorage` for form parsing.

Also current as of this date: FastAPI 0.139.0 (still ZeroVer), Flask 3.1.3, htmx 2.0.10,
mistune 3.3.3, Python-Markdown 3.10.2, markdown-it-py 4.2.0, waitress 3.0.2 (last release
2024-11-16 — ageing).

## Sources

Primary sources, all fetched 2026-07-15:

- Starlette release notes (1.0/1.3, removals): https://raw.githubusercontent.com/encode/starlette/master/docs/release-notes.md
- Starlette `request_response` threadpool behaviour: https://raw.githubusercontent.com/encode/starlette/master/starlette/routing.py
- Starlette templates / StaticFiles: https://raw.githubusercontent.com/encode/starlette/master/docs/templates.md, `.../docs/staticfiles.md`
- htmx docs (local install, dependency-free): https://htmx.org/docs/
- htmx parameters / form serialisation: https://htmx.org/docs/#parameters
- htmx `hx-trigger` modifiers (`delay`, `changed`, `throttle`, `from`): https://htmx.org/attributes/hx-trigger/
- htmx 0BSD licence: https://raw.githubusercontent.com/bigskysoftware/htmx/master/LICENSE
- markdown-it-py usage, presets and rules: https://markdown-it-py.readthedocs.io/en/latest/using.html
- mistune plugins (table): https://raw.githubusercontent.com/lepture/mistune/main/docs/plugins.rst
- PEP 594 (`cgi` removal): https://peps.python.org/pep-0594/
- Version/date/dependency metadata: PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`) and
  npm registry (`https://registry.npmjs.org/<pkg>`)
