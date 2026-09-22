# Hosting Registry Schema
# AOSDF v3.0 — Track H (Internal Product Hosting, Own Products Only)
# Read this before building or operating the Track H build pipeline (`H0`).

---

## Why This Exists

Track H hosts AOSDF's own products (Bidium, Comms-Engine/Supagram, AOSDF itself, and whatever else
gets added later) at a shareable link, reusing the exact `mkdocs build` step `docs_site_agent` already
runs locally. Per `aosdf_expansion_scope_2.md` §0/§4, this is **internal, own-products-only hosting** —
there is one owner, not many tenants, so this schema deliberately has no `tenants`, `users`, or billing
tables. If a multi-tenant SaaS layer (`HX`, currently `Deferred`) is ever revisited, a `tenant_id`
column can be added to `products` later without a redesign — it is not designed in now.

This document fixes the two tables the build pipeline reads and writes. It does not define the pipeline
mechanics themselves (see `aosdf_expansion_scope_2.md` §4 "Build pipeline mechanics") or the deployment
backend (`OD-H2`, resolved — Vercel, see Section 3 below).

---

## 1. `products`

One row per registered product. Registration is a manual, human-triggered action — no product is
auto-discovered or auto-enrolled (Principle 24).

| Field | Type | Purpose | Must Never |
| --- | --- | --- | --- |
| `id` | string (slug) | Stable identifier, used in the hosted URL path | Change once a build has been served at a URL using it |
| `display_name` | string | Human-readable name shown on the hosted page | — |
| `repo_url` | string (URL) | Source repo to clone at build time | Be treated as anything other than opaque input to a build — never parsed for task status (Principle 26) |
| `subfolder` | string, optional | Path within the repo to the `{project_name}-Documents/` root (where `mkdocs.yml` lives) | — |
| `access_method` | enum: `public` \| `deploy_key` | How the worker authenticates to fetch the repo | Ever be `write` or `push` scoped — read-only, always (Principle 34) |
| `latest_build_status` | enum: `never_built` \| `building` \| `success` \| `failed` | Denormalized display only | Be treated as authoritative if it disagrees with the latest row in `builds` — `builds` is the source of truth, this is a cache reconciled on read (Principle 31) |
| `latest_build_url` | string (URL), optional | Shortcut to the most recent successful build's output | — |

**Deliberately not modeled here:** `tenant_id`, `owner_user_id`, `plan`, `billing_*` — no multi-tenant
or billing concept exists in this schema (see "Why This Exists" above).

---

## 2. `builds`

One row per build attempt. Append-only — a build is never edited after it completes, only superseded by
a newer row for the same product (Principle 32: a hosted build is a point-in-time snapshot).

| Field | Type | Purpose | Must Never |
| --- | --- | --- | --- |
| `id` | string (UUID) | Build identifier | — |
| `product_id` | string | Foreign key to `products.id` | — |
| `triggered_at` | timestamp | When the human clicked Build (or, once `H2` ships, when the opt-in webhook fired) | Be set by anything other than a human action or an explicitly opted-in webhook (Principle 24) |
| `status` | enum: `queued` \| `building` \| `success` \| `failed` | Build lifecycle state | — |
| `log` | text | Raw build output, verbatim | Be paraphrased, truncated silently, or summarized — surfaced exactly as `mkdocs build`/the worker emitted it, matching `docs_site_agent`'s existing discipline |
| `output_url` | string (URL), optional | Where the static output was published (only set on `success`) | — |
| `docs_present` | boolean | Whether a Project Docs Site was found and built | — |
| `learn_present` | boolean | Whether a Track L `render/index.html` was found in the same fetch and hosted alongside | — |

**Deliberately not modeled here:** anything from `execution_plan.md`, `identified_gaps.md`, or
`project_status.md`. The `H1` Status tab re-parses those files fresh from the fetched repo on every
build rather than this table ever caching or owning task/gap status (Principle 22, 26, 31, and the new
Principle 35 once ratified — see `aosdf_expansion_scope_2.md` §4).

---

## 3. Repo Access (`OD-H3`, resolved 2026-09-02)

**One fine-grained GitHub PAT per registered repo** — read-only `Contents` permission, scoped to
exactly that one product's repo, rotated on GitHub's enforced expiration schedule. Not a single shared
deploy key/PAT covering every registered product (the earlier draft's guess), and not a full GitHub App.

The `products.access_method` field's `deploy_key` value therefore means "a per-product PAT is
configured," stored per product (e.g. `{product_id}.token`, gitignored, read only by the build worker
at clone time — same handling precedent as `tracker_config.env`, see `tracker_mapping.md` §2a), not one
credential shared across the whole registry.

**Why per-product rather than shared, even with a single owner:** a single owner removes the need for
*tenant* isolation, but not *blast-radius* isolation — a compromised build sandbox or a leaked build log
with a shared credential would expose every registered repo at once, which is exactly what Principle 34
("a hosted build never executes with more trust than the least-trusted input it consumes") argues
against. A per-product PAT means each build's sandbox only ever holds the credential for the one repo
it's cloning.

**Why not a GitHub App:** short-lived installation tokens and no long-lived secret at rest are the
better answer at real scale, but the setup complexity isn't justified for a handful of internal repos at
MVP — consistent with `aosdf_expansion_scope_2.md` §0 cutting the equivalent complexity (OAuth,
multi-tenant auth) elsewhere in this same scope.

---

## 4. Deployment Backend (`OD-H2`, resolved 2026-09-01)

**Vercel's REST API**, behind a `DeploymentProvider` interface (mirrors `TrackerAdapter` in
`tracker_mapping.md` §1 / Principle 25) — confirmed technically viable: MkDocs + Material deploys to
Vercel via a `requirements.txt` (`mkdocs`, `mkdocs-material`, `pymdown-extensions`) plus a build command
(`pip install -r requirements.txt && mkdocs build -d public`) with `outputDirectory` set accordingly;
multiple working reference deployments exist using this exact pattern. See the Decision & Sign-Off
Record entry for `OD-H2` in `execution_plan.md` Section 6 for the full reasoning and sources.

One gap not yet verified: the reference examples are single-repo, git-integration deployments
configured once, not the per-product, API-driven provisioning `H0` needs (one deployment created
programmatically per registered product). `H0-T2` includes a spike to confirm the API-driven path
before this is treated as fully proven end to end.
