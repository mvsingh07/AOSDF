---
concepts: [rest-api, graphql-api]
concept_category: API Design
difficulty: fundamental
prerequisites: []
interview_angle: >
  Don't present GraphQL as strictly better — name over-fetching/under-fetching as REST's real pain
  point, and name GraphQL's real cost (caching is harder, query complexity can be abused for a
  denial-of-service-shaped attack if unguarded).
built_at: L6-T1
diagram: false
---

# REST vs GraphQL

## Definition

- **REST (Representational State Transfer):** resources are addressed by URL, manipulated via HTTP verbs
  (GET/POST/PUT/DELETE). Simple, cacheable by standard HTTP semantics, but a client often either
  **over-fetches** (gets fields it doesn't need) or **under-fetches** (needs a second request to get
  related data) — a mobile screen showing just a user's name might still receive their entire profile
  object.
- **GraphQL:** a single endpoint where the client specifies exactly which fields it needs, across
  potentially multiple related resources, in one request. Solves over/under-fetching directly, at the
  cost of losing REST's simple HTTP-cache-by-URL model and needing its own query-complexity/depth
  limiting to prevent an expensive nested query from overloading the server.

## Example

REST — two requests to get a user and their recent orders:

```
GET /users/42          → { id, name, email, address, bio, ... }  (fields the client may not need)
GET /users/42/orders
```

GraphQL — one request, exact fields:

```graphql
query {
  user(id: 42) {
    name
    orders(limit: 5) { id, total }
  }
}
```

## When Each Is the Right Call

REST is usually the simpler, right default — most APIs don't have GraphQL's over/under-fetching pain
badly enough to justify the added complexity (schema, resolvers, query-cost guarding). GraphQL earns its
keep when a product genuinely has many different clients (web, iOS, Android) each needing different
shapes of the same underlying data.
