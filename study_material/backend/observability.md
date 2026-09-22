t---
concepts: [logging, metrics, distributed-tracing]
concept_category: DevOps/Infra
difficulty: intermediate
prerequisites: [microservices-architecture]
interview_angle: >
  Be ready to explain why distributed tracing specifically becomes necessary once you have
  microservices — a single request now crosses process/network boundaries, and logs alone can't
  reconstruct the causal chain across services without a shared trace ID.
built_at: L6-T1
diagram: true
---

# Observability: Logs, Metrics, Traces

## Definition

The three pillars of observability, each answering a different question:

- **Logs:** discrete, timestamped events — "what happened, in detail, at this specific point." Best for
  deep-diving one specific incident once you already know roughly where to look.
- **Metrics:** aggregated numeric measurements over time (request rate, error rate, p99 latency) — best
  for spotting *that* something's wrong and *how bad*, cheap to store and alert on, but they don't tell
  you *why*.
- **Distributed tracing:** follows one request's full path across multiple services, tagged with a shared
  **trace ID**, showing exactly where time was spent and where it failed — the only one of the three that
  reconstructs causality across service boundaries.

## Example

```python
# Logs — verbatim record of a raw build error, matching this framework's own discipline
# (framework.md's build pipeline: "raw build log, never paraphrased")
logger.error(f"Build {build_id} failed: {raw_mkdocs_output}")

# Metrics — aggregate signal
build_duration_seconds.observe(elapsed)
build_failures_total.inc()

# Tracing — a shared trace ID follows one request end-to-end
# [trace_id=abc123] Dashboard → Pipeline → RepoFetcher → VercelProvider → Vercel API
```

## Diagram

```aosdf-diagram
One request, traced across services (single trace_id):
Dashboard ──▶ Pipeline ──▶ Repo Fetcher ──▶ Vercel Provider ──▶ Vercel API
   │ log         │ log          │ log             │ log             │ log
   └─────────────┴──────────────┴─────────────────┴─────────────────┘
              all tagged trace_id=abc123 — reconstructs the full path
```

## Why All Three, Not Just One

Metrics tell you *that* the hosting pipeline's build failure rate spiked at 2pm; logs tell you *what*
error a specific failed build hit; tracing tells you *where* in the chain (repo fetch? Vercel API call?)
a specific slow build actually spent its time. Each pillar alone leaves a real blind spot the other two
cover.
