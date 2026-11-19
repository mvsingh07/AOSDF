# Scale and system design

A system design is a set of decisions about how requests move through software, where data lives, what happens under load, and what users see when parts fail. **Scale** means the system can keep its promised behavior as demand grows. It is not a server count: a fast API with a saturated database or an incorrect cache is not successfully scaled.

This module starts with a simple **shared document library**. A reader opens a document, an editor changes it, and authorized users search their library. We begin with one API process and one database. Each later lesson adds a component only when a stated requirement or measured bottleneck justifies it. The example uses ordinary HTTP and relational data; the principles apply to many products.

![Reader and editor requests enter a service, which reads and writes the primary database and stores document bodies.](/learning/scale-design/system-map.svg)

```aosdf-diagram
Reader / Editor ──▶ API ──▶ Primary database (metadata, access, versions)
                       └────▶ Object store (document bodies)
```

## Who this is for

Begin with HTTP requests and a database table; no distributed-systems background is assumed. If you already review production architectures, use the worked estimates, failure contracts, and review checklist to challenge your assumptions. Every lesson has a browser-rendered figure, a text alternative, an exercise, and primary references.

## What you will learn

- Turn user promises into measurable latency, correctness, capacity, and recovery requirements.
- Estimate peak load, concurrency, and p99 latency instead of sizing from average traffic alone.
- Place load balancing, gateways, caches, replicas, partitions, and indexes at the right boundary.
- Explain exactly what a user may observe during replication lag, simultaneous edits, and network partitions.
- Make API, schema, and operational changes while old and new versions coexist.

## Learning approach

Read in order if these topics are new. After each **Engineering exercise**, add a paragraph to one design note for the document library: requirements, capacity estimate, traffic path, cache policy, data access, consistency contract, concurrency rule, and rollout plan. Numbers are illustrative, not universal defaults. A professional design replaces them with measurements and an explicit error budget.

## Diagram: the architecture as demand grows

The full diagram shows an edge cache, load balancer, API fleet, application cache, primary database, read replica, and object store. Follow its arrows while reading. It is a possible design, not a mandate to deploy every box.

<!-- SCALE_DESIGN_DIAGRAM -->

## Reference stack at a glance

These are examples of products and frameworks an engineering team could use to implement the paths in this module. Each lesson explains a choice and its limits; the logos identify actual tools, not a required stack. The browser serves these marks from local SVG assets.

| Logo | Tool | Concrete role |
| :---: | --- | --- |
| ![NGINX logo](/learning/scale-design/logo-nginx.svg) | [NGINX](https://nginx.org/en/docs/) | Reverse proxy and load balancing at the API entry point |
| ![FastAPI logo](/learning/scale-design/logo-fastapi.svg) | [FastAPI](https://fastapi.tiangolo.com/) | Example Python HTTP framework for the document API |
| ![Kubernetes logo](/learning/scale-design/logo-kubernetes.svg) | [Kubernetes](https://kubernetes.io/docs/concepts/) | Service discovery, readiness, and workload autoscaling |
| ![PostgreSQL logo](/learning/scale-design/logo-postgresql.svg) | [PostgreSQL](https://www.postgresql.org/docs/current/) | Authoritative metadata, transactions, indexes, and replication |
| ![Redis logo](/learning/scale-design/logo-redis.svg) | [Redis](https://redis.io/docs/latest/) | Bounded application cache and shared rate-limit state |
| ![Cloudflare logo](/learning/scale-design/logo-cloudflare.svg) | [Cloudflare Cache](https://developers.cloudflare.com/cache/) | Edge delivery of public, cacheable assets |
| ![OpenTelemetry logo](/learning/scale-design/logo-opentelemetry.svg) | [OpenTelemetry](https://opentelemetry.io/docs/) | Traces across request, data, and storage paths |
| ![Prometheus logo](/learning/scale-design/logo-prometheus.svg) | [Prometheus](https://prometheus.io/docs/) | Request histograms, saturation, and error measurements |
| ![Grafana k6 logo](/learning/scale-design/logo-k6.svg) | [Grafana k6](https://grafana.com/docs/k6/latest/) | Representative load tests before capacity decisions |

## Lesson index

| Order | Lesson | Question it answers |
| --- | --- | --- |
| 1 | [What system design solves](/learn/ai-engineer-fde/scale-design/system-design-basics) | What must a service do before adding servers? |
| 2 | [Capacity, throughput, and tail latency](/learn/ai-engineer-fde/scale-design/capacity-and-latency) | How much traffic and delay must the design absorb? |
| 3 | [Scaling and load balancing](/learn/ai-engineer-fde/scale-design/scaling-and-balancing) | How do extra instances help without creating a new bottleneck? |
| 4 | [The edge and API boundary](/learn/ai-engineer-fde/scale-design/edge-and-api-boundary) | Where are requests routed, limited, and authenticated? |
| 5 | [Caching and invalidation](/learn/ai-engineer-fde/scale-design/caching-and-invalidation) | What can be reused, and how does it become fresh? |
| 6 | [Queries, indexes, and connections](/learn/ai-engineer-fde/scale-design/queries-and-connections) | How can data access stay fast without exhausting the database? |
| 7 | [Replication, partitioning, and sharding](/learn/ai-engineer-fde/scale-design/replication-and-sharding) | When does one database stop being enough? |
| 8 | [Consistency, partitions, and time](/learn/ai-engineer-fde/scale-design/consistency-and-time) | What does a reader see after a write or network failure? |
| 9 | [Concurrency, locks, and runtime health](/learn/ai-engineer-fde/scale-design/concurrency-and-runtime) | How are simultaneous edits and process failures controlled? |
| 10 | [Compatible change and architecture review](/learn/ai-engineer-fde/scale-design/compatibility-and-review) | How can a design evolve without breaking current users? |

## Completion check

Draw the read and edit paths. Explain the p99 target, peak load, database connection limit, cache freshness rule, read-after-write promise, simultaneous edit rule, and one rollback path. For each added component, say which measured problem it solves and which new failure it introduces.

## Primary references

- [Google SRE: service level objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE: monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [PostgreSQL: using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
