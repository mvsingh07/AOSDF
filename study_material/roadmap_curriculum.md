# AI Engineer / FDE Curriculum Coverage

The public roadmap interprets [`roadmap.md`](roadmap.md) as a dependency sequence, not a
12-week schedule. It preserves the reference's central idea: learn AI engineering, distributed
systems, AWS, system design, and FDE practice through general engineering examples.
There are no dates, study-hour targets, or course-completion gates on the website.

| Public domain | Reference material carried forward | Practical proof |
| --- | --- | --- |
| ML foundations | Week 1 ML concepts and evaluation questions | Dataset, baseline, split, error analysis |
| AWS and cloud foundations | Weeks 1–4 AWS region, IAM, VPC, compute, storage, and data choices | Secure deployment path with service trade-offs |
| Queues and reliable delivery | Weeks 1–2 queue, worker, retry, DLQ, idempotency; Week 7 event services | Asynchronous delivery path and failure table |
| Neural networks and transformers | Weeks 2–3 neural learning and attention | Explain training versus inference and token limits |
| Scale and system design | Week 3 1M-request design; Week 10 design framework | Peak-load estimate and architecture review |
| Embeddings and document pipelines | Week 4 embeddings, vector search, S3 pipeline | Permission-aware ingestion and index experiment |
| RAG foundations | Week 5 RAG V1, chunking, retrieval, citations | Grounded answer with no-evidence behavior |
| Advanced retrieval and evaluation | Week 6 hybrid retrieval, reranking, 20-case eval set | RAG variant comparison and error diagnosis |
| Agents and workflow execution | Week 7 tool calls, Step Functions, workflow design | Versioned proposal, validation, approval, execution |
| Production AI, cost, and security | Week 8 gateway, latency, cost, observability, AWS deployment; original security request | Traced AI request with budgets and policy gates |
| Email infrastructure and recovery | Week 9 SMTP, DNS authentication, bounces, provider failover, RTO/RPO | Deliverability and recovery runbook |
| FDE delivery and architecture proof | Weeks 10–12 system designs, customer scenarios, capstone, interview evidence | Scoped pilot, migration plan, measurable outcome |

The website shows all 12 modules in sequence. ML foundations has five separate lessons in
[`modules/ml-foundations/`](modules/ml-foundations/README.md), and Queues and reliable delivery
has eight in [`modules/async-systems/`](modules/async-systems/README.md). Scale and system design
has ten in [`modules/scale-design/`](modules/scale-design/README.md). All three open from their
own module indexes. Other nodes are shown as planned until complete documentation exists.
The project-specific `16_Learning_Roadmap` still derives from a project's own decisions.

## Topic-list coverage in the public outlines

Every entry in [`topic-list.md`](topic-list.md) now has a home in the planned module
outlines shown on the roadmap page. Unpublished outlines are curriculum commitments;
ML foundations, Queues and reliable delivery, and Scale and system design have reading pages. Several subjects also recur
across modules when applied to a different boundary (for example, IAM in cloud placement
and production credential handling).

| `topic-list.md` lines | Primary module | Placement |
| --- | --- | --- |
| 1–5 | Scale and system design | Rate limits, caches, load balancing, reverse proxies, API gateways |
| 6–7 | AWS and cloud foundations | CI/CD, Docker, Kubernetes |
| 8 | Scale and system design | Service discovery |
| 9–23 | Queues and reliable delivery | Failure controls, messaging, transactions, jobs, and real-time delivery |
| 24–42 | Scale and system design | Database performance, replication, consistency, locking, and runtime concurrency |
| 43 | Queues and reliable delivery | Backpressure |
| 44–48 | Scale and system design | Scaling and cache behavior |
| 49–64 | Production AI, cost, and security | Releases, health, observability, and service objectives |
| 65–78 | Production AI, cost, and security | Secrets, identity, transport, and web attack controls; IAM starts in cloud foundations |
| 79–80 | Scale and system design | Schema versioning appears twice in the source list and has one outline entry |
| 81–86 | Production AI, cost, and security | Recovery, fault exercises, and cost |
| 87–88 | AWS and cloud foundations | Serverless operational limits |
| 89–94 | Scale and system design | Latency, throughput, partitions, and clock skew |
| 95–98 | AWS and cloud foundations | DNS and network/application protocols |
| 99 | Queues and reliable delivery | Webhooks |
| 100–101 | Scale and system design | API and semantic versioning |
| 102–106 | AWS and cloud foundations | Infrastructure as code, Terraform, Helm, builds, and dependency conflicts |
| 107–109 | Production AI, cost, and security | Incidents, on-call, and postmortems |

The outline groups related concepts into teachable units; it does not imply one lesson per
source-list line. Author each planned module as indexed documentation before marking it
available. Keep the public examples general and link each published topic to its own
reading page.

The original plan treats DSA and interviews as recurring practice. The public, untimed
curriculum places coding, system-design, AI, and FDE evidence in the final domain and asks
readers to revisit those checks while building. It deliberately does not turn those topics
into a calendar or a credential checklist.
