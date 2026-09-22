---
concepts: [database-replication, replication-lag]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [acid-properties]
interview_angle: >
  Be ready to explain the synchronous-vs-asynchronous replication trade-off precisely: synchronous
  costs write latency (waiting for a replica to confirm) in exchange for zero data loss on
  failover; asynchronous is fast but can lose the last few writes if the primary fails before
  replicating them.
built_at: L6-T1
diagram: true
---

# Database Replication & Consistency

## Definition

**Replication** keeps copies of the same data on multiple database nodes — for availability (a replica
can take over if the primary fails) and read scaling (reads can be served from replicas, spreading load).

- **Leader-follower (primary-replica) replication:** all writes go to one primary; it streams its changes
  (often via its own WAL, `write-ahead-log.md`) to one or more read replicas.
- **Synchronous replication:** the primary waits for at least one replica to confirm it received the
  write before acknowledging the write as committed — zero data loss if the primary then fails, at the
  cost of added write latency (and reduced availability if that replica is unreachable).
- **Asynchronous replication:** the primary acknowledges the write immediately, without waiting for
  replicas — fast writes, but if the primary fails before a replica caught up, those last few writes are
  lost on failover.
- **Replication lag:** how far behind a replica is from the primary, in either time or number of
  un-applied writes — the direct cause of the read-your-writes problem (`consistency-models.md`) when
  reads are served from a lagging replica.

## Example

```
Synchronous:  Client write ──▶ Primary ──▶ waits for Replica ack ──▶ Primary confirms to client
              (write latency includes a network round-trip to the replica)

Asynchronous: Client write ──▶ Primary confirms immediately ──▶ (later) streams to Replica
              (if Primary crashes here, before streaming, this write is lost on failover)
```

## Diagram

```aosdf-diagram
┌─────────┐  writes   ┌──────────┐   stream changes   ┌───────────┐
│  Client  │──────────▶│ Primary  │───────────────────▶│ Replica(s) │
└─────────┘           └──────────┘                    └───────────┘
                             ▲                                │
                             └──────── reads (may be stale) ──┘
```

## The Real Decision

Most systems use asynchronous replication for read replicas (read scaling doesn't need zero data loss
guarantees) but synchronous replication specifically for failover-critical copies where losing the last
few writes on a primary failure would be unacceptable — the two modes are often combined in the same
deployment for different replicas, not a single global choice.
