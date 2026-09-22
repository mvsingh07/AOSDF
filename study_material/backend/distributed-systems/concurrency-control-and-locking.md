---
concepts: [optimistic-locking, pessimistic-locking, distributed-lock]
concept_category: Concurrency
difficulty: advanced
prerequisites: [mvcc, database-transactions]
interview_angle: >
  Be ready to state the decision rule plainly: pessimistic locking when contention is expected and
  frequent, optimistic when conflicts are rare — and know the real risk a naive distributed lock has
  (a client pausing past its lock's TTL and resuming as if it still holds it).
built_at: L6-T1
diagram: false
---

# Optimistic vs. Pessimistic Concurrency Control & Distributed Locks

## Definition

- **Pessimistic locking:** acquire a lock on a row *before* reading/modifying it, blocking any other
  transaction that wants the same row until the lock is released. Correct and simple to reason about, but
  reduces concurrency — waiting transactions are blocked, and a slow holder delays everyone behind it.
- **Optimistic locking:** don't lock anything upfront — read the row along with a version number, do the
  work, then on write, check the version is still unchanged (`WHERE id = ? AND version = ?`); if another
  transaction updated it in the meantime, the write fails and the caller retries. Better throughput under
  low contention (most of the time, nothing conflicts); wasted retry work under high contention.
- **Distributed lock:** the same idea as a database row lock, but across separate processes/services with
  no shared database transaction to rely on — typically implemented with Redis (`SET key value NX PX
  30000`, an atomic "set if not exists, with a TTL"). The TTL matters: it prevents a crashed holder from
  locking a resource forever, at the cost of a real risk — if the holder pauses (a long GC pause, a slow
  network) past the TTL, another process can acquire the lock while the first still believes it holds it.

## Example

```python
# Optimistic locking
def update_price(product_id, new_price, expected_version):
    rows = db.execute(
        "UPDATE products SET price=%s, version=version+1 WHERE id=%s AND version=%s",
        (new_price, product_id, expected_version))
    if rows == 0:
        raise ConflictError("row changed since read — retry")

# Distributed lock (Redis) — TTL is the safety net against a crashed holder
acquired = redis.set(f"lock:order:{order_id}", worker_id, nx=True, px=30000)
if not acquired:
    raise LockHeldError()
```

## The Decision Rule

Use pessimistic locking when conflicts are frequent and a wasted retry is expensive (e.g. a seat
reservation system near sellout). Use optimistic locking when conflicts are rare and retries are cheap
(most CRUD update endpoints). For distributed locks specifically, prefer a system designed for it (a
proper consensus-backed lock service) over a hand-rolled Redis lock whenever the cost of two holders
briefly overlapping is genuinely severe — the TTL-expiry race above is a real, well-documented failure
mode, not a hypothetical one.
