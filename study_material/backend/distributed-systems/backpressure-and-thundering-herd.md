---
concepts: [thundering-herd, backpressure]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: []
interview_angle: >
  Be ready to give a concrete thundering herd trigger (a cache expiry, a service restart with a
  shared retry interval) and explain how backpressure differs from a circuit breaker (slowing the
  source down vs. cutting it off).
built_at: L6-T1
diagram: false
---

# Thundering Herd & Backpressure

## Definition

- **Thundering herd problem:** a large number of clients/processes all wake up and act at the same
  moment, overwhelming a shared resource — e.g. every client using the same fixed retry interval retries
  at exactly the same time after an outage, or every worker process wakes up on the same OS timer tick to
  poll a queue. (Cache stampede, `cache-failure-patterns.md`, is the specific cache-flavored version of
  this same general problem.)
- **Backpressure:** a way for a slow consumer to signal upstream that it can't keep up, so the producer
  slows down instead of continuing to pile up more work than the consumer can ever process — the
  alternative to backpressure is an unbounded queue that just keeps growing until it exhausts memory.

## Example

Thundering herd fix — add jitter so retries spread out instead of aligning:

```python
def retry_delay(attempt):
    base = min(2 ** attempt, 30)
    return base + random.uniform(0, base * 0.5)  # jitter spreads clients out in time
```

Backpressure — a bounded queue that rejects or blocks new work once full, rather than growing forever:

```python
queue = BoundedQueue(max_size=1000)
def submit(task):
    if queue.is_full():
        raise BackpressureError()  # signal the caller to slow down, don't silently queue forever
    queue.put(task)
```

Reactive streaming systems (e.g. RxJS, Reactor) implement backpressure as a first-class protocol: a
consumer explicitly requests "N more items" from a producer, rather than the producer pushing everything
it has as fast as possible.

## Where They Connect

Both are about protecting a system from being overwhelmed, but at different points: thundering herd is
about *when* a burst of demand happens (many actors, coincidentally aligned), while backpressure is about
*how a system responds* once demand exceeds capacity, regardless of why.
