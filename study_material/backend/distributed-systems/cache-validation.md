---
concepts: [cache-validation]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: [caching-strategies]
interview_angle: >
  Be ready to distinguish a TTL-only cache (never re-checks, just expires) from ETag/conditional-
  request validation (checks with the origin whether the cached copy is still fresh, cheaply).
built_at: L6-T1
diagram: false
---

# Cache Validation

## Definition

`study_material/backend/caching-strategies.md` covers *where* a cached value comes from and how it's
invalidated; **cache validation** is specifically about *confirming a cached value is still fresh* before
serving it, without necessarily re-fetching the full response. HTTP's standard mechanism: the origin
server returns an **ETag** (a fingerprint of the resource) or `Last-Modified` timestamp with a response. A
client's next request sends that value back (`If-None-Match` / `If-Modified-Since`); if unchanged, the
server replies `304 Not Modified` with **no body at all** — the client keeps using its cached copy,
having spent only a small validation round-trip instead of re-downloading the full resource.

## Example

```
Request 1:
  GET /api/products/42
  Response: 200 OK, ETag: "a1b2c3", body: {...}

Request 2 (later, using the cached ETag):
  GET /api/products/42
  If-None-Match: "a1b2c3"
  Response: 304 Not Modified   ← no body sent; client's cached copy is confirmed still valid
```

## Why This Differs From a Pure TTL Cache

A pure TTL cache (`caching-strategies.md`'s cache-aside example) either serves stale data until the TTL
expires, or pays the full cost of a fresh fetch once it does — it never asks "is this actually still
valid?" cheaply. ETag validation gives freshness *and* low cost for the common case where the underlying
data hasn't actually changed: the client still makes a request, but the response is nearly free (no body)
when nothing changed, versus a full re-fetch on every TTL expiry regardless of whether the data moved.
