---
concepts: [circuit-breaker, cascading-failure, bulkhead-pattern, graceful-degradation]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: []
interview_angle: >
  Be ready to explain the three circuit breaker states (closed/open/half-open) precisely, and to
  give one concrete example of a cascading failure that a circuit breaker would have stopped.
built_at: L6-T1
diagram: true
---

# Resilience Patterns: Circuit Breaker, Bulkhead, Graceful Degradation

## Definition

- **Cascading failure:** one component's failure or slowness overloads the components that depend on it
  (they're all now waiting/retrying against it), which then overloads *their* dependents in turn — a
  single slow dependency can bring down an entire system if nothing isolates the damage.
- **Circuit breaker:** wraps a call to a dependency and tracks its failure rate. **Closed** (normal) —
  calls pass through. After enough failures, it trips to **Open** — calls fail immediately without even
  attempting the dependency, giving it time to recover instead of piling on more load. After a cooldown,
  it moves to **Half-Open** — lets a small number of test calls through; if they succeed, back to Closed,
  if they fail, back to Open.
- **Bulkhead pattern:** isolate resources (thread pools, connection pools) per dependency, so one slow or
  failing dependency can't exhaust resources shared with everything else — named after ship compartments
  designed so one flooded section doesn't sink the whole vessel.
- **Graceful degradation:** when a non-critical dependency fails, serve a reduced but still-functional
  experience (e.g. show a product page without personalized recommendations) rather than failing the
  entire request.

## Example

```python
class CircuitBreaker:
    def call(self, fn):
        if self.state == "OPEN":
            if time.time() - self.opened_at < self.cooldown:
                raise CircuitOpenError()  # fail fast, don't even try
            self.state = "HALF_OPEN"
        try:
            result = fn()
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"; self.failures = 0
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold:
                self.state = "OPEN"; self.opened_at = time.time()
            raise
```

Graceful degradation using the same breaker: `if recommendations_breaker.is_open(): return page_without_recommendations()`.

## Diagram

```aosdf-diagram
        failures ≥ threshold
 CLOSED ────────────────────▶ OPEN
   ▲                            │
   │ test call succeeds         │ cooldown elapsed
   │                            ▼
   └──────────────────── HALF-OPEN
         test call fails: back to OPEN
```

## Why All Three Together

They're commonly taught as a trio because they solve the same underlying problem — an unhealthy
dependency shouldn't be able to take down everything that calls it — at three different points: the
bulkhead limits *how much* of a shared resource one dependency can consume, the circuit breaker stops
*calling* a dependency once it's clearly unhealthy, and graceful degradation decides *what to serve
instead* when that happens.
