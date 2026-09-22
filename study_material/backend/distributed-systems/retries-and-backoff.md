---
concepts: [retry-policy, exponential-backoff, jitter]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: []
interview_angle: >
  Be ready to explain why naive fixed-interval retries make an outage worse (synchronized retry
  waves) and why jitter specifically — not just backoff alone — is the fix for that.
built_at: L6-T1
diagram: false
---

# Retries, Exponential Backoff & Jitter

## Definition

- **Retry policy:** on a failed (typically transient — timeout, `503`, connection reset) request, try
  again rather than failing immediately — but only for **idempotent** operations (`reliable-messaging-
  patterns.md`), since retrying a non-idempotent write could duplicate its effect.
- **Exponential backoff:** each successive retry waits longer than the last (`base * 2^attempt`) instead
  of retrying immediately — gives a struggling downstream service increasing room to recover instead of
  being hit with a steady stream of retries right when it's least able to handle them.
- **Jitter:** adding randomness to the backoff delay. Without it, many clients that failed at the same
  moment (a brief outage) all retry at *exactly* the synchronized backoff intervals, recreating the
  thundering herd problem (`backpressure-and-thundering-herd.md`) they were trying to avoid.

## Example

```python
def retry_with_backoff(fn, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            return fn()
        except TransientError:
            if attempt == max_attempts - 1:
                raise
            delay = min(2 ** attempt, 30)          # exponential backoff, capped
            delay += random.uniform(0, delay * 0.5)  # jitter — spreads out synchronized retries
            time.sleep(delay)
```

## Why "Just Retry" Isn't Enough

A retry policy without backoff can turn a brief blip into a sustained outage (retries themselves become
the overload); backoff without jitter can leave every client retrying in near-perfect sync anyway if they
all failed at the same instant. The combination — increasing delay, randomized — is what actually spreads
retry load out over time instead of concentrating it.
