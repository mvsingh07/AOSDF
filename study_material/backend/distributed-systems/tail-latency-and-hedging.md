---
concepts: [tail-latency, request-hedging]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: []
interview_angle: >
  Be ready to explain why average latency is a misleading metric at scale — with enough parallel
  calls, a request's overall latency is dominated by its slowest dependency (p99), not the average
  one — and why hedging trades extra load for a better tail.
built_at: L6-T1
diagram: false
---

# Tail Latency & Request Hedging

## Definition

**Tail latency** is how slow the *slowest* requests are (p95/p99/p999), as distinct from average
latency. It matters disproportionately in fan-out systems: if a page load makes 100 parallel backend
calls and each has a 1% chance of a slow (p99) response, the overall page has roughly a 63% chance that
*at least one* of those calls is slow — the user experiences the tail far more often than any single
dependency's own p99 suggests.

**Request hedging:** if a request hasn't returned within some threshold (e.g. the p95 latency for that
call), fire a second, redundant request to a different replica/instance, and use whichever response comes
back first, cancelling the other. Trades extra load (occasional duplicate requests) for a much better
tail — most hedged requests never even need the second call, since it's only sent when the first is
already running unusually slow.

## Example

```python
def hedged_call(fn, hedge_delay_ms=100):
    first = async_call(fn)
    if not first.done_within(hedge_delay_ms):
        second = async_call(fn)  # only fired if the first is already slow
        return first_to_complete(first, second)
    return first.result()
```

## Why This Matters at Scale

This is exactly why a well-designed system tracks and alerts on p99/p999 latency, not just the average —
a service with a great *average* latency can still deliver a terrible experience to a meaningful fraction
of users if its tail is long. Hedging is a real, deliberate trade-off (accepting some wasted duplicate
work) to shrink that tail, not a free optimization — it's typically reserved for read-only, idempotent
calls specifically because firing a redundant request is safe to do.
