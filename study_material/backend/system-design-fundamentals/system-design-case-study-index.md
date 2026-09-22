---
concepts: [system-design-case-studies]
concept_category: System Design Process
difficulty: intermediate
prerequisites: [system-design-framework]
interview_angle: >
  Well-known "design X" interview problems are rarely testing knowledge of X itself — they're testing
  whether you recognize which of the concepts already in this corpus apply, and pick the right one for
  the stated scale and consistency requirements. This index is the lookup table for that recognition step.
built_at: L6-T1
diagram: false
---

# System Design Case Studies — A Concept Lookup Index

## Definition

Classic "design X" interview prompts are not a separate body of knowledge — each one is a combination of
concepts already covered elsewhere in this corpus, applied to a specific product. This file is
deliberately **not** a full walkthrough of any of these designs (that's a much longer, product-specific
exercise); it's an index mapping well-known prompts to the concept files here that are actually
load-bearing for them, so the framework-level baseline stays a lookup table, not a growing pile of
bespoke, product-specific solutions.

## Example — The Lookup Table

| Well-known prompt | Primarily exercises |
| --- | --- |
| URL shortener | `unique-id-generation.md`, `caching-strategies.md`, `database-indexing.md` |
| Rate limiter | `rate-limiting-algorithms.md`, `distributed-rate-limiting.md` |
| Web crawler | `message-queues.md`, `distributed-rate-limiting.md`, `backpressure-and-thundering-herd.md` |
| Notification / chat system | `message-queues.md`, `message-delivery-semantics.md`, `reliable-messaging-patterns.md` |
| News feed | `caching-strategies.md`, `sharding-and-rebalancing.md`, fan-out trade-offs (write-time vs. read-time) |
| Search autocomplete | `database-indexing.md`, `caching-strategies.md`, `tail-latency-and-hedging.md` |
| Key-value store / object storage | `consistent-hashing.md`, `database-replication.md`, `consistency-models.md` |
| Distributed message queue | `message-delivery-semantics.md`, `write-ahead-log.md`, `backpressure-and-thundering-herd.md` |
| Metrics monitoring & alerting | `observability.md`, `backpressure-and-thundering-herd.md` |
| Payment system / digital wallet | `acid-transactions.md`, `isolation-levels.md`, `saga-pattern.md`, `reliable-messaging-patterns.md` (idempotency) |
| Ad click / event aggregation | `message-queues.md`, `sharding-and-rebalancing.md`, `database-replication.md` |

## The Real Takeaway

Recognizing "this prompt is mostly a sharding + consistency-model problem" or "this prompt is mostly an
idempotent-write problem" in the first two minutes is the actual skill (`system-design-interview-
framework.md`) — the product framing (URL shortener vs. payment system) changes the numbers and the
constraints, not the underlying toolbox.
