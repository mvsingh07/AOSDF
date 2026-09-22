---
concepts: [relational-database, nosql-database]
concept_category: Data Modeling
difficulty: fundamental
prerequisites: []
interview_angle: >
  Be ready to justify a choice by the actual access pattern and consistency need of the data — not
  by "NoSQL scales better," which is an oversimplification that doesn't survive a follow-up question.
built_at: L6-T1
diagram: false
---

# Relational vs. NoSQL Databases

## Definition

- **Relational (SQL):** data in tables with fixed schemas, related via foreign keys, queried with SQL.
  Strong consistency guarantees (see `study_material/backend/acid-transactions.md`), mature tooling, and
  the right default when data has clear relationships and you need to query across them flexibly.
- **NoSQL** — several distinct families, not one thing:
  - **Document stores** (MongoDB): flexible, schema-less JSON-like documents — good when each record's
    shape varies or nests naturally.
  - **Key-value stores** (Redis, DynamoDB): extremely fast lookups by key — good for caching, sessions.
  - **Wide-column stores** (Cassandra): optimized for massive write throughput across many nodes.
  - **Graph databases** (Neo4j): optimized for traversing relationships (social graphs, recommendation
    engines) — the one case where relational joins genuinely get slow at scale.

## Example

A relational schema for orders (clear, stable relationships):

```sql
CREATE TABLE orders (id INT PRIMARY KEY, user_id INT REFERENCES users(id), total DECIMAL);
CREATE TABLE order_items (order_id INT REFERENCES orders(id), product_id INT, qty INT);
```

A document store for a product catalog where each product has wildly different attributes (a laptop has
a CPU spec, a t-shirt has a size/color — no clean shared schema):

```json
{ "type": "laptop", "cpu": "M3", "ram_gb": 16 }
{ "type": "t-shirt", "size": "M", "color": "navy" }
```

## The Real Decision Criterion

The question isn't "which is faster" in the abstract — it's whether the data's shape is stable and
relationships need flexible querying (relational wins) or the shape varies per record and access is
mostly by a known key (NoSQL wins). Most products default to relational and add a specialized NoSQL store
(commonly Redis for caching) alongside it, rather than choosing one exclusively.
