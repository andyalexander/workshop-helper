# Workshop Helper

A local-first framework for browsing and running small, pluggable reference tools — calculators and documentation — for workshop and house use.

Everything runs on your own machine. The Host binds to `127.0.0.1` only, so nothing is exposed to the network.

For the domain language (Host, Applet, Manifest, Overlay, Root, Facet, Fault) see [CONTEXT.md](CONTEXT.md); for the full behaviour, [docs/spec/host-framework.md](docs/spec/host-framework.md).

## Requirements

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)** — the only supported way to install and run this project

## How to run

From the repository root:

```bash
./scripts/run.sh
```

That syncs dependencies and starts the Host. It then opens your browser at <http://127.0.0.1:8731/>.

To use a different port, pass it through — arguments go straight to the underlying command:

```bash
./scripts/run.sh --port 9000
```

If you would rather not use the script, the equivalent is:

```bash
uv sync
uv run workshop-helper
```

### What you should see

The startup summary, the address, then a browser window:

```
Loaded 3 Applets; 0 failed. 1 Root skipped.
Serving Workshop Helper on http://127.0.0.1:8731/  (Ctrl-C to stop)
 * Serving Flask app 'workshop_helper.app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:8899
Press CTRL+C to quit
```

The first line is the startup summary — how many Applets were loaded, how many were refused as **Faults**, and how many **Roots** were skipped because their directory does not exist. Refused Applets are not hidden: they appear in the UI as greyed, un-openable cards explaining why.

Two things there are expected, not problems:

- **`1 Root skipped.`** on a first run simply means `~/.workshop-helper/applets/` does not exist yet. Create it when you have an Applet of your own to put in it.
- **The development-server warning** comes from Flask itself. It is aimed at people deploying to the internet; this Host binds to `127.0.0.1` and is meant to be run exactly this way.

Requests are logged to the console as you use the UI.

### Stopping it

The Host is a **foreground process, never a daemon**. It holds the terminal until you press **Ctrl-C**.

### Running it twice

Starting the Host when it is already running is harmless and does exactly what you want:

```
Workshop Helper already running on http://127.0.0.1:8731/
```

A busy port is read as "a copy is already up", so the Host opens your browser at the running instance and exits cleanly rather than starting a second one or reporting an error.

### Choosing a port

`--port` is a command-line flag only, deliberately — there is no configuration key for it. The default is **8731**.

## Where your files live

The Host keeps everything in one directory, `~/.workshop-helper/`. There is no XDG split. Set `WORKSHOP_HELPER_HOME` to put it somewhere else:

```bash
WORKSHOP_HELPER_HOME=~/tmp/wh-test ./scripts/run.sh
```

The directory holds:

| Path | Written by | Purpose |
| --- | --- | --- |
| `applets/` | you | Your own Applets — the `own` Root |
| `config.toml` | you | Hand-edited; declares additional Root directories |
| `overlay.toml` | the Host | Your saved defaults and overrides |

Nothing needs to exist before the first run. A missing home directory, a missing `config.toml`, and a missing Root are all normal — the Host skips them and reports the count in its startup summary.

The Overlay is **always safely discardable**: deleting it returns the Host to a pristine state, losing only your saved defaults and calibration overrides. Your Applets are never modified — the Host only ever reads a Manifest, never writes to one.

## Adding your own Applets

The Host scans **Roots** in a fixed order, and that order is also the precedence rule when two Applets collide on a name:

1. **`own`** — `~/.workshop-helper/applets/`
2. **`built-in`** — the three Applets shipped in the wheel (`pipe-bender`, `thread-finder`, `thread-pitch`)
3. **foreign** — each path listed in `config.toml`, in the order written

To drop in your own, create `~/.workshop-helper/applets/` and put an Applet folder in it. To add a collection from elsewhere, list it in `~/.workshop-helper/config.toml`:

```toml
roots = [
    "~/src/mate-collection/applets",
    "~/Documents/workshop-applets",
]
```

Paths are `~`-expanded and keep the order you write them in. A Root named `applets` takes its display name from the folder above it, so the first entry above shows as Root `mate-collection`.

Restart the Host to pick up new Applets — discovery runs once, at startup.

For writing an Applet, see [docs/authoring/calculator-modes.md](docs/authoring/calculator-modes.md).

## Development

```bash
uv run pytest        # tests
uv run ruff format . # format
uv run ruff check .  # lint
uv run pyright       # type check
```

Add dependencies with `uv add <package>` (never `pip`).
