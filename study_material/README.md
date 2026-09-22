# Study Material — Framework-Curated Baseline

# AOSDF v3.1 — Track L (Learning), builds `L6` (`aosdf_expansion_scope_2.md` §6, `execution_plan.md` L6-T1/L6-T2)
# Resolves OD-H7 (ownership + refresh cadence) — see "Ownership & Refresh Cadence" below.

---

## Why This Exists

`concept_indexer_agent` today only ever indexes a *product's own* Concept Frontmatter — real design
decisions, captured at the moment they were made. That's deliberately narrow: Principle 28/29 forbid an
agent from inventing learning content. But it means a brand-new product with three ADRs has a three-node
roadmap, even though "what is a REST API" or "what does ACID mean" are things every engineer on that
product already needs and nobody wrote an ADR about.

`study_material/` is the answer: a **framework-level, not project-level**, curated baseline of
widely-recognized software engineering principles, frontend topics, and backend topics — sourced and
maintained by whoever curates AOSDF itself, not derived from any one product's decisions. It ships once,
here, and every product gets to draw on it.

This is the one deliberate, documented exception to "Learning content is derived, never duplicated"
(Principle 28) at the *framework* level — the same way `aosdf_expansion_scope_2.md` §6 already carved out
a parallel, per-project exception for uploaded reference material (`L7`). `study_material/` is original
content, on purpose: someone has to write "what SOLID means" down somewhere, once, so it doesn't have to
be re-derived from scratch inside every product's own frontmatter.

---

## Two Distinct Reference Sources — Don't Conflate Them

| | `AOSDF/study_material/` (this folder) | `documents/16_Learning_Roadmap/reference_material/` (`L7`, per-project) |
| --- | --- | --- |
| Level | Framework | Product |
| Authored by | AOSDF's own curators (human + `architect_agent`) | Each product's own team, uploading their own course/book/notes |
| Scope | Fixed, general baseline — SOLID, REST vs GraphQL, ACID, etc. | Whatever that specific product's team chose to upload |
| Status | **`L6`, this document — building now** | **`L7`, not started** — depends on this folder existing first |

Both eventually feed the same `concept_indexer_agent` merge mode (`L7`), joined against
`concept_vocabulary.md` (`OD-8`) to prevent silent ID duplication across all three sources (product
frontmatter, this baseline, and per-project uploads) — see `AOSDF/reference/concept_vocabulary.md` §4.
**Until `L7` ships, this folder is inert** — nothing reads it yet. It's being built now, ahead of that
merge mode, the same sequencing `L5` used ahead of `L6`/`L7`.

---

## Format — Same Concept Frontmatter Standard, No Exceptions

Every file in this folder follows `framework.md`'s **Concept Frontmatter Standard** exactly — the same
`concepts` / `concept_category` / `difficulty` / `prerequisites` / `interview_angle` / `built_at` /
`diagram` block as any ADR. `built_at` on every file here is `L6-T1` (the task this baseline was authored
under) rather than a product-specific task ID — there is no product decision to point to; the "decision"
is "this is a foundational concept worth including in the baseline."

Body structure, kept deliberately brief per the task's own scope ("brief definitions and examples," not
a textbook):

1. **Definition** — two to four sentences, plain language.
2. **Example** — a short code snippet or concrete scenario, never abstract-only.
3. **Diagram** (only when `diagram: true`) — an `aosdf-diagram` fenced block, same convention as
   everywhere else in this framework.

## Diagram Format: `aosdf-diagram`, Never Archify

