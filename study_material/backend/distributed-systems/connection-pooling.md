---
concepts: [connection-pooling]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: []
interview_angle: >
  Be ready to explain why opening a fresh TCP+auth connection per request is expensive (handshake,
  TLS negotiation, DB auth), and what happens when a pool is exhausted under load.
built_at: L6-T1
diagram: false
---

# Database Connection Pooling

## Definition

Establishing a database connection is expensive (TCP handshake, TLS negotiation, authentication) — doing
it fresh for every request would dominate request latency. A **connection pool** keeps a set of already-
open connections ready to reuse: a request borrows one, uses it, and returns it to the pool instead of
closing it. Pool size is a real tuning knob — too small and requests queue waiting for a free connection
under load; too large and the database server itself gets overwhelmed by more concurrent connections than
it can efficiently handle (each connection has server-side memory/CPU overhead too).

## Example

```python
# Without pooling — a new connection (and its full handshake cost) on every single request
def get_user(id):
    conn = psycopg2.connect(DATABASE_URL)  # expensive, every call
    ...
    conn.close()

# With pooling — connections are reused across requests
pool = ConnectionPool(DATABASE_URL, min_size=5, max_size=20)
def get_user(id):
    with pool.connection() as conn:  # borrows an existing connection, returns it after
        ...
```

## Why It Bites in Practice

A common real incident shape: a service scales out to more instances, and each instance's own connection
pool is sized generously — multiplied across instances, the database ends up with far more concurrent
connections than it can handle, and it's the *pool sizing*, not the query logic, that causes the outage.
This is also why serverless/lambda-style compute (many short-lived instances, each with its own pool)
often needs an external pooler (e.g. PgBouncer) sitting between the application and the database.
