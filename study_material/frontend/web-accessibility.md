---
concepts: [web-accessibility, wcag, semantic-html]
concept_category: Frontend
difficulty: fundamental
prerequisites: []
interview_angle: >
  Be ready with concrete examples beyond "add alt text" — keyboard-only navigation and screen-reader
  landmark structure are the ones that actually reveal whether you've tested with real assistive tech.
built_at: L6-T1
diagram: false
---

# Web Accessibility (a11y)

## Definition

**Accessibility** means a site is usable by people with disabilities — visual, auditory, motor, or
cognitive — typically via assistive technology (screen readers, keyboard-only navigation, voice control).
**WCAG (Web Content Accessibility Guidelines)** is the standard rubric, with three conformance levels
(A, AA, AAA — AA is the common legal/practical baseline). **Semantic HTML** — using `<button>` instead of
a styled `<div onclick>`, `<nav>`/`<main>`/`<header>` instead of generic `<div>`s — is the cheapest,
highest-leverage accessibility win: it gives assistive tech and keyboard navigation correct behavior for
free, with no ARIA attributes needed.

## Example

```html
<!-- Inaccessible: no keyboard focus, no screen-reader semantics, no click-via-Enter -->
<div onclick="submit()">Submit</div>

<!-- Accessible: native button gets focus, Enter/Space activation, and a screen reader
     announces it as "Submit, button" — for free -->
<button onclick="submit()">Submit</button>
```

A form image with `alt=""` is read as decorative (correct for a spacer image) — a real photo with no
`alt` text at all is announced as just "image," conveying nothing.

## Why It's Not Optional

Beyond the legal exposure (ADA/WCAG lawsuits are real and common), accessibility failures often reveal a
deeper UX problem for *everyone* — a low-contrast color scheme that fails WCAG AA is also just hard to
read in bright sunlight; a page that breaks with keyboard-only navigation often also breaks for anyone
whose mouse/trackpad is temporarily unavailable.
