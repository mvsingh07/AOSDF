---
concepts: [change-data-capture]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [write-ahead-log]
interview_angle: >
  Be ready to contrast CDC with "just poll the table for changes every N seconds" — name the two
  concrete problems polling has (missed deletes, load on the source table) that CDC avoids.
built_at: L6-T1
diagram: true
---

# Change Data Capture (CDC)

## Definition

**Change Data Capture** streams every insert/update/delete a database makes, as it happens, to
downstream consumers — typically by tailing the database's own **write-ahead log**
(`write-ahead-log.md`) rather than querying tables directly. Common uses: keeping a search index (e.g.
Elasticsearch) in sync with a primary database, feeding a data warehouse, or propagating changes into a
cache or a different service's own database, without that service polling or being directly coupled to
the source database's schema.

## Example

```
Primary DB (Postgres) ──WAL stream──▶ Debezium (CDC tool) ──▶ Kafka topic ──▶ consumers:
                                                                  ├─▶ Elasticsearch indexer
                                                                  ├─▶ Data warehouse loader
                                                                  └─▶ Cache invalidator
```

Compare to polling — `SELECT * FROM orders WHERE updated_at > last_poll_time` — which misses **deletes**
entirely (a deleted row just isn't there to select), adds recurring load to the source table, and has an
inherent delay equal to the poll interval. CDC captures every change, including deletes, with near-real-
time latency and no repeated query load on the source table.

## Diagram

```aosdf-diagram
┌──────────┐  WAL tail   ┌──────────┐  publish   ┌───────────┐
│ Primary DB│────────────▶│ CDC Tool  │───────────▶│  Kafka     │──▶ multiple independent consumers
└──────────┘             └──────────┘            └───────────┘
```

## Where This Connects

This is the mechanism behind the **outbox pattern**'s reliability guarantee
(`reliable-messaging-patterns.md`) — CDC can tail an outbox table's WAL instead of a separate publisher
process polling it, closing the gap between "committed to the database" and "published to the event log."
