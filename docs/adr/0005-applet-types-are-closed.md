# Applet types are a closed set owned by the Host

The Applet type set is closed: `documentation` and `calculator`. Adding a type is a change to the Host, not something an Applet or a contributor can do.

An Applet type is not a category — it is **a rendering contract the Host implements**. `documentation` means "read `content.md`, render it, serve the folder's assets." `calculator` means "build a form from the Manifest's inputs, import `applet.py`, call `compute()`, render the Result." Those are Host behaviours. For a contributor to add a type they would have to ship rendering code into the Host, at which point the Host no longer knows what it is rendering and every generic affordance it provides — defaults, validation, consistent formatting — stops working.

The pressure for more types appears to be imaginary at this stage: a unit converter is a calculator, a checklist is documentation, a parts reference is documentation with a table, a torque lookup is a calculator returning a table. The full set of known use cases fits in two types.

## Considered Options

- **Open/registerable types (contributors ship renderers)** — rejected: maximum extensibility, but it dissolves the Host's generic features and makes every Applet type a bespoke thing that cannot be reasoned about.
- **Closed types plus an `html` escape hatch on the calculator Result** — accepted as the pressure valve. Anything exotic can be a calculator returning `html`, covering the long tail without opening the type system.

## Consequences

Closed is reversible — a third type can be added later — whereas open is not: once contributors ship renderers, that cannot be withdrawn without breaking them. This decision deliberately retains control while the shape of the project is still unknown.
