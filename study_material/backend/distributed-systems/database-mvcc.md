---
concepts: [mvcc]
concept_category: Data Modeling
difficulty: advanced
prerequisites: [acid-properties, database-transactions]
interview_angle: >
  Be ready to explain how MVCC lets readers never block writers (and vice versa) — the mechanism,
  not just the name — and why that's *not* the same thing as full Serializable isolation.
built_at: L6-T1
diagram: false
---

# MVCC (Multi-Version Concurrency Control)

## Definition

Instead of locking a row for reads while a write is in progress, MVCC keeps multiple **versions** of a
row simultaneously — a write creates a new version rather than overwriting the old one in place, and each
transaction sees a consistent **snapshot** of the data as it existed when that transaction (or statement)
started. This is how PostgreSQL, MySQL/InnoDB, and most modern relational databases achieve high
concurrency: a long-running read never blocks a concurrent write, and vice versa, because they're
literally looking at different row versions.

## Example

```
Transaction A (started at T1): reads product.price = 10   -- sees the version live at T1
Transaction B (started at T2, T2 > T1): updates product.price = 12, commits
Transaction A: reads product.price again -- still sees 10, its own snapshot from T1,
               even though B has already committed a newer version
```

Old row versions aren't kept forever — a background process (PostgreSQL's `VACUUM`) reclaims versions no
longer visible to any active transaction.

## The Trade-off

MVCC buys read/write concurrency without locking, but it doesn't eliminate all anomalies by itself — two
concurrent writers can still both read the old version and both attempt to write, producing a **write
skew** anomaly at weaker isolation levels (see `study_material/backend/distributed-systems/isolation-levels.md`).
MVCC is the *mechanism*; the isolation level is the *guarantee* built on top of it — they're related but
distinct concepts, a common point of confusion.
