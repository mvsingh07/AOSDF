---
concepts: [web-performance, lazy-loading, code-splitting, caching-strategies]
concept_category: Frontend
difficulty: intermediate
prerequisites: [critical-rendering-path]
interview_angle: >
  Name a specific Core Web Vital (LCP, INP, CLS) and one concrete fix for it — "make it faster" is
  not an answer an interviewer accepts.
built_at: L6-T1
diagram: false
---

# Web Performance

## Definition

- **Code splitting:** ship only the JS a route actually needs, loading the rest on demand — instead of
  one giant bundle every visitor downloads regardless of which page they land on.
- **Lazy loading:** defer loading a resource (an image below the fold, a component not yet visible)
  until it's actually needed.
- **Caching strategies:** reuse a previous response instead of re-fetching — browser HTTP caching
  (`Cache-Control` headers), a CDN edge cache, or an application-level cache (see
  `study_material/backend/caching-strategies.md` for the backend-side version of the same concept — the
  same ID intentionally, since it's the same underlying idea from two angles).
- **Core Web Vitals** (Google's standardized UX metrics): **LCP** (Largest Contentful Paint — how fast
  the main content appears), **INP** (Interaction to Next Paint — how responsive the page feels to
  input), **CLS** (Cumulative Layout Shift — how much content unexpectedly jumps around while loading).

## Example

```jsx
// Without code splitting: every visitor downloads the admin panel's JS, even if they never see it
import AdminPanel from "./AdminPanel";

// With code splitting: AdminPanel's JS only loads when this route is actually visited
const AdminPanel = lazy(() => import("./AdminPanel"));
```

```html
<img src="hero.jpg" loading="lazy" width="800" height="400">
<!-- loading="lazy" defers offscreen images; explicit width/height reserves layout space,
     preventing a CLS-causing jump when the image finishes loading -->
```

## Why It's Measured, Not Guessed

Performance work without a metric is guesswork — Lighthouse/Chrome DevTools' Performance panel gives
concrete before/after numbers for each Core Web Vital, the same "prove it, don't assume it" discipline
this framework applied when evaluating Archify's actual output (`R3`) rather than trusting its README.
