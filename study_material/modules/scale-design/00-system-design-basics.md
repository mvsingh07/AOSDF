# What system design solves

A system is the people-facing behavior plus the software and data paths that produce it. **System design** asks how those parts will meet a promise under ordinary traffic, failure, and change. A diagram is useful only when its arrows have a contract: who sends what, where truth is stored, and what happens if a box is unavailable.

## Begin with behavior, not boxes

Our document library has three actions: open a document, save an edit, and search documents the user may access. Begin with one API and one relational database. Store a document ID, owner, access rule, title, version, and object-storage key in the database; keep larger document bodies in object storage. On a read, authorize the user **before** returning a body or a cached result. On a save, update the document version atomically and return the new version.

Write two kinds of requirement. **Functional**: an editor can save a document and another authorized reader can open it. **Quality**: for example, 99% of authorized document opens finish within 400 ms, and a successful save is visible to that editor immediately. Define what a failed save looks like; a timeout does not prove that no write occurred. A service level objective (SLO) measures an observable promise, whereas a server specification is only one means to meet it.

| Concern | Example question | Initial answer |
| --- | --- | --- |
| Users | Who can read and edit? | Owner and granted collaborators |
| Correctness | Can edits overwrite each other? | Compare the submitted version |
| Speed | Which action matters most? | Document open p99 under 400 ms |
| Durability | What must survive a crash? | A confirmed edit and its version |
| Failure | Can a read be stale? | Listing may lag; own edit may not |

## Diagram: one request before scale

![An authorized reader passes through the API; metadata and access are checked before the document body is returned.](/learning/scale-design/requirements.svg)

```aosdf-diagram
Browser ──▶ API ──▶ access + metadata in primary DB
                └──▶ body in object storage ──▶ authorized response
```

The drawing intentionally omits caches and replicas. Starting here exposes the correctness boundary that every later optimization must preserve. A cache key that ignores user permissions could turn a fast design into a data leak.

## Worked design decision

Suppose opening a small document takes 130 ms at p99 and the goal is 400 ms. No scaling component is justified yet. Suppose instead search takes 1.8 seconds because it scans every document. Adding API replicas will not change the scan; inspect the query and index first. This is the core system-design habit: find the limiting path, then change that path.

## Implementation: a credible first stack

An engineer should be able to build and instrument the smallest version before sketching a fleet. One possible stack is NGINX at ingress, FastAPI for a Python document API, PostgreSQL for metadata and versions, an S3-compatible object store for bodies, and OpenTelemetry for request traces. The API still owns authorization; storage location does not decide who can see a document.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![nginx logo](/learning/scale-design/logo-nginx.svg) | [NGINX](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) | Forward HTTP requests to the API. | Set timeouts and trusted forwarded headers explicitly. |
| ![fastapi logo](/learning/scale-design/logo-fastapi.svg) | [FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/) | Express request handlers and inject an authenticated principal. | Put object authorization in the handler or service, not only a global dependency. |
| ![postgresql logo](/learning/scale-design/logo-postgresql.svg) | [PostgreSQL](https://www.postgresql.org/docs/current/) | Keep access, metadata, and version changes in transactions. | Model permission and version constraints before optimizing. |
| ![opentelemetry logo](/learning/scale-design/logo-opentelemetry.svg) | [OpenTelemetry](https://opentelemetry.io/docs/concepts/) | Trace the request across API, database, and object retrieval. | Do not put document content or tokens in spans. |

For the first implementation, define `documents(id, tenant_id, owner_id, version, object_key)` and a FastAPI `GET /documents/{id}` handler. A dependency can resolve the signed-in principal; the handler or document service must then check that principal's tenant and document permission **before** fetching the object. Record one span for the permission query and one for object retrieval. A fast response that bypasses the permission check is a correctness failure, regardless of its latency.

## Engineering exercise

Write four sentences for a photo library: one user action, one correctness rule, one p99 target, and one failure response. Sketch the smallest request path and mark the durable source of truth.

## Design review questions

- What is the difference between “four servers” and “p99 open latency under 400 ms”?
- Why must an access check apply even when a body is cached?
- Which measurement would justify an index before a load balancer?

**Review criteria:** the first is an implementation choice and the second is a user-visible promise; cached data can still be private; a slow query plan or high database scan time points at the data path.

## Read further

- [Google SRE: service level objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE: monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/)
