# Replication, partitioning, and sharding

A **replica** copies changes from a primary database, often to serve reads or aid recovery. A **partition** divides one logical table into pieces. **Sharding** distributes data across independent database servers. They solve different constraints and introduce different failure modes.

## Add a replica only with a staleness contract

Suppose the document listing is read-heavy. A read replica may absorb listing queries, but asynchronous replication can lag. An editor saves version 8 to the primary and immediately reads a replica still at version 7. That is not merely a performance issue; the UI may claim the save failed. Route the editor's immediate read to the primary, track a session version, or wait until the replica has caught up. Define how much staleness a general reader may see. Monitor replay lag and failover behavior, not just replica CPU. A replica does not remove write pressure from the primary.

## Split data deliberately

PostgreSQL table partitioning may help a very large `document_events` table when queries and retention align with a partition key such as month. It is still one logical database system. Sharding might place tenants on different database clusters when one primary cannot handle total write/storage load. Choose a stable routing key, keep operations that need one transaction together, and plan cross-shard searches and migrations. A large tenant can become a **hot shard** even when average shard load is low; detect skew and plan for tenant moves or finer subdivision.

| Technique | Helps with | New cost |
| --- | --- | --- |
| Read replica | Read capacity, recovery options | Lag and failover complexity |
| Table partitioning | Large-table maintenance and pruning | Partition key and query discipline |
| Sharding | Write/storage limits of one cluster | Routing, rebalance, cross-shard work |

## Diagram: copies versus splits

![A primary asynchronously feeds a read replica, while two shards hold different tenant groups rather than full copies.](/learning/scale-design/replication.svg)

```aosdf-diagram
PRIMARY ──async copy──▶ REPLICA (same logical data, potentially stale)
SHARD A: tenants 1–50    SHARD B: tenants 51–100 (different data)
```

## Implementation: distinguish native replication from distribution

PostgreSQL streaming replication supplies an asynchronous read copy. Native table partitioning divides a table inside a PostgreSQL deployment. Citus is a PostgreSQL extension for distributed tables; it is a possible sharding path when tenant-local queries dominate. Start from the actual write, storage, and read bottleneck before introducing one of these.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![postgresql logo](/learning/scale-design/logo-postgresql.svg) | [PostgreSQL replication](https://www.postgresql.org/docs/current/warm-standby.html) | Serve tolerated-stale reads or prepare a failover path. | Measure replay lag and read-after-write behavior. |
| ![postgresql logo](/learning/scale-design/logo-postgresql.svg) | [PostgreSQL partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html) | Prune old event-table partitions by time. | Queries must filter on the partition key to benefit. |
| ![prometheus logo](/learning/scale-design/logo-prometheus.svg) | [Prometheus](https://prometheus.io/docs/introduction/overview/) | Alert on lag, primary write pressure, and hot tenants. | Compare distributions per shard; averages hide skew. |

A Citus-style tenant-sharded table uses `tenant_id` as the distribution key so a document and its access rows can be colocated; see the [Citus data-modeling guidance](https://github.com/citusdata/citus_docs/blob/master/sharding/data_modeling.rst). That requires changing keys, joins, and migration paths. It is not a transparent speed switch. Before a replica rollout, test `save v8 → immediate read`; before sharding, test a cross-tenant admin query and movement of a hot tenant.

## Engineering exercise

A user saves a document, then opens the listing and sees the old title. Draw the write and read paths that caused this. Choose one fix and state the cost. Then decide whether a 500-million-row event table needs partitioning, sharding, both, or more evidence.

## Design review questions

- Can a read replica make the primary's writes faster by itself?
- What is a hot shard?
- Why is sharding harder for a query across all tenants?

**Review criteria:** no, it primarily offloads reads; one shard receives disproportionate traffic; the query must coordinate results across servers.

## Read further

- [PostgreSQL: warm standby and streaming replication](https://www.postgresql.org/docs/current/warm-standby.html)
- [PostgreSQL: table partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [Azure Architecture Center: sharding pattern](https://learn.microsoft.com/azure/architecture/patterns/sharding)
