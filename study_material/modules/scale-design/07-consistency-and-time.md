# Consistency, partitions, and time

**Consistency** describes what different clients can observe about updates. The word has several precise meanings; choose a user-facing guarantee before choosing a database label. Our editor should see a confirmed version 8 on the next read. A public document count may tolerate a short delay. These are different contracts.

## Name the observation you promise

**Read-your-writes** means a client that successfully saved version 8 does not subsequently see version 7. **Eventual consistency** means replicas can temporarily disagree but converge if updates stop and communication resumes; it does not promise a particular delay. Some operations need stronger ordering, such as accepting only one successful update from a given base version. Use an authoritative primary transaction or a storage system with the required conditional write behavior.

During a **network partition**, two sides cannot communicate. The familiar CAP result concerns whether a distributed data service can provide linearizable responses and availability to every request while that partition persists. It does **not** say systems choose only two properties for all time, nor that a database is simply “CP” or “AP” in every operation. The useful design question is: for this operation and failure, do we reject/delay a response or permit a response that may be stale or conflicting? A document edit should usually refuse to claim success without durable authoritative acceptance; a cached public thumbnail can often remain available.

Wall clocks can disagree across machines. Do not use client timestamps as the sole ordering or conflict rule. Use database-assigned versions or transaction sequence for edits; record wall-clock time for display and diagnostics. Clock skew can also affect token expiry and lease logic, so tolerate bounded skew and avoid treating a timestamp as proof of a unique global order.

## Diagram: versioned read after write

![A primary confirms version eight while a lagging replica still holds version seven; the editor's next read follows the primary or waits for the replica.](/learning/scale-design/consistency.svg)

```aosdf-diagram
Editor ──save v8──▶ PRIMARY v8 ──async copy──▶ REPLICA v7 → v8
Editor ──next read──▶ PRIMARY v8 (or replica after v8 is visible)
```

## Implementation: express the promise in API and storage

PostgreSQL's transaction isolation and conditional updates can enforce the edit version. OpenTelemetry can trace the save and the next read across primary and replica. Redis may serve eventually consistent counts or bounded-stale listings, but it should not become the sole authority for a confirmed edit.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![postgresql logo](/learning/scale-design/logo-postgresql.svg) | [PostgreSQL transactions](https://www.postgresql.org/docs/current/transaction-iso.html) | Commit authoritative versions and access changes. | Choose isolation and retry behavior per invariant. |
| ![opentelemetry logo](/learning/scale-design/logo-opentelemetry.svg) | [OpenTelemetry traces](https://opentelemetry.io/docs/concepts/signals/traces/) | Follow a write and subsequent read across data paths. | Correlate with version IDs, not document contents. |
| ![redis logo](/learning/scale-design/logo-redis.svg) | [Redis](https://redis.io/docs/latest/develop/use-cases/cache-aside/) | Serve data explicitly allowed to be stale. | Write down TTL, invalidation, and fallback behavior. |

A concrete HTTP contract is `PATCH /documents/42` with `If-Match: "v7"`. On a successful conditional update, return `ETag: "v8"`; on a stale precondition, return `412 Precondition Failed` and let the authorized client fetch the current version. The editor's next read must route to the primary or a replica known to have reached v8. [HTTP `If-Match`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Match) is a useful protocol tool, but the database conditional write remains the enforcement point. During a partition, do not confirm an edit that the authoritative write path could not commit.

## Engineering exercise

Classify three actions: the editor's immediate read after save, a public count of document views, and granting a collaborator access. For each, state whether a stale response is acceptable, for how long, and what happens during a partition.

## Design review questions

- Does “eventual” specify an upper bound on staleness?
- Why is CAP about the behavior during a partition?
- What is safer than client wall-clock timestamps for edit ordering?

**Review criteria:** no; partitions force a response-or-consistency decision for distributed operations; a server-controlled version or transactional compare-and-swap gives a clear order.

## Read further

- [Gilbert and Lynch: Brewer's conjecture and feasibility of consistent, available, partition-tolerant web services](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf)
- [Jepsen: consistency models](https://jepsen.io/consistency/models)
- [PostgreSQL: transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