Track P (per-project MkDocs sites) uses [Archify](https://github.com/tt-a1i/archify) for real rendered
diagrams (`OD-H11`, `R3`) — but `study_material/` is explicitly excluded from that, for the same reason
Track L's own `render/index.html` is (`framework.md` § Richer Diagrams: Archify): a generated Archify
diagram links to Google Fonts, which breaks the offline-first, zero-external-call guarantee
`render/index.html` holds itself to (Principle 30). Since this folder's whole purpose is eventually being
inlined into `roadmap_graph.json`'s `diagram` field (`L7`'s merge mode, verbatim per the existing
`concept_indexer_agent` step 6 rule — see that agent's file), every diagram here **must** already be a
plain-text `aosdf-diagram` fence, the same format `concept_indexer_agent` already knows how to extract
verbatim. This was a deliberate check made before writing any content, not an oversight.

---

## Ownership & Refresh Cadence (`OD-H7`, resolved 2026-09-08)

**Decision:** no fixed calendar cadence (e.g. "review quarterly") — that invites either neglect (nobody
actually does the quarterly review) or busywork (reviewing topics that haven't changed). Instead:

- **Curation is opportunistic, triggered by actual need** — a new topic is added here the same way a new
  ADR triggers Concept Frontmatter: at the moment someone (human or `architect_agent`, acting on human
  instruction — this is never machine-invented per Principle 29) recognizes a gap, not on a schedule.
- **Each file's own `built_at` is its staleness signal.** There's no separate "Last reviewed" field to
  drift out of sync (the exact failure mode Principle 31 already warns about for denormalized status) —
  if a topic's accepted best practice changes materially, the fix is to edit that file directly and note
  it in the file's own prose, not to maintain a second freshness tracker.
- **Owner: whoever is curating AOSDF itself** (currently: the human + `architect_agent`, same as every
  other framework-level document — `framework.md`, `reference/*.md`). Not a per-product responsibility;
  a product consuming this baseline never edits it directly — corrections flow back here, the single
  copy, never forked per-product.
- **Coverage is intentionally partial at any given time** — this is seeded in iterations (this file's own
  first commit covers three initial topic areas; see below), never a one-time content dump meant to be
  exhaustive on day one.

---

## Current Coverage

**Iteration 1 (2026-09-08):**

| Folder | Topics covered |
| --- | --- |
| `principles/` | SOLID, DRY/KISS/YAGNI, the Twelve-Factor App, common design patterns, architecture styles (monolith/microservices/event-driven/layered), the testing pyramid, CI/CD fundamentals |
| `frontend/` | The DOM & critical rendering path, the JavaScript event loop, component-based UI, client state management, rendering strategies (CSR/SSR/SSG/ISR), web accessibility, web performance |
| `backend/` | REST vs GraphQL, relational vs NoSQL, ACID & transactions, database indexing, caching strategies, message queues & pub/sub, authentication vs authorization, concurrency models, load balancing & rate limiting, observability |

**Iteration 2 (2026-09-08) — `backend/distributed-systems/`,** added opportunistically at the human's
direct request for deeper, senior/staff-level backend and distributed-systems reliability/consistency
topics (24 files, same Concept Frontmatter format as iteration 1, tightly-related concepts grouped per
file the same way `architecture-styles.md` groups four related styles):

| File | Concepts covered |
| --- | --- |
| `cache-failure-patterns.md` | Cache stampede, cache penetration, cache avalanche |
| `connection-pooling.md` | Database connection pooling |
| `tail-latency-and-hedging.md` | Tail latency (p99), request hedging |
| `database-mvcc.md` | MVCC (multi-version concurrency control) |
| `saga-pattern.md` | Saga pattern vs. two-phase commit |
| `distributed-consensus.md` | Leader election, quorum, split-brain |
| `resilience-patterns.md` | Circuit breaker, cascading failures, bulkhead pattern, graceful degradation |
| `distributed-rate-limiting.md` | Rate limiting with shared state across instances |
| `sharding-and-rebalancing.md` | Sharding, hot partitions, partition rebalancing |
| `distributed-time.md` | Clock skew, logical clocks, vector clocks |
| `consistency-models.md` | Read-your-writes, eventual, and strong consistency |
| `consistent-hashing.md` | Consistent hashing (the ring, virtual nodes) |
| `write-ahead-log.md` | Write-ahead log (WAL) |
| `change-data-capture.md` | Change data capture (CDC) |
| `api-pagination.md` | Offset vs. cursor/keyset pagination |
| `concurrency-control-and-locking.md` | Optimistic vs. pessimistic locking, distributed locks |
| `backpressure-and-thundering-herd.md` | Thundering herd problem, backpressure |
| `reliable-messaging-patterns.md` | Dead letter queue, outbox pattern, idempotency |
| `query-execution-plans.md` | Query execution plans, `EXPLAIN` |
| `isolation-levels.md` | Transaction isolation levels, dirty/non-repeatable/phantom reads |
| `cache-validation.md` | Cache validation (ETag, conditional requests) |
| `retries-and-backoff.md` | Retry policy, exponential backoff, jitter |
| `message-delivery-semantics.md` | At-most-once, at-least-once, exactly-once processing |
| `database-replication.md` | Leader-follower replication, sync vs. async, replication lag |

**Iteration 3 (2026-09-09) — `backend/system-design-fundamentals/`,** the human pointed at
[`liquidslr/system-design-notes`](https://github.com/liquidslr/system-design-notes) (public notes on the
book *System Design Interview — An Insider's Guide*) as a candidate source. **That repo carries no
license** (default copyright applies) and is itself a derivative of a commercially-published book, so no
text from it was copied — its table of contents was used only to gap-check this corpus against well-known
interview topics, then five files were authored here from scratch, in AOSDF's own words and format:

| File | Concepts covered |
| --- | --- |
| `horizontal-vs-vertical-scaling.md` | Scaling up vs. scaling out |
| `back-of-envelope-estimation.md` | Capacity estimation (QPS, storage, bandwidth) |
| `system-design-interview-framework.md` | The clarify → estimate → design → deep-dive → bottlenecks structure |
| `rate-limiting-algorithms.md` | Token bucket, leaky bucket, fixed window counter, sliding window log |
| `unique-id-generation.md` | UUID vs. Snowflake ID, why sharded auto-increment breaks |
| `system-design-case-study-index.md` | A lookup table mapping well-known "design X" prompts (URL shortener, chat system, payment system, etc.) to which concepts *already in this corpus* they exercise — no full case-study designs are reproduced here, by design (see the file itself for why) |

If a future source under a real open license (MIT/CC-BY/etc.) is identified, its content can be adapted
directly per its license terms rather than treated as inspiration-only — the restriction above is specific
to this unlicensed repo, not a blanket policy against external sources.

Not yet covered (future iterations, add as gaps are actually noticed — no fixed backlog list is
maintained here on purpose, per the "opportunistic, not scheduled" rule above): mobile-specific topics,
cloud provider primitives (AWS/GCP/Azure service catalogs), infrastructure-as-code, container
orchestration, specific language idioms beyond JavaScript's event loop, full applied system-design
walkthroughs (deliberately out of scope — see `system-design-case-study-index.md`). Add a subfolder (e.g.
`cloud/`, `mobile/`) the same way `principles/`/`frontend/`/`backend/`/`backend/distributed-systems/`/
`backend/system-design-fundamentals/` were added — no restructuring required.
