# Concurrency, locks, and runtime health

**Concurrency** means work overlaps in time. The difficult case is not just many readers; it is two editors changing the same document or two processes claiming the same maintenance job. A **race condition** exists when the outcome depends on timing that the design has not controlled.

## Protect simultaneous edits

Both editors read version 7. Alice saves first; Bob saves afterward. A blind `UPDATE` loses Alice's edit. With **optimistic concurrency**, Bob submits the version he read:

```sql
UPDATE documents
SET title = $new_title, version = version + 1
WHERE id = $id AND version = 7;
```

If the affected-row count is zero, return a conflict and show the current version; do not silently overwrite. This fits conflicts that are relatively rare. **Pessimistic locking** reserves the row while a short transaction computes a change, useful when conflicts are common or a multi-step invariant needs protection. Keep lock order consistent and transactions short to reduce **deadlocks**; on deadlock or serialization failure, retry the *whole* transaction only when the operation is safe to retry.

A distributed lock coordinates processes, but a lock lease can expire while a paused holder is still working. For a critical effect, use a fencing token or a storage-level conditional write so an old holder cannot act after a new leader. Leader election identifies one coordinator; it does not magically make its effects exactly once.

## Keep the process healthy too

**Thread safety** means shared in-memory state behaves correctly under concurrent execution. Avoid mutable global request state; protect shared structures or keep state local. A **memory leak** is memory that remains reachable but is no longer useful, such as unbounded in-memory document caches or event listeners never removed. Garbage collection reclaims unreachable objects, not objects a mistaken cache still references. Watch heap growth, GC pause time, allocation rate, and p99 latency under sustained load; restart policies only hide a leak temporarily.

## Diagram: compare a version before saving

![Two editors read version seven; Alice's conditional update creates version eight and Bob's stale update is rejected with a conflict.](/learning/scale-design/concurrency.svg)

```aosdf-diagram
Alice reads v7 ── conditional save ──▶ v8 success
Bob reads v7   ── conditional save ──▶ 0 rows → conflict, reload v8
```

## Implementation: enforce ownership where the effect occurs

PostgreSQL row versions and locks guard document invariants. Redis can coordinate an advisory lease for a background coordinator, but an expired lease holder may still run. Prometheus process metrics make memory growth and pause time visible before p99 degrades.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![postgresql logo](/learning/scale-design/logo-postgresql.svg) | [PostgreSQL locking](https://www.postgresql.org/docs/current/explicit-locking.html) | Apply row-level or optimistic concurrency to edits. | Keep transactions short and handle deadlock retries. |
| ![redis logo](/learning/scale-design/logo-redis.svg) | [Redis distributed locks](https://redis.io/docs/latest/develop/use/patterns/distributed-locks/) | Coordinate best-effort exclusive work across processes. | Use fencing or a storage-level condition for critical effects. |
| ![prometheus logo](/learning/scale-design/logo-prometheus.svg) | [Prometheus](https://prometheus.io/docs/introduction/overview/) | Observe heap, GC pauses, conflicts, and deadlocks. | Relate runtime metrics to request p99. |

Use the SQL conditional `UPDATE ... WHERE id = $id AND version = $expected` from this lesson as the final authority for edits; check `row_count === 1`. If a Redis lease protects a scheduled cleanup job, include a monotonically increasing fencing token in writes to the downstream store or make the write conditional there. A lock key alone cannot prevent a paused old holder from resuming. Set a bounded in-process cache size and test steady-state heap after repeated document reads; a garbage collector cannot reclaim still-referenced entries.

## Engineering exercise

Write the response to Bob after his version-7 update conflicts. Then describe a job coordinator whose lock expires mid-task; explain how a fencing token would prevent its old write. Name one metric that would reveal a leaking application cache.

## Design review questions

- Why does a mutex in one API instance not protect a document across the fleet?
- Why can a stale lock holder still be dangerous?
- Why does a garbage collector not fix an unbounded cache?

**Review criteria:** other instances have separate memory; a paused holder may resume after its lease expires; cached objects remain reachable and therefore are not collectible.

## Read further

- [PostgreSQL: transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [PostgreSQL: explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- [Oracle Java: troubleshooting memory leaks](https://docs.oracle.com/en/java/javase/27/troubleshoot/troubleshooting-memory-leaks.html)
