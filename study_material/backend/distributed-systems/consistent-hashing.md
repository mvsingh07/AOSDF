---
concepts: [consistent-hashing]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [sharding]
interview_angle: >
  Be ready to explain, precisely, how many keys remap when a node is added or removed under
  consistent hashing (roughly 1/N of them) versus naive modulo hashing (nearly all of them).
built_at: L6-T1
diagram: true
---

# Consistent Hashing

## Definition

Naive sharding with `hash(key) % N` has a serious rebalancing problem: changing `N` (adding or removing a
node) changes the modulo result for almost every key, forcing a near-total data reshuffle. **Consistent
hashing** solves this by placing both nodes and keys on a conceptual ring (hash space 0 to 2^32-1, say): a
key belongs to the first node found walking clockwise from the key's hash position. Adding or removing one
node only affects the keys between it and its neighbor on the ring — roughly `1/N` of all keys, not
nearly all of them.

## Example

```
Ring positions (simplified):     Node A: 10    Node B: 90    Node C: 200
Key "user:42" hashes to 45  →  first node clockwise from 45 is Node B (90)

Remove Node B: only keys between A (10) and B's old position (90) need to move — to Node C,
the next node clockwise. Keys already mapped to A or C are completely unaffected.
```

In practice, each physical node is placed on the ring multiple times (**virtual nodes**) to avoid uneven
load distribution that a small number of ring positions would otherwise produce.

## Diagram

```aosdf-diagram
                    Node A (10)
                   ╱
          ring →  ●───────────●  Node B (90)
                   ╲         ╱
                    ●───────●
                  Node C (200)
   key hash=45 walks clockwise from 45 → lands on Node B (next node found)
```

## Why This Matters

This is the mechanism that makes `sharding-and-rebalancing.md`'s rebalancing cheap instead of a full data
migration — Redis Cluster, DynamoDB, Cassandra, and most distributed caches/databases use a variant of
this specifically to avoid the "add one node, reshuffle everything" problem naive modulo sharding has.
