---
concepts: [token-bucket, leaky-bucket, fixed-window-counter, sliding-window-log]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: [rate-limiting]
interview_angle: >
  Be ready to compare these on burst tolerance and memory cost specifically: token bucket allows bursts
  up to the bucket size, fixed window has a boundary edge-case that can let through 2x the intended rate,
  and sliding window log is precise but stores a timestamp per request.
built_at: L6-T1
diagram: true
---

# Rate Limiting Algorithms

## Definition

`load-balancing-rate-limiting.md` covers *why* rate limiting exists; this covers *how* the limit itself is
actually enforced:

- **Token bucket:** a bucket holds up to `N` tokens, refilled at a fixed rate; each request consumes one
  token, and is rejected if the bucket is empty. Allows short bursts (up to the bucket's full capacity)
  while enforcing a long-run average rate. The most commonly used algorithm in practice.
- **Leaky bucket:** requests enter a fixed-size queue and are processed at a constant fixed rate,
  regardless of burstiness on the way in — smooths bursts into a steady output rate, but a burst can fill
  the queue and cause later requests in that burst to be dropped or delayed.
- **Fixed window counter:** count requests in a fixed time window (e.g., "100 per minute, aligned to the
  clock minute"); simplest to implement, but has an edge-case: a client can send 100 requests in the last
  second of one window and another 100 in the first second of the next, getting 200 requests in ~2 seconds.
- **Sliding window log:** store a timestamp per request in a rolling window and count how many fall within
  the last `N` seconds — precise, no boundary edge-case, but memory cost grows with request volume instead
  of being a fixed counter.

## Example

```python
# Token bucket — the algorithm behind most production rate limiters (e.g. AWS API Gateway, Stripe API)
class TokenBucket:
    def __init__(self, capacity, refill_rate_per_sec):
        self.capacity = self.tokens = capacity
        self.refill_rate = refill_rate_per_sec
        self.last_refill = time.monotonic()

    def allow(self):
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.last_refill) * self.refill_rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

## Diagram

```aosdf-diagram
Token bucket:   [●●●○○]  refills over time ──▶  each request removes one ●, rejected if empty

Fixed window:   |--- 100 req cap ---|--- 100 req cap ---|
                                  ▲ 100 req here  100 req here ▲
                                  └── both allowed: 200 req in ~2 sec ──┘   (the edge-case)
```
