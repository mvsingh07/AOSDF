# Queries, indexes, and connections

A database can be the limiting resource long before the API reaches CPU capacity. Faster queries, fewer round trips, and a bounded connection budget usually come before moving data to another database.

## Follow the query plan

Suppose the library lists documents for one tenant, newest first. This query needs to filter and order efficiently:

```sql
SELECT id, title, updated_at
FROM documents
WHERE tenant_id = $1 AND deleted_at IS NULL
ORDER BY updated_at DESC
LIMIT 30;
```

A possible PostgreSQL index is `CREATE INDEX ... ON documents (tenant_id, updated_at DESC) WHERE deleted_at IS NULL`. Check `EXPLAIN (ANALYZE, BUFFERS)` against realistic data before assuming the index helps. It costs storage and write time, and a planner may choose a scan for a tiny table or broad filter. Query shape, selectivity, sort order, and pagination all matter. For deep pages, keyset pagination using `(updated_at, id)` avoids the cost and unstable results of large offsets.

An **N+1 query** appears when one list query returns 30 documents and application code makes one author or permission query for each row: 31 round trips. Fetch related data in a join or bounded batch, while retaining access filters. Instrument query count per request so the regression is visible.

## Budget connections, not only CPUs

Each database connection consumes server resources. If 20 API instances each allow 30 active connections, the fleet can open 600 connections before workers, migrations, and operators. A pool reuses connections and queues callers when all are busy. Set a per-instance pool cap from the database's safe total, reserve headroom for maintenance, and watch pool wait time. A larger pool can reduce waiting at the API while increasing database contention and p99 latency. Long transactions hold connections and locks; make them short.

## Diagram: a bounded data path

![A batched list query uses an index and a bounded connection pool; an N plus one path fans out into many unnecessary database calls.](/learning/scale-design/queries.svg)

```aosdf-diagram
API list request ──▶ connection pool ──▶ indexed list query ──▶ 30 rows
                                    bad path: 1 list + 30 related queries
```

## Implementation: inspect the database before enlarging it

PostgreSQL provides indexes, `EXPLAIN`, and transaction diagnostics. SQLAlchemy is one Python ORM that can batch related rows with `selectinload()` instead of issuing one lazy query per document. PgBouncer can bound physical server connections when many API processes use short transactions. OpenTelemetry traces and Grafana dashboards help distinguish time spent waiting for a pool slot from time spent executing SQL.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![postgresql logo](/learning/scale-design/logo-postgresql.svg) | [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) | Compare scan and sort plans on production-like data. | Measure buffers and execution, not just estimated cost. |
| ![sqlalchemy logo](/learning/scale-design/logo-sqlalchemy.svg) | [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html) | Use `selectinload()` or a suitable join to avoid N+1 relationship queries. | Count generated SQL and check row multiplication on joins. |
| ![opentelemetry logo](/learning/scale-design/logo-opentelemetry.svg) | [OpenTelemetry](https://opentelemetry.io/docs/concepts/) | Separate pool wait, query, and serialization spans. | Sanitize SQL parameters and document identifiers. |
| ![grafana logo](/learning/scale-design/logo-grafana.svg) | [Grafana](https://grafana.com/docs/grafana/latest/) | Compare p99, active connections, and pool wait. | Set alerts on user impact, not only server CPU. |

For a Python service using SQLAlchemy, `select(Document).options(selectinload(Document.owner))` loads related owners in a bounded follow-up query rather than one query per document. The `Document` mapping must define that relationship. Record the actual SQL count for a page of 30 rows and compare both strategies; eager loading a large collection can move the bottleneck to memory or network transfer.

For the list query above, a candidate PostgreSQL index is:

```sql
CREATE INDEX CONCURRENTLY documents_tenant_recent_idx
ON documents (tenant_id, updated_at DESC)
WHERE deleted_at IS NULL;
```

Run `EXPLAIN (ANALYZE, BUFFERS)` before and after on representative data. `CONCURRENTLY` reduces blocking of writes but takes longer and has operational constraints. If using [PgBouncer](https://www.pgbouncer.org/config), choose `pool_mode` deliberately: transaction pooling can break features that expect session state. Track **server** connections as well as client connections; a pool is not unlimited database capacity.

## Engineering exercise

Given 16 API instances and a database budget of 240 application connections, reserve 48 for workers and admin tasks. Set an initial maximum API pool per instance and show the arithmetic. Then explain how you would detect a slow query versus pool exhaustion.

## Design review questions

- Does adding an index always speed up every query?
- Why can a connection pool be full when CPU is low?
- What is the N+1 cost for a page of 30 rows?

**Review criteria:** indexes have maintenance cost and fit specific filters and sorts; slow I/O or long transactions can occupy connections; one initial query plus 30 related queries creates 31 round trips.

## Read further

- [PostgreSQL: using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
- [PostgreSQL: CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html)
- [PostgreSQL: resource consumption and connections](https://www.postgresql.org/docs/current/runtime-config-resource.html)
