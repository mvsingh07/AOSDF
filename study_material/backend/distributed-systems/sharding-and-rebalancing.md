---
concepts: [sharding, hot-partition, partition-rebalancing]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [relational-database]
interview_angle: >
  Be ready to give a concrete example of a hot partition (a bad shard key choice, like sharding by
  signup date when most traffic is for recent users) and explain what rebalancing has to move to fix it.
built_at: L6-T1
diagram: true
---

# Sharding, Hot Partitions & Rebalancing

## Definition

- **Sharding (horizontal partitioning):** splitting one large dataset across multiple database instances
  by a **shard key** (e.g. `user_id % N`), so no single machine holds all the data or takes all the
  traffic.
- **Hot partition:** a shard key choice that sends disproportionate traffic or data to one shard — e.g.
  sharding a social app by signup date puts every currently-active user's data (usually the newest
  accounts) on the same shard, while old shards sit nearly idle.
- **Partition rebalancing:** redistributing data across shards — either to add new shards as data grows,
  or to fix a hot partition — moving a subset of keys from an overloaded shard to underused ones without
  taking the system offline.

## Example

```
Bad shard key: user_id % 4  →  users 1,5,9,13... always land on shard 1
                                if user_id is assigned sequentially and recent users are most active,
                                shard 1 (lowest IDs) or the highest shard (newest, most active users)
                                becomes a hot partition depending on the access pattern

Better: hash(user_id) % 4  →  spreads users pseudo-randomly and evenly across shards,
                               independent of ID ordering or signup recency
```

Rebalancing without consistent hashing (see `consistent-hashing.md`) means changing `N` in `key % N`
remaps *almost every* key to a different shard — consistent hashing exists specifically to make
rebalancing move only a small fraction of keys instead.

## Diagram

```aosdf-diagram
Hot partition:                          After rebalancing:
Shard 1: ██████████ (overloaded)        Shard 1: ████
Shard 2: ██                             Shard 2: █████
Shard 3: █                              Shard 3: █████
Shard 4: █                              Shard 4: █████
```

## Why the Shard Key Choice Is the Real Decision

Almost every hot-partition incident traces back to the shard key, chosen early, before the real traffic
pattern was known — this is why hashing a key (spreading load pseudo-randomly) is usually safer than
sharding by a naturally-ordered or naturally-skewed field (date, sequential ID, a single tenant's ID in a
multi-tenant system with one dominant customer).
