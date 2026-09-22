---
concepts: [cache-stampede, cache-penetration, cache-avalanche]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [caching-strategies]
interview_angle: >
  These three are commonly confused with each other — be ready to distinguish them by *cause*
  (expired key vs. no key ever exists vs. mass simultaneous expiry), since the fix for each differs.
built_at: L6-T1
diagram: true
---

# Cache Failure Patterns: Stampede, Penetration, Avalanche

## Definition

- **Cache stampede (a.k.a. cache breakdown / dogpile effect):** a single, popular key expires, and a
  flood of concurrent requests all miss the cache at once and hammer the database simultaneously trying
  to recompute the same value.
- **Cache penetration:** requests for a key that **never exists** in the database at all (a malformed ID,
  or a deliberate attack) — every such request always misses the cache (there's nothing to cache) and
  always hits the database, bypassing the cache's protection entirely.
- **Cache avalanche:** many *different* keys expire at roughly the same time (e.g. they were all set with
  the same TTL at the same moment, like a bulk cache warm-up) — the database gets hit with a broad wave of
  misses across many keys at once, not just one hot key.

## Example

Stampede fix — a mutex/lock so only one request recomputes a hot key while others wait for the result:

```python
def get_product(id):
    if val := redis.get(f"product:{id}"):
        return val
    if redis.set(f"lock:product:{id}", 1, nx=True, ex=5):  # only one caller wins the lock
        val = db.query(Product, id=id)
        redis.set(f"product:{id}", val, ex=300)
        redis.delete(f"lock:product:{id}")
        return val
    time.sleep(0.05)
    return get_product(id)  # retry — most callers wait briefly for the winner's result
```

Penetration fix — cache the "not found" result too (a short-TTL negative cache), or a Bloom filter to
reject known-nonexistent IDs before ever touching the database.

Avalanche fix — add random jitter to TTLs (`ex=300 + random.randint(0, 60)`) so keys don't all expire in
the same instant.

## Diagram

```aosdf-diagram
Stampede:  1 key expires ──▶ N concurrent requests ──▶ N simultaneous DB queries for the SAME key
Penetration: key never exists ──▶ every request misses ──▶ every request hits DB, forever
Avalanche: many keys expire together ──▶ broad wave of misses ──▶ DB hit across MANY different keys
```
