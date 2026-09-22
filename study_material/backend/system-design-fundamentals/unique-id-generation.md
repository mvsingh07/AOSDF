---
concepts: [snowflake-id, distributed-id-generation]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: [clock-skew]
interview_angle: >
  Be ready to explain why auto-increment breaks the moment a table is sharded (`sharding-and-
  rebalancing.md`) — no single database owns "the next number" anymore — and why Snowflake's design
  embeds a timestamp specifically so IDs stay roughly sortable by creation time.
built_at: L6-T1
diagram: true
---

# Distributed Unique ID Generation

## Definition

A single database's auto-increment column can't generate globally unique IDs once that table is sharded
across multiple databases (`sharding-and-rebalancing.md`) — each shard would independently produce
colliding IDs (both shards eventually emit `id=1`, `id=2`, ...). Two common approaches:

- **UUID (v4):** 128-bit random identifier, generated locally with no coordination needed — simple and
  always unique, but random UUIDs are not sortable by creation time and are larger than a 64-bit integer
  (worse index locality in the database).
- **Snowflake ID (Twitter's design):** a 64-bit integer composed of a timestamp (most significant bits), a
  machine/worker ID, and a per-machine sequence number. Roughly sortable by creation time (since the
  timestamp is the leading bits), globally unique without any coordination between machines, and fits in a
  standard 64-bit integer column — at the cost of depending on each machine's clock being reasonably
  correct (`distributed-time.md`'s clock skew is the real risk here: if a machine's clock jumps backward,
  it can generate an ID that collides with or sorts before an ID it already issued).

## Example

```
Snowflake layout (64 bits):
 1 bit unused | 41 bits timestamp (ms since epoch) | 10 bits machine ID | 12 bits sequence
```

```python
def next_id(machine_id, sequence, last_timestamp):
    now = current_millis()
    if now == last_timestamp:
        sequence = (sequence + 1) & 0xFFF   # 12-bit sequence, same millisecond
    else:
        sequence = 0
    return (now << 22) | (machine_id << 12) | sequence
```

## Diagram

```aosdf-diagram
┌─ 41 bits: timestamp ─┐┌ 10 bits: machine ID ┐┌ 12 bits: sequence ┐
│ roughly sortable      ││ which node issued it ││ order within 1ms  │
└───────────────────────┘└──────────────────────┘└────────────────────┘
                              64-bit Snowflake ID — no coordination needed between machines
```
