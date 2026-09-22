---
concepts: [dry-principle, kiss-principle, yagni-principle]
concept_category: Software Design
difficulty: fundamental
prerequisites: []
interview_angle: >
  These three principles frequently pull against each other — be ready to explain a case where
  removing duplication (DRY) actually made code harder to read (violating KISS), and where you
  chose to keep the duplication instead.
built_at: L6-T1
diagram: false
---

# DRY, KISS, and YAGNI

## Definition

- **DRY (Don't Repeat Yourself):** every piece of knowledge should have a single, unambiguous
  representation in a system. Not "never write similar-looking code twice" — specifically, never let
  the *same fact* (a business rule, a formula, a schema) live in two places that can drift apart.
- **KISS (Keep It Simple, Stupid):** prefer the simplest design that solves the actual problem — most
  systems fail from unnecessary complexity, not from insufficient cleverness.
- **YAGNI (You Aren't Gonna Need It):** don't build a capability until an actual requirement needs it —
  speculative generality ("we might need multi-currency support someday") costs real complexity now for
  a maybe-benefit later.

## Example

A YAGNI violation: building a plugin architecture with a `PaymentProviderRegistry` for a product that
has exactly one payment provider and no near-term plan for a second. The abstraction has real cost
(more files, more indirection) and zero current payoff.

A DRY violation caught late: a discount-percentage calculation duplicated in both the checkout page and
the invoice PDF generator. Six months later, a tax-rule change updates one copy and not the other —
customers see two different totals for the same order.

## The Tension

This framework's own `Reusable Architecture Patterns` section (`framework.md`) is explicit that patterns
like Tenant Reputation Gating apply *only* when a project matches a specific criterion, and declining a
pattern requires a one-line reason — that's YAGNI enforced as a documented discipline, not a vague
intuition. Three similar lines of code is often genuinely better than a premature shared abstraction; the
judgment call is whether the duplication is *coincidental* (KISS/YAGNI wins) or the *same fact* expressed
twice (DRY wins).
