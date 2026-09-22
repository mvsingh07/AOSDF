---
concepts: [continuous-integration, continuous-delivery, continuous-deployment]
concept_category: DevOps/Infra
difficulty: fundamental
prerequisites: [unit-testing]
interview_angle: >
  Know the precise distinction between continuous delivery and continuous deployment (a human
  approval gate vs. none) — it's a common trick question and the two terms get conflated constantly.
built_at: L6-T1
diagram: true
---

# CI/CD Fundamentals

## Definition

- **Continuous Integration (CI):** every code change is automatically built and tested against the main
  branch, frequently (ideally on every push) — catches integration problems early, before they compound.
- **Continuous Delivery (CD):** every change that passes CI is automatically prepared for release
  (built, tested, packaged) and *could* be deployed at any time — but an actual production deploy still
  requires a deliberate human trigger.
- **Continuous Deployment:** the same pipeline, but every change that passes all checks is deployed to
  production automatically, with no human gate at all.

## Example

A typical pipeline: push → run linter → run unit tests → run integration tests → build artifact → (CD:
stop here, awaiting human approval) → (Continuous Deployment: proceed automatically) → deploy → run
smoke tests against the live deploy.

## Diagram

```aosdf-diagram
┌───────┐   ┌─────────┐   ┌────────┐   ┌─────────┐         ┌──────────┐
│  Push  │──▶│  Build  │──▶│  Test  │──▶│ Package │──▶ ??? ─▶│  Deploy  │
└───────┘   └─────────┘   └────────┘   └─────────┘         └──────────┘
                                              │
                          Continuous Delivery: human clicks "Deploy" here
                          Continuous Deployment: no gate, proceeds automatically
```

## Where AOSDF Draws This Line Deliberately

This is directly Principle 24 in this framework: "human-triggered only" for anything that publishes or
deploys — `AOSDF-Hosting`'s pipeline is Continuous Delivery at most, never Continuous Deployment. A build
can be triggered from the dashboard, but nothing pushes to production automatically on a `git push` (see
`aosdf_expansion_scope_2.md` §4 — "Does not auto-rebuild on push" is an explicit MVP non-goal, not an
oversight).
