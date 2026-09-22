---
concepts: [client-state-management, state-lifting, global-state-store]
concept_category: Frontend
difficulty: intermediate
prerequisites: [component-based-ui]
interview_angle: >
  Be ready to argue *against* reaching for a global store by default — "lift state up" to the
  nearest common ancestor is the right first move for most cases; a global store solves a specific
  pain (deeply nested prop drilling, state needed in unrelated branches), not every case.
built_at: L6-T1
diagram: false
---

# Client-Side State Management

## Definition

- **Local component state:** state that only one component (and maybe its direct children) needs —
  lives inside that component, dies when it unmounts. The correct default.
- **State lifting:** when two sibling components need the same state, move it up to their nearest common
  parent, which then passes it down as props — solves the immediate problem without introducing a global
  store.
- **Global state store** (Redux, Zustand, Context API, Vuex/Pinia): a single source of truth for state
  that's genuinely needed across many unrelated parts of the tree (logged-in user, theme, shopping cart)
  — avoids prop drilling (passing a prop through five layers of components that don't use it themselves,
  just to reach a deeply nested child).

## Example

Prop drilling problem:

```jsx
<App user={user}>
  <Layout user={user}>
    <Sidebar user={user}>
      <UserBadge user={user} />  {/* only this component actually needs `user` */}
```

Solved with a store/context instead — `UserBadge` reads `user` directly, no intermediate component needs
to know about it at all.

## The Trade-off

A global store makes data flow harder to trace at a glance (any component, anywhere, could be reading or
writing it) in exchange for solving the drilling problem — the same "convenience vs. traceability"
tension this framework resolves for task status via Principle 22 (one canonical record,
`execution_plan.md`, rather than state scattered and duplicated across files that can drift).
