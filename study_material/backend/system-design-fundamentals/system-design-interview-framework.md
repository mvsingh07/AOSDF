---
concepts: [system-design-framework]
concept_category: System Design Process
difficulty: fundamental
prerequisites: [back-of-envelope-estimation]
interview_angle: >
  The framework itself is often what's being evaluated more than the final design — jumping straight to
  a detailed design without first clarifying requirements and scale is the single most common way this
  goes wrong, regardless of how good the eventual design is.
built_at: L6-T1
diagram: false
---

# System Design Interview Framework

## Definition

A repeatable structure for approaching an open-ended "design X" problem, so the conversation doesn't
either stall on ambiguity or dive into detail before the scope is agreed:

1. **Clarify requirements** — functional (what must it do) and non-functional (scale, latency,
   consistency vs. availability). Never assume; the "right" design for 1,000 users and 1 billion users is
   different.
2. **Estimate scale** — back-of-envelope numbers (`back-of-envelope-estimation.md`) for QPS, storage,
   bandwidth, informing which patterns are even relevant.
3. **High-level design** — the main components and how data flows between them, before drilling into any
   one piece.
4. **Deep dive** — pick the one or two components that are actually interesting or contentious (usually
   where a real trade-off lives — consistency model, sharding key, cache strategy) and go deep there.
5. **Identify bottlenecks and trade-offs** — single points of failure, hot spots, what breaks first under
   10x load, and what was explicitly traded away (e.g., availability for consistency).

## Example

For "design a rate limiter": clarify whether it's per-user or per-IP and whether it must work across
multiple servers (this single question decides whether the answer is a local in-memory counter or
`distributed-rate-limiting.md`) before writing anything down — skipping straight to "I'll use a token
bucket" without that clarification risks designing the wrong thing correctly.
