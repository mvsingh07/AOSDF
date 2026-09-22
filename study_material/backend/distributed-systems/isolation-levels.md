---
concepts: [isolation-levels, dirty-read, phantom-read]
concept_category: Data Modeling
difficulty: advanced
prerequisites: [acid-properties, mvcc]
interview_angle: >
  Be ready to define dirty read, non-repeatable read, and phantom read precisely, and to say which
  standard isolation level first prevents each one — this table gets asked directly, often.
built_at: L6-T1
diagram: false
---

# Transaction Isolation Levels

## Definition

The SQL standard defines four isolation levels, each preventing progressively more of three
concurrency anomalies:

| Anomaly | Definition |
| --- | --- |
| Dirty read | reading another transaction's **uncommitted** change — which might later roll back |
| Non-repeatable read | reading the same row twice in one transaction and getting different values, because another transaction committed a change in between |
| Phantom read | re-running the same *range* query twice in one transaction and getting a different *set of rows*, because another transaction inserted/deleted a matching row in between |

| Isolation Level | Prevents Dirty Read | Prevents Non-Repeatable Read | Prevents Phantom Read |
| --- | --- | --- | --- |
| Read Uncommitted | No | No | No |
| Read Committed | Yes | No | No |
| Repeatable Read | Yes | Yes | No (mostly — implementation-dependent) |
| Serializable | Yes | Yes | Yes |

## Example

Non-repeatable read at Read Committed:

```
Tx A: SELECT balance FROM accounts WHERE id=1;   -- reads 100
Tx B: UPDATE accounts SET balance=50 WHERE id=1; COMMIT;
Tx A: SELECT balance FROM accounts WHERE id=1;   -- reads 50 — different value, same transaction
```

At Repeatable Read, Tx A's second read would still see 100 — its own snapshot, taken at the transaction's
start, doesn't reflect Tx B's later commit (this is MVCC, `database-mvcc.md`, providing the mechanism).

## The Real Trade-off

Higher isolation levels prevent more anomalies but cost more — Serializable typically means more lock
contention or more transaction aborts-and-retries under concurrent load. Most applications default to
Read Committed (Postgres's default) and only reach for Repeatable Read or Serializable for specific
operations where a detected anomaly would cause real business harm (e.g. double-booking a seat).
