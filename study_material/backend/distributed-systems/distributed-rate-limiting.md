---
concepts: [distributed-rate-limiting]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [rate-limiting]
interview_angle: >
  Be ready to explain why a naive per-instance rate limiter (each server tracking its own counter in
  memory) silently multiplies the effective limit by the number of instances — and what a shared
  store fixes.
built_at: L6-T1
diagram: false
---

# Distributed Rate Limiting

## Definition

`study_material/backend/load-balancing-rate-limiting.md` covers rate limiting on a single instance —
but behind a load balancer with N instances, a per-instance in-memory counter means a client can actually
make N times the intended limit (a different request hits a different instance, each with its own,
un-shared counter). Distributed rate limiting solves this by making the counter **shared state** — every
instance checks and increments the same store (typically Redis) instead of its own local memory, so the
limit is enforced against the client's *total* traffic across all instances.

## Example

```python
# Shared, atomic counter in Redis — every instance checks the same state
def allow(client_id, limit=100, window_seconds=60):
    key = f"rl:{client_id}:{int(time.time() // window_seconds)}"
    count = redis.incr(key)          # atomic increment, shared across every instance
    redis.expire(key, window_seconds)
    return count <= limit
```

## The Real Trade-off

The shared store becomes a new point of coordination — every request now pays a network round-trip to
Redis, and Redis itself becomes a dependency the rate limiter can't function without (a real availability
trade-off, not a hidden one). At very high scale, this is sometimes relaxed deliberately: each instance
gets a local budget (`total_limit / instance_count`) and only periodically syncs with the shared store,
trading perfect accuracy for lower coordination overhead — a real, documented compromise, not an
oversight.
