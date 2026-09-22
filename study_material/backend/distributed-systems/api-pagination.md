---
concepts: [api-pagination]
concept_category: API Design
difficulty: intermediate
prerequisites: [database-indexing]
interview_angle: >
  Be ready to explain why offset pagination gets slow and inconsistent at high page numbers, and
  why cursor pagination fixes both problems.
built_at: L6-T1
diagram: false
---

# API Pagination

## Definition

- **Offset pagination:** `?page=5&limit=20` → `OFFSET 80 LIMIT 20`. Simple, supports jumping to an
  arbitrary page, but has two real problems at scale: the database still has to scan and discard the
  first 80 rows every time (gets slower as the offset grows), and if a row is inserted/deleted while a
  user is paging through, they can see a duplicate or skip a row entirely (the "page" is really just a
  moving window over data that's changing underneath it).
- **Cursor-based (keyset) pagination:** `?after=<last_seen_id>&limit=20` →
  `WHERE id > <last_seen_id> ORDER BY id LIMIT 20`. Every page query uses an index seek to a specific
  point, not a scan-and-discard — consistently fast regardless of how deep into the results you are, and
  immune to the insert/delete skew problem since it's anchored to an actual row, not a numeric position.

## Example

```sql
-- Offset: slow at high page numbers, and unstable if rows change between page requests
SELECT * FROM orders ORDER BY created_at DESC OFFSET 10000 LIMIT 20;

-- Cursor: fast at any depth, stable regardless of concurrent inserts/deletes
SELECT * FROM orders WHERE created_at < :last_seen_created_at ORDER BY created_at DESC LIMIT 20;
```

## The Trade-off

Cursor pagination can't jump to an arbitrary page number ("go to page 47") — it only supports
"next"/"previous" relative to a cursor, which is why most public APIs (Stripe, GitHub, Twitter) use it for
list endpoints, while offset pagination stays common in admin UIs where jumping to a specific page number
is a real, needed feature and the underlying tables are small enough that offset's cost never becomes
visible.
