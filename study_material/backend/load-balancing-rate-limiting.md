---
concepts: [load-balancing, rate-limiting]
concept_category: Networking
difficulty: intermediate
prerequisites: []
interview_angle: >
  Be ready to name a specific load-balancing algorithm beyond round-robin (e.g. least-connections)
  and explain when round-robin's assumption — that every request costs the same — breaks down.
built_at: L6-T1
diagram: true
---

# Load Balancing & Rate Limiting

## Definition

- **Load balancing:** distributing incoming requests across multiple server instances so no single
  instance is overwhelmed. Common algorithms: **round-robin** (requests cycle through servers in order —
  simple, but assumes every request is equally cheap), **least-connections** (send to whichever server
  currently has the fewest active connections — better when request cost varies), and consistent hashing
  (used when requests for the same key should reliably land on the same server, e.g. for caching
  locality).
- **Rate limiting:** capping how many requests a client can make in a given time window, protecting the
  service from being overwhelmed (accidentally by a bug, or deliberately by abuse). Common algorithms:
  fixed window, sliding window, and token bucket (allows short bursts up to a cap, then throttles to a
  steady refill rate).

## Example

```python
# Token bucket rate limiter — allows bursts, then steady-state throttling
class TokenBucket:
    def allow(self, client_id):
        bucket = self.buckets[client_id]
        bucket.refill(rate=10, per_seconds=1)  # 10 tokens/sec steady rate
        if bucket.tokens >= 1:
            bucket.tokens -= 1
            return True
        return False  # rate limited
```

## Diagram

```aosdf-diagram
                    ┌──────────────┐
                    │ Load Balancer │
                    └──────┬───────┘
          ┌──────────────┼──────────────┐
          ▼               ▼               ▼
   ┌───────────┐  ┌───────────┐  ┌───────────┐
   │ Server A   │  │ Server B   │  │ Server C   │
   └───────────┘  └───────────┘  └───────────┘
```

## Where This Connects to a Real AOSDF Pattern

This framework's own **Tenant Reputation Gating** reusable pattern (`framework.md` § Reusable
Architecture Patterns) is rate limiting applied per-tenant on shared outbound infrastructure, with a
graduated ladder (`HEALTHY → WATCHLIST → THROTTLED → SUSPENDED → BANNED`) rather than a single fixed
threshold — a more sophisticated version of the same core idea shown here.
