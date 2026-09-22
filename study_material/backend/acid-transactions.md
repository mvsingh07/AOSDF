---
concepts: [acid-properties, database-transactions]
concept_category: Data Modeling
difficulty: intermediate
prerequisites: [relational-database]
interview_angle: >
  Have one concrete failure example ready for each letter — especially Isolation, since "what
  happens with two concurrent transactions" is the question that actually separates a memorized
  answer from real understanding.
built_at: L6-T1
diagram: false
---

# ACID Properties & Transactions

## Definition

A **transaction** groups multiple database operations so they succeed or fail as one unit. **ACID** is
the guarantee a transactional database makes about that unit:

- **Atomicity:** all operations in the transaction happen, or none do — no partial writes.
- **Consistency:** a transaction moves the database from one valid state to another, never violating
  defined constraints (foreign keys, uniqueness).
- **Isolation:** concurrent transactions don't see each other's uncommitted intermediate state —
  governed by isolation levels (Read Committed, Repeatable Read, Serializable), each trading strictness
  for performance.
- **Durability:** once committed, a transaction's changes survive a crash immediately after.

## Example

A bank transfer — the canonical Atomicity example:

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

Without atomicity, a crash between the two `UPDATE`s would destroy $100 — it left one account, never
arrived at the other. Atomicity guarantees either both happen or neither does.

An Isolation failure without proper isolation level: two concurrent transactions both read a product's
stock as 5, both decide there's enough for their order of 3, and both commit — stock is now -1, because
neither saw the other's in-flight change.

## Why This Still Matters With NoSQL Around

Most NoSQL stores relax one or more of these guarantees deliberately (often Consistency, per the CAP
theorem — a distributed system can't have full Consistency and Availability during a network Partition)
in exchange for scale. Knowing which guarantee a given data store relaxed, and why that's an acceptable
trade for that specific data, is the actual skill being tested.
