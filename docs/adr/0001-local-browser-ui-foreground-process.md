# Local browser UI served by a foreground process

The Host needs a UI on both macOS and Linux desktops, with no server infrastructure available and nothing running in the background. We decided the Host is a foreground CLI process that binds a fixed, non-obvious port on `127.0.0.1`, opens the user's default browser at it, and lives only until Ctrl-C — using the browser as its window rather than a GUI toolkit.

## Considered Options

- **TUI (e.g. Textual)** — rejected: rendering technical diagrams reliably across macOS Terminal and assorted Linux terminal emulators depends on inconsistent terminal image support, and graphics are a core requirement.
- **Native desktop GUI (Tkinter/PyQt/PySide)** — rejected: forces Applet authors to write GUI-toolkit code rather than plain Python, which raises the barrier for the contributor ecosystem we want.

## Consequences

This is not a daemon: nothing is installed as a service and nothing listens when the Host isn't running. "Minimal footprint" for this project means operational simplicity — no background processes, one command to start — not small binary or dependency size.
