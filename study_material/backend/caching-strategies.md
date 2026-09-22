---
concepts: [caching-strategies, cache-invalidation]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: []
interview_angle: >
  Be ready to explain why write-through was chosen over write-back for a given scenario, and what
  happens to an in-flight write if the cache node fails mid-request — this exact example is the one
  used in framework.md's own Concept Frontmatter Standard illustration, worth recognizing.
built_at: L6-T1
diagram: true
---

# Caching Strategies & Cache Invalidation

## Definition

- **Cache-aside (lazy loading):** the application checks the cache first; on a miss, it reads from the
  database and populates the cache for next time. Simple, and the cache only ever holds data that's
  actually been requested — but the first request for any key is always slow (a "cold" cache miss).
- **Write-through:** every write goes to the cache *and* the database together, synchronously — reads are
  always fresh, at the cost of every write paying the cache-write latency too.
- **Write-back (write-behind):** a write goes to the cache immediately and is flushed to the database
  asynchronously later — fast writes, but a cache-node failure before the flush loses that write.
- **Cache invalidation:** the (famously hard) problem of knowing when cached data is stale and must be
  evicted or refreshed — "there are only two hard things in computer science: cache invalidation, naming
  things, and off-by-one errors."

## Example

```python
def get_user(user_id):
    cached = redis.get(f"user:{user_id}")
    if cached:
        return cached                      # cache-aside hit
    user = db.query(User, id=user_id)       # miss — go to the source of truth
    redis.set(f"user:{user_id}", user, ex=300)  # populate, 5-minute TTL
    return user
```

## Diagram

```aosdf-diagram
┌─────────┐  1. read   ┌─────────┐  2. miss   ┌──────────┐
│  Client  │───────────▶│  Cache  │───────────▶│ Database │
└─────────┘            └────┬────┘            └────┬─────┘
                              │ 3. populate cache    │
                              ◀──────────────────────┘
```

## Why This Is the Same Concept Everywhere

This is the exact `caching-strategies`/`cache-invalidation` concept pair `framework.md`'s own Concept
Frontmatter Standard section uses as its illustrative example — and the same ID, `caching-strategies`,
recurs on `study_material/frontend/web-performance.md` deliberately: it's the same underlying idea
(reuse a previous result instead of recomputing/refetching it) whether it's a browser HTTP cache or a
backend Redis layer, and `concept_indexer_agent`'s dedupe step (step 2, `concept_indexer_agent.md`) is
designed to merge exactly this kind of cross-document recurrence into one node with two source links.
