---
concepts: [twelve-factor-app]
concept_category: DevOps/Infra
difficulty: intermediate
prerequisites: []
interview_angle: >
  Don't just recite the list — pick two or three factors (Config, Processes, Disposability are
  common ones) and explain a concrete bug you'd expect from violating them in production.
built_at: L6-T1
diagram: false
---

# The Twelve-Factor App

## Definition

A methodology (from Heroku, 2011) for building SaaS applications that are portable across
environments and scale cleanly. The twelve factors: **I.** one codebase, many deploys; **II.** explicit
dependencies, never assumed system-wide packages; **III.** config in environment variables, never in
code; **IV.** backing services as attached resources (swappable via config, e.g. a database URL);
**V.** strict separation of build/release/run stages; **VI.** stateless processes — no in-memory session
state that a restart would lose; **VII.** port binding — the app is self-contained, not injected into a
runtime container; **VIII.** concurrency via the process model, not thread-juggling inside one process;
**IX.** disposability — fast startup, graceful shutdown; **X.** dev/prod parity — keep environments as
similar as possible; **XI.** logs as event streams, not files the app manages; **XII.** admin/management
tasks run as one-off processes against the same codebase.

## Example

Factor III violated:

```python
DATABASE_URL = "postgres://prod-user:hunter2@db.internal:5432/app"  # hard-coded
```

Factor III applied:

```python
DATABASE_URL = os.environ["DATABASE_URL"]  # same code, different value per environment
```

Factor VI violated: storing a logged-in user's shopping cart in a Python dict in server memory — a
second server behind a load balancer, or a restart, silently loses the cart. Applied: cart state lives in
Redis or the database, so any process can serve the next request for that user.

## Why It Still Matters

This is the exact discipline this framework's own `AOSDF-Hosting` build pipeline follows: per-product
GitHub PATs and the Vercel API token are read from environment/config, never hard-coded into
`pipeline.py` (Factor III), and each build runs in a fresh, ephemeral worker rather than a long-lived
mutable one (Factor IX, and Principle 34's "least trust" sandboxing).
