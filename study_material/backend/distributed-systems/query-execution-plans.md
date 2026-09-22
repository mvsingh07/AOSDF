---
concepts: [query-execution-plan]
concept_category: Data Modeling
difficulty: intermediate
prerequisites: [database-indexing]
interview_angle: >
  Be ready to walk through reading an actual EXPLAIN output — naming a sequential scan vs. an index
  scan and explaining why the planner chose one over the other for a given query.
built_at: L6-T1
diagram: false
---

# Database Indexes & Query Execution Plans

## Definition

Before running a query, the database's **query planner** decides *how* to execute it — which indexes (if
any) to use, in what order to join tables, whether to scan a full table or seek via an index — and
produces an **execution plan**. `EXPLAIN` (and `EXPLAIN ANALYZE`, which actually runs the query and
reports real timings) shows that plan, which is the primary tool for diagnosing why a query is slow.

## Example

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42;

-- Without an index on user_id:
Seq Scan on orders (cost=0.00..18334.00 rows=12 width=64) (actual time=0.02..142.5 rows=12)
  Filter: (user_id = 42)
-- reads every single row in the table, discarding non-matches — cost scales with table size

-- With an index on user_id:
Index Scan using idx_orders_user_id on orders (cost=0.29..8.31 rows=12 width=64) (actual time=0.01..0.02 rows=12)
  Index Cond: (user_id = 42)
-- jumps directly to matching rows via the index's sorted structure — cost barely grows with table size
```

## Why the Planner Sometimes Ignores an Index

An index existing doesn't guarantee it's used — if a table is small, or a query matches a large fraction
of the table's rows anyway, a full sequential scan can genuinely be cheaper than the overhead of an index
lookup. This is why "add an index" doesn't always fix a slow query, and why checking the actual plan (not
assuming) is the correct first diagnostic step, the same "verify, don't assume" discipline that applies
to any performance claim.
