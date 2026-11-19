export type LearningModule = {
  id: string;
  title: string;
  summary: string;
  stage: string;
  status: "available" | "planned";
  topics: string[];
};

// Stable identifiers keep routes usable if the catalog later moves to a database.
// Planned topics are curriculum outlines, not links to unpublished lessons.
export const aiEngineerRoadmap: { id: string; title: string; description: string; modules: LearningModule[] } = {
  id: "ai-engineer-fde",
  title: "AI Engineer / FDE",
  description: "An applied path from learning fundamentals through dependable AI systems and customer delivery. ML foundations, queues, and scale and system design are ready to read; the remaining modules show the intended sequence.",
  modules: [
    { id: "ml-foundations", title: "ML foundations", stage: "01 · Foundations", summary: "Frame a learning problem, prepare data, understand training, evaluate decisions, and plan inference.", status: "available", topics: [] },
    {
      id: "cloud-foundations", title: "AWS and cloud foundations", stage: "02 · Foundations",
      summary: "Choose cloud primitives, networking, compute, and delivery tools for a workload and its trust boundaries.", status: "planned",
      topics: [
        "Regions, availability zones, edge locations, and multi-region placement",
        "IAM, identity boundaries, and least-privilege access",
        "VPCs, public and private subnets, routing, and network controls",
        "DNS, TCP versus UDP, HTTP/2 and HTTP/3, and gRPC",
        "EC2, Docker containers, Kubernetes, and managed container services",
        "Lambda, cold starts, and serverless limits",
        "S3, relational databases, NoSQL, and storage choices",
        "Infrastructure as code with Terraform and Helm charts",
        "CI/CD pipelines, build caching, dependency conflicts, and reproducible builds",
        "Service choice, cloud monitoring, and cost trade-offs",
      ],
    },
    {
      id: "async-systems", title: "Queues and reliable delivery", stage: "03 · Systems",
      summary: "Learn what queues do and when to use them, then make background work recoverable across failures.", status: "available",
      topics: [
        "Producers, message queues, consumers, workers, and job scheduling with cron",
        "Publish-subscribe and event-driven architecture",
        "Throughput, queue depth, latency, and backpressure",
        "Timeouts, retries, exponential backoff, jitter, and circuit breakers",
        "Dead-letter queues, poison messages, and replay",
        "Idempotency keys, duplicate effects, and delivery guarantees",
        "Distributed transactions, the outbox pattern, and saga compensation",
        "Webhooks, WebSockets, server-sent events, and long polling",
        "Failure recovery, ordering, and operational visibility",
      ],
    },
    { id: "models-transformers", title: "Neural networks and transformers", stage: "04 · AI foundations", summary: "Understand how modern models represent, train on, and generate sequences.", status: "planned", topics: ["Neurons, layers, and backpropagation", "Tokens and embeddings", "Attention and transformer blocks", "Pretraining, fine-tuning, and inference", "Context limits and model tradeoffs"] },
    {
      id: "scale-design", title: "Scale and system design", stage: "05 · Systems",
      summary: "Design API, data, and compute paths for peak load, consistency needs, and failure modes.", status: "available",
      topics: [
        "Requirements, capacity estimates, throughput, latency, and p99 tail latency",
        "Horizontal versus vertical scaling, autoscaling, and load balancing",
        "Reverse proxies, API gateways, service discovery, and rate limiting",
        "CDN and edge caching, application caches, and cache invalidation",
        "Database indexing, query optimization, and N+1 queries",
        "Connection pooling, read replicas, and replication lag",
        "Partitioning, sharding, and hot partitions",
        "CAP trade-offs, network partitions, clock skew, and eventual consistency",
        "Optimistic and pessimistic locking, distributed locks, and leader election",
        "Race conditions, deadlocks, thread safety, memory leaks, and garbage collection",
        "API and schema versioning, semantic versioning, and compatibility",
        "Architecture review and explicit trade-off decisions",
      ],
    },
    { id: "embeddings", title: "Embeddings and vector search", stage: "06 · AI systems", summary: "Represent content for similarity search and maintain a useful index.", status: "planned", topics: ["Embedding spaces and similarity", "Chunking and document metadata", "Vector indexes and approximate search", "Filtering and permission boundaries", "Search quality and index freshness"] },
    { id: "rag", title: "Retrieval augmented generation", stage: "07 · AI systems", summary: "Build grounded answers from controlled, current sources.", status: "planned", topics: ["Ingestion and source provenance", "Retrieval and context assembly", "Grounded generation and citations", "No-evidence behavior", "Access control across the pipeline"] },
    { id: "rag-evaluation", title: "Retrieval and answer evaluation", stage: "08 · AI systems", summary: "Measure what retrieval finds and what an answer claims.", status: "planned", topics: ["Representative question sets", "Recall and ranking measures", "Answer faithfulness and citation checks", "Hybrid retrieval and reranking", "Failure diagnosis and regression gates"] },
    { id: "agents-workflows", title: "Agents and workflow execution", stage: "09 · AI systems", summary: "Let models propose steps while deterministic code controls authority and effects.", status: "planned", topics: ["Tool schemas and validation", "Workflow state and persistence", "Authorization and approval gates", "Retries, compensation, and recovery", "Tracing agent decisions and outcomes"] },
    {
      id: "production-ai", title: "Production AI, cost, and security", stage: "10 · Production",
      summary: "Ship and operate AI features with measured quality, secure boundaries, recoverable releases, and clear budgets.", status: "planned",
      topics: [
        "AI gateway, provider fallback, latency budgets, and token costs",
        "Observability: monitoring, logging, distributed tracing, metrics, and alerts",
        "SLIs, SLOs, error budgets, and alert response",
        "Feature flags, blue-green deployments, canary releases, and rolling deployments",
        "Health checks, liveness and readiness probes, and rollbacks",
        "Threat modeling, prompt injection, and safe tool boundaries",
        "Secrets management, IAM, and credential rotation",
        "OAuth, JWT lifecycle and rotation, and session security",
        "TLS, encryption in transit, and encryption at rest",
        "CORS, CSRF, SQL injection, XSS, and SSRF defenses",
        "WAF, DDoS protection, abuse controls, and tenant isolation",
        "Backups, disaster recovery, failover, and multi-region recovery",
        "Chaos engineering and failure exercises",
        "Cost optimization and capacity budgets",
        "Production incidents, on-call practice, and postmortems",
      ],
    },
    { id: "email-reliability", title: "Email infrastructure and recovery", stage: "11 · Production", summary: "Make email delivery trustworthy through authentication, feedback, and recovery.", status: "planned", topics: ["SMTP and delivery lifecycle", "SPF, DKIM, and DMARC", "Bounces, complaints, and suppression", "Provider failover and rate control", "RTO, RPO, and incident runbooks"] },
    { id: "fde-delivery", title: "Forward deployed engineering", stage: "12 · Delivery", summary: "Translate a customer problem into an integrated, measurable production outcome.", status: "planned", topics: ["Discovery and problem framing", "Integration and data constraints", "Pilot scope and acceptance criteria", "Deployment, handoff, and support", "Outcome measurement and iteration"] },
  ],
};
