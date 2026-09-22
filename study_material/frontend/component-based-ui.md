---
concepts: [component-based-ui, virtual-dom, unidirectional-data-flow]
concept_category: Frontend
difficulty: intermediate
prerequisites: [dom]
interview_angle: >
  Be ready to explain *why* a virtual DOM diff is usually faster than naive direct DOM manipulation
  in a UI with frequent updates, and to name a case where it isn't (a single, targeted update).
built_at: L6-T1
diagram: false
---

# Component-Based UI, Virtual DOM, and Unidirectional Data Flow

## Definition

- **Component-based UI:** the interface is built from small, self-contained, reusable pieces
  (components), each owning its own markup, styling, and behavior, composed into a tree to form the full
  page (React, Vue, Angular, Svelte all share this model, differing mainly in *how* they update the DOM).
- **Virtual DOM:** a lightweight in-memory representation of the UI tree. On a state change, the
  framework builds a new virtual tree, **diffs** it against the previous one, and applies only the
  minimal set of real DOM mutations needed — real DOM writes are the expensive operation, so batching and
  minimizing them is the whole point.
- **Unidirectional data flow:** data flows one direction — parent to child via props — and a child
  changes state by calling a function the parent gave it, never by mutating the parent's data directly.
  Makes state changes traceable: any given piece of UI state has exactly one place it's modified from.

## Example

```jsx
function Cart({ items, onRemove }) {
  return items.map(item => (
    <CartItem key={item.id} item={item} onRemove={() => onRemove(item.id)} />
    // data flows down (item), events flow up (onRemove) — never a direct child→parent mutation
  ));
}
```

Changing `items` in the parent triggers a re-render; the framework diffs the new virtual tree against
the old one and patches only the DOM nodes that actually changed — not the whole list.

## Where This Connects

This is the same underlying discipline as this framework's Principle 26 ("tooling is a client of the
files, never a second source of truth") applied at UI scale: state lives in exactly one place (the
component tree's state, analogous to `execution_plan.md`'s Status column), and every view is a derived,
regenerable rendering of it — never an independently-mutable copy.
