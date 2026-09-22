---
concepts: [read-your-writes-consistency, eventual-consistency, strong-consistency]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [database-replication]
interview_angle: >
  Be ready to place read-your-writes on the spectrum between strong and eventual consistency — it's
  a specific, weaker-than-strong guarantee that's often exactly enough for the actual UX problem.
built_at: L6-T1
diagram: false
---

# Consistency Models: Read-Your-Writes, Eventual, Strong

## Definition

- **Strong consistency:** every read reflects the most recent committed write, no matter which
  replica/node answers it. Simplest to reason about, hardest to scale — usually requires coordination
  (quorum reads/writes, or routing everything through a single leader) that costs latency.
- **Eventual consistency:** replicas will *eventually* converge to the same value if writes stop, but a
  read immediately after a write might see stale data from a replica that hasn't caught up yet. Cheap and
  highly available, at the cost of that staleness window.
- **Read-your-writes consistency:** a specific, weaker-than-strong guarantee — a user is guaranteed to see
  their *own* writes immediately (reads are routed to a replica known to have their write, or to the
  primary for a short window after writing), even though *other* users might not see it yet. Solves the
  most common, most visible symptom of eventual consistency (a user who just posted a comment doesn't see
  it after refreshing) without paying for full strong consistency everywhere.

## Example

The classic eventual-consistency bug: a user updates their profile photo, refreshes, and sees the old
photo — because the read was served by a replica that hadn't yet received the write. Read-your-writes
fixes exactly this case by routing that user's subsequent reads to the primary (or a replica confirmed to
be caught up) for a short window, while still letting *other* users' reads hit any replica.

```python
def read_profile(user_id, requesting_user_id):
    if user_id == requesting_user_id and just_wrote_recently(user_id):
        return read_from_primary(user_id)   # guarantee this user sees their own write
    return read_from_any_replica(user_id)    # eventual consistency is fine for everyone else
```

## The Real Decision

Full strong consistency everywhere is rarely worth its latency/availability cost — most products only
need read-your-writes for the specific action a user just took, and can tolerate eventual consistency for
everything else (another user's activity feed lagging by a second is usually invisible).
