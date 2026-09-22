---
concepts: [csr, ssr, ssg, isr]
concept_category: Frontend
difficulty: intermediate
prerequisites: [dom]
interview_angle: >
  Know the real trade-off axis: time-to-first-byte and SEO vs. server cost and build complexity —
  not just the acronyms. Be ready to pick the right one for a stated scenario (e.g. a marketing
  site vs. a real-time dashboard).
built_at: L6-T1
diagram: true
---

# Rendering Strategies: CSR, SSR, SSG, ISR

## Definition

- **CSR (Client-Side Rendering):** the server sends a near-empty HTML shell + a JS bundle; the browser
  runs the JS to build the page. Fast subsequent navigation, but a blank screen until JS loads and runs —
  and poor SEO unless crawlers execute JS.
- **SSR (Server-Side Rendering):** the server renders full HTML for each request and sends it already
  populated — fast first paint, good SEO, but every request costs server compute time.
- **SSG (Static Site Generation):** HTML is rendered once, at *build* time, and served as static files
  from a CDN — the fastest possible response, but content is only as fresh as the last build (this
  framework's own MkDocs-based Project Docs Site, `docs_site_agent`, is exactly this model).
- **ISR (Incremental Static Regeneration):** SSG's speed, but pages are regenerated in the background
  after a set time or on-demand — avoids a full rebuild for every content change while staying mostly
  static.

## Example

A marketing landing page: SSG is usually correct — content rarely changes, and a CDN-served static file
beats any dynamic rendering on cost and speed. A logged-in dashboard showing live account data: SSR or
CSR, since SSG can't know per-user content at build time.

## Diagram

```aosdf-diagram
CSR:  Request ─▶ Empty HTML + JS bundle ─▶ Browser runs JS ─▶ Page appears
SSR:  Request ─▶ Server renders HTML now ─▶ Full page sent ─▶ Page appears
SSG:  Build time: render once ─▶ CDN serves static file ─▶ Request ─▶ Page appears (fastest)
ISR:  Like SSG, but regenerated in the background after N seconds or on-demand
```

## Where AOSDF Uses This

Track P's Project Docs Site and `AOSDF-Hosting`'s deployed marketing site are both SSG — built once
(`mkdocs build`), served as static files, rebuilt only on a deliberate human trigger (Principle 24), never
regenerated per-request.
