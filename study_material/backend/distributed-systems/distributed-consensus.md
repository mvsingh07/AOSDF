---
concepts: [split-brain, quorum, leader-election]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: []
interview_angle: >
  Be ready to explain *why* a quorum (majority) specifically prevents split-brain — walk through what
  happens with an even-numbered cluster split exactly in half, and why an odd number of nodes avoids
  that specific failure mode.
built_at: L6-T1
diagram: true
---

# Leader Election, Quorum & Split-Brain

## Definition

- **Leader election:** in a cluster where one node must coordinate writes (or make some other
  authoritative decision), nodes run a protocol (Raft, Paxos, ZooKeeper's ZAB) to agree on exactly one
  leader, and to detect and replace it if it fails.
- **Quorum:** a majority of nodes (e.g. 3 out of 5) must agree before a decision (a leader election, a
  write) is considered valid. Requiring a *majority*, not just "more than one," is what guarantees at
  most one side of any network split can ever reach quorum at the same time.
- **Split-brain:** a network partition divides a cluster into two groups, and **both** groups
  independently believe they're the legitimate leader/primary and keep accepting writes — producing two
  divergent, conflicting histories of the data that must later be reconciled (often manually, and often
  lossily).

## Example

A 5-node cluster splits into a group of 3 and a group of 2 due to a network partition. The group of 3 can
reach quorum (3 out of 5 is a majority) and safely elects a leader; the group of 2 cannot reach quorum, so
it correctly refuses to elect its own leader — this is exactly what prevents split-brain. An
**even-numbered** cluster (say, 4 nodes splitting 2-and-2) is the dangerous case: neither side can reach
majority on its own, which is actually *safer* against split-brain than it sounds (neither elects a
leader) but does mean the whole cluster becomes unavailable during the partition — the real reason
clusters are conventionally sized as odd numbers (3, 5, 7).

## Diagram

```aosdf-diagram
5-node cluster, network partition:
┌───┐ ┌───┐ ┌───┐        ┌───┐ ┌───┐
│ A │ │ B │ │ C │   ✂    │ D │ │ E │
└───┘ └───┘ └───┘        └───┘ └───┘
   3 nodes: reaches quorum   2 nodes: cannot reach quorum
   → safely elects a leader  → correctly refuses to elect one
```

## Where This Shows Up

This is the exact reasoning behind why this framework's own `study_material/principles/architecture-
styles.md` treats a single-owner monolith as the safer MVP default — leader election, quorum, and
split-brain are all real distributed-systems costs a monolith never has to pay, because there's only ever
one process making decisions.
