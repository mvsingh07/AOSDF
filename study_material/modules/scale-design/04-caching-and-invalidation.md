# Caching and invalidation

A **cache** keeps a reusable copy near the next reader. It reduces latency and work on an origin, but introduces a freshness contract. “Use a cache” is incomplete until the key, owner, lifetime, invalidation trigger, and behavior after a miss are defined.

## Choose the right layer

A CDN or edge cache is a good fit for public, immutable images and versioned JavaScript. Private document bodies require careful permission handling and usually should not be stored in a shared public cache. Browser caches can revalidate with `ETag` and `If-None-Match`; an unchanged representation can return `304 Not Modified`. An application cache might hold document metadata or a search result, keyed by tenant, viewer permissions, query, and data version. The key must encode all inputs that affect the result.

For document 42, a safe simple policy is: on a successful edit, increment `version` in the primary transaction; cache the body under `document:42:v7` instead of overwriting `document:42`. The response for version 8 uses a new key, so old cached bytes cannot masquerade as the new version. Old keys expire. A listing may tolerate a short TTL; the editor's immediate post-save read should use the primary or a session-aware path.

If many misses for the same popular key arrive together, all may hit the database: a **cache stampede**. Bound concurrent fills per key, use short stale-while-revalidate only where stale data is acceptable, and size the origin for a realistic miss storm. A 95% hit ratio at 1,160 RPS still sends about 58 requests/second to the origin; the number can jump to 1,160 when the cache is cold.

## Diagram: hit, miss, and version change

![A cache hit serves a versioned document; a miss reads the origin, and an edit creates a new versioned cache key.](/learning/scale-design/caching.svg)

```aosdf-diagram
GET doc v7 ──▶ cache v7 ── hit ──▶ response
                   └── miss ──▶ primary + object store ──▶ fill
EDIT doc ──▶ commit v8 ──▶ future reads use cache v8
```

## Implementation: put each cache at a deliberate boundary

Cloudflare Cache can keep public versioned assets at the edge. Redis can hold bounded application cache entries. NGINX can honor or generate HTTP cache headers at a controlled proxy boundary. The important engineering decision is the **cacheability rule**, not which logo sits on the architecture diagram.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![cloudflare logo](/learning/scale-design/logo-cloudflare.svg) | [Cloudflare Cache](https://developers.cloudflare.com/cache/get-started/) | Serve public immutable thumbnails and assets near readers. | Bypass shared caching for private document responses. |
| ![redis logo](/learning/scale-design/logo-redis.svg) | [Redis](https://redis.io/docs/latest/develop/use-cases/cache-aside/) | Store short-lived metadata or versioned derived results. | Include tenant, permission scope, and version in keys. |
| ![nginx logo](/learning/scale-design/logo-nginx.svg) | [NGINX proxy cache](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) | Control a proxy cache in self-hosted deployments. | Audit headers, cookie handling, and invalidation. |

For a fingerprinted public asset, an origin might send `Cache-Control: public, max-age=31536000, immutable`. For a private document body, use `Cache-Control: private, no-store` unless you have a reviewed private-cache contract. A Redis key like `doc:{tenant}:{id}:v{version}` avoids returning v7 as v8; permission-scoped results also need the viewer's authorization scope. Test permission revocation and cache outage explicitly before calling the path complete.

## Engineering exercise

Define cache keys and freshness for public thumbnails, a private document body, and a search result. For each, say what happens after permission revocation and during a cache outage.

## Design review questions

- Why can a high cache hit rate hide an origin capacity problem?
- What does an ETag help a browser avoid?
- Why is a URL alone an unsafe key for a permission-dependent result?

**Review criteria:** cold starts and stampedes send traffic to origin; revalidation can avoid retransmitting unchanged content; different viewers may be allowed to see different data.

## Read further

- [MDN: HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching)
- [MDN: ETag](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/ETag)
- [Cloudflare: cache invalidation](https://developers.cloudflare.com/cache/guides/invalidate-cache/)
