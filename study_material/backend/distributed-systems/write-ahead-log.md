---
concepts: [write-ahead-log]
concept_category: Data Modeling
difficulty: advanced
prerequisites: [database-transactions]
interview_angle: >
  Be ready to explain how a WAL gives Durability and crash recovery specifically — what a database
  does on restart after a crash, using only the log.
built_at: L6-T1
diagram: false
---

# Write-Ahead Log (WAL)

## Definition

A database doesn't write every change directly and immediately to its main data files on disk — that
would mean scattered random writes for every transaction, which is slow. Instead, it first appends a
compact, sequential record of the change to a **write-ahead log** (a simple append-only file), and only
*then* applies the change to the actual data files, often later and in batches. A transaction is
considered durable (Durability, from ACID) the moment its record is safely on the WAL — even if the
database crashes before the change is applied to the main data files, it can replay the WAL on restart to
recover.

## Example

```
Transaction commits: UPDATE accounts SET balance = 90 WHERE id = 1
1. Append to WAL (sequential, fast): "tx=501, table=accounts, id=1, balance=90"  ← durable now
2. Return "commit successful" to the client
3. (later, possibly batched) apply the change to the actual accounts table on disk

If the database crashes between steps 2 and 3: on restart, it replays the WAL from the last
checkpoint — finds tx=501's record, and re-applies it. No committed data is lost.
```

## Why Sequential Matters

Appending to a WAL is a sequential write (fast, no disk seeking), while applying changes to the actual
data files (scattered across many pages/tables) is comparatively slow, random I/O. Separating "make it
durable" (fast, sequential WAL append) from "make it queryable" (slower, applied later) is the core
performance trick — it's also exactly the mechanism **change data capture** (see
`change-data-capture.md`) taps into: reading the WAL is a cheap way to observe every change a database
makes, without querying the tables directly.
