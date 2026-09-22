---
concepts: [horizontal-scaling, vertical-scaling]
concept_category: Distributed Systems
difficulty: fundamental
prerequisites: []
interview_angle: >
  Be ready to explain why teams reach for vertical scaling first (it's simpler — no distributed-systems
  problems to solve) and only move to horizontal scaling once a single machine's ceiling is hit or
  availability requires no single point of failure.
built_at: L6-T1
diagram: true
---

# Horizontal vs. Vertical Scaling

## Definition

- **Vertical scaling (scale up):** add more CPU/RAM/disk to a single existing machine. Simple — no code
  changes, no distributed coordination — but bounded by the biggest machine you can buy, and that one
  machine is a single point of failure.
- **Horizontal scaling (scale out):** add more machines and split the load across them. Effectively
  unbounded capacity and no single point of failure, but it's what actually creates the need for
  everything else in this corpus — load balancing, sharding, consistent hashing, distributed locks,
  replication — none of those problems exist on a single box.

## Example

A database under growing read load can first get a bigger instance (vertical) — cheap, immediate, zero
application changes. Once it outgrows the largest available instance, or a single-node failure can't be
tolerated, the next step is horizontal: read replicas (`database-replication.md`) or sharding
(`sharding-and-rebalancing.md`) — both of which introduce consistency and coordination problems that
didn't exist when it was one box.

## Diagram

```aosdf-diagram
Vertical:    [ small box ] ──▶ [ bigger box ] ──▶ [ biggest box available ]   (ceiling exists)

Horizontal:  [ box ] [ box ] [ box ] [ box ] ...                              (add more boxes, no ceiling,
                                                                                but now needs a load
                                                                                balancer + coordination)
```
