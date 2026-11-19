# The edge and API boundary

A **reverse proxy** receives a client request and forwards it to an internal service. A **load balancer** spreads traffic among instances. An **API gateway** can add routing, authentication integration, quotas, and policy at a shared entry point. These roles may be implemented by one product, but the responsibilities should stay explicit in the design.

## Trace one request through the boundary

A reader requests `GET /documents/42`. At the edge, terminate TLS and reject malformed or oversized requests. The gateway routes to the document API, checks a validated identity where appropriate, and applies a per-user or per-tenant rate limit. The API still performs document-level authorization: a gateway can know the user but usually cannot know whether that user may read document 42. Internal **service discovery** maps a service name to currently healthy endpoints, so adding an instance does not require clients to learn its address.

A token bucket is one rate-limit model: tokens arrive at a configured rate up to a burst capacity; each request consumes one. A full bucket allows a short burst, while a sustained flood is limited. For example, a 20-token bucket refilled at 5 tokens/second allows a burst of 20 and then roughly 5/second. Limits should be scoped to the actual abuse and fairness boundary. A single global quota can let one tenant crowd out another. Return an intelligible `429` and retry guidance when a client is limited.

## Keep trust boundaries visible

Forwarded headers such as client IP or user identity are trustworthy only when set and sanitized by a proxy you control. The API must validate auth and authorization at its own boundary; rate limiting is not a substitute. If the gateway is unavailable, it is an availability dependency. Define timeouts, health checks, and a policy for overload before moving all traffic through it.

## Diagram: edge to authorized data

![TLS termination and request limits precede routing; the document API checks the user's permission before reading the record.](/learning/scale-design/api-boundary.svg)

```aosdf-diagram
Browser ──▶ edge/proxy ──▶ gateway: route + quota ──▶ API: document authorization
                                                    └──▶ data only after approval
```

## Implementation: make routing and limits enforceable

A typical deployment uses an edge proxy, Kubernetes Service discovery, and a shared Redis-backed limiter. Envoy Gateway is another entry-point implementation when route policy and per-tenant limits need central management. Pick one owner for each rule so the API and gateway do not silently disagree.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![envoyproxy logo](/learning/scale-design/logo-envoyproxy.svg) | [Envoy Gateway](https://gateway.envoyproxy.io/docs/concepts/rate-limiting/) | Apply local or global HTTP rate-limit policy. | Local limits are per instance; global limits need a shared service. |
| ![kubernetes logo](/learning/scale-design/logo-kubernetes.svg) | [Kubernetes Service](https://kubernetes.io/docs/concepts/services-networking/service/) | Resolve a stable service name to healthy API endpoints. | Readiness and endpoint updates affect where requests go. |
| ![redis logo](/learning/scale-design/logo-redis.svg) | [Redis rate limiter](https://redis.io/docs/latest/develop/use-cases/rate-limiter/) | Maintain quota state shared across gateway instances. | Make read-decide-update atomic; define outage behavior. |

For a tenant quota, key the limit by `tenant_id` and route, not a client-provided IP alone. A token bucket with capacity 20 and refill 5/second permits a short burst while holding the sustained rate near 5/second. If the decision uses Redis, perform the token calculation and update atomically, for example through a script or a supported limiter. Decide whether an unavailable limiter fails open or closed for each endpoint; editing and public search may warrant different choices. The API still checks object authorization after the gateway accepts the request.

## Engineering exercise

Design quotas for a library with one free user who may issue 10 searches/minute and a business tenant allowed 1,000/minute. Decide the token-bucket key, burst size, and response when a limit is hit. Say where document authorization happens.

## Design review questions

- Can a gateway's authentication check replace document authorization?
- What does service discovery change when an API instance is replaced?
- Why distinguish a short burst from sustained request rate?

**Review criteria:** identity does not imply permission on a particular resource; discovery resolves a service name to the healthy instance set; bursts are normal but continuous excess can exhaust capacity.

## Read further

- [AWS API Gateway throttling and token buckets](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-throttling.html)
- [Kubernetes Services and service discovery](https://kubernetes.io/docs/concepts/services-networking/service/)
