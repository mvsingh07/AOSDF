---
concepts: [dom, critical-rendering-path]
concept_category: Frontend
difficulty: fundamental
prerequisites: []
interview_angle: >
  Be ready to walk through the critical rendering path step by step for a real page load, and name
  one concrete optimization for each stage (e.g. why render-blocking CSS in <head> matters).
built_at: L6-T1
diagram: true
---

# The DOM & Critical Rendering Path

## Definition

The **DOM (Document Object Model)** is the browser's in-memory tree representation of an HTML document —
JavaScript reads/mutates it to change what's on screen. The **critical rendering path** is the sequence
of steps a browser takes to turn HTML/CSS/JS into pixels: parse HTML → build the DOM tree → parse CSS →
build the CSSOM → combine both into the **render tree** (only visible nodes) → **layout** (compute
position/size of every node) → **paint** (fill in pixels).

## Example

```html
<link rel="stylesheet" href="style.css">  <!-- render-blocking: browser waits for this before painting -->
<script src="app.js"></script>            <!-- parser-blocking by default, unless async/defer -->
```

Moving `<script>` to the end of `<body>`, or adding `defer`, lets the browser finish building the DOM
before running JS that might otherwise block parsing mid-document — a real, measurable page-load
improvement, not a stylistic preference.

## Diagram

```aosdf-diagram
HTML ──parse──▶ DOM Tree ──┐
                            ├──combine──▶ Render Tree ──▶ Layout ──▶ Paint
CSS ───parse──▶ CSSOM ──────┘
```

## Why It Matters Beyond Trivia

Every "why is my page slow" investigation traces back to one of these stages — a render-blocking
stylesheet delays first paint; a layout thrashing loop (reading `offsetHeight` then writing a style, in a
tight loop) forces the browser to redo layout synchronously, repeatedly. See
`study_material/frontend/web-performance.md` for the optimization side of this.
