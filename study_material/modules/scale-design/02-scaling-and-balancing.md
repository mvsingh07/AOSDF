# Scaling and load balancing

**Vertical scaling** gives one machine more CPU, memory, or I/O capacity. **Horizontal scaling** adds machines or processes. Either may help, but only at the current bottleneck. Two API instances do not double throughput when both wait on the same saturated database.

## Make API instances interchangeable

A load balancer distributes incoming connections among healthy API instances. The API should keep durable state in the database or object store, not solely in one process's memory. Store browser session state in a signed token or shared session store according to the security model; do not require “sticky” routing just to find an editor's document. Health checks remove an instance that cannot serve traffic, while **draining** lets existing requests finish before a rollout or scale-down. A health check should reflect the dependencies needed for the endpoint, without causing every transient dependency blip to restart every instance.

Autoscaling adds or removes instances based on a signal such as CPU, request rate, or queue depth. The signal must relate to the bottleneck, and the policy needs warm-up, bounds, and cooldown. Scaling from two to twenty API instances can accidentally create hundreds of new database connections; the connection budget is a separate design decision.

## Worked bottleneck comparison

At peak, an API fleet has CPU at 85%, database CPU at 30%, and p99 latency rises with API request queueing. More API instances may help. In another peak, API CPU is 25% and database connections are maxed out. More API instances may worsen contention. Measure per-stage latency, saturation, error rate, and p99 while changing one variable. Run a load test using a realistic mix of opens, edits, and searches rather than one cheap endpoint.

## Diagram: add instances at the bottleneck

![A load balancer routes readers across healthy API instances; all instances share a database, whose connection limit remains a shared constraint.](/learning/scale-design/scaling.svg)

```aosdf-diagram
Readers ──▶ load balancer ──▶ API A ─┐
                          └──▶ API B ─┼──▶ shared database
                          └──▶ API C ─┘
```

## Implementation: route to interchangeable instances

NGINX can distribute HTTP traffic; Kubernetes can manage replicas, readiness, and horizontal autoscaling; Prometheus can expose the saturation that tells you whether scaling helped. A managed load balancer can play the ingress role in another environment. None of these tools removes the shared database limit.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![nginx logo](/learning/scale-design/logo-nginx.svg) | [NGINX load balancing](https://nginx.org/en/docs/http/load_balancing.html) | Route requests across API instances. | Configure upstream failure behavior and request timeouts. |
| ![kubernetes logo](/learning/scale-design/logo-kubernetes.svg) | [Kubernetes HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/) | Adjust replica count from a measured workload signal. | Provide resource requests, readiness, and scale-down behavior. |
| ![prometheus logo](/learning/scale-design/logo-prometheus.svg) | [Prometheus](https://prometheus.io/docs/introduction/overview/) | Track API saturation, database connections, and errors. | Confirm the bottleneck moved after scaling. |

A small NGINX upstream for two interchangeable instances looks like this; production deployments also need TLS, readiness, and graceful draining:

```nginx
upstream document_api {
    server api-a:8080;
    server api-b:8080;
}
server {
    listen 80;
    location / { proxy_pass http://document_api; }
}
```

Set an aggregate database connection budget before raising the HPA maximum. For example, 20 replicas × 12 connections = 240 potential API connections. If the database can safely support only 200 after reserves, the autoscaling policy and pool settings disagree.

## Engineering exercise

Your API p99 doubled after adding instances, while database active connections hit its limit. Describe what to measure next and two safer fixes. Include how you would verify the change and roll it back.

## Design review questions

- What makes a process stateless enough for a load balancer?
- Why can autoscaling increase errors?
- What is the role of draining during a deployment?

**Review criteria:** any instance can reconstruct required request state from shared durable sources; new instances can overwhelm a shared dependency; draining protects in-flight work while routing stops.

## Read further

- [Kubernetes workload autoscaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/)
- [AWS Auto Scaling with a load balancer](https://docs.aws.amazon.com/autoscaling/ec2/userguide/autoscaling-load-balancer.html)
