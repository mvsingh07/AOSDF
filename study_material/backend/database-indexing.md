---
concepts: [database-indexing, query-optimization]
concept_category: Data Modeling
difficulty: intermediate
prerequisites: [relational-database]
interview_angle: >
  Be ready to explain why indexes aren't free — every index speeds up reads on that column but
  slows down every write (the index itself must be updated), and costs storage.
built_at: L6-T1
diagram: false
---

# Database Indexing & Query Optimization

## Definition

An **index** is a separate, sorted data structure (typically a B-tree) built over one or more columns,
letting the database find matching rows without scanning the entire table. Without an index, a query
filtering on a column requires a **full table scan** — checking every row.

## Example

```sql
-- Without an index on email: full table scan across every user row
SELECT * FROM users WHERE email = 'a@example.com';

-- Add the index once:
CREATE INDEX idx_users_email ON users(email);
-- Now the same query does a fast index lookup instead of a full scan
```

A composite index `(user_id, created_at)` speeds up queries filtering on `user_id` alone, or on both
columns together — but not a query filtering on `created_at` alone, since the index is ordered by
`user_id` first (leftmost-prefix rule).

## The Trade-off

Every index adds overhead to every `INSERT`/`UPDATE`/`DELETE` on that table (the index must be kept in
sync) and consumes storage — indexing every column "just in case" is a real anti-pattern, not a free
optimization. Use `EXPLAIN`/`EXPLAIN ANALYZE` to confirm a query is actually using an index (and which
one) before assuming an index fixed a slow query — a common mistake is adding an index that the query
planner doesn't actually choose to use.
