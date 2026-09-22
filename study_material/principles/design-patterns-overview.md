---
concepts: [singleton-pattern, factory-pattern, observer-pattern, strategy-pattern, decorator-pattern]
concept_category: Software Design
difficulty: intermediate
prerequisites: [solid-principles]
interview_angle: >
  Interviewers usually care less about naming the pattern and more about recognizing it in existing
  code and knowing its trade-off. Be ready to say when a pattern is overkill for the problem size.
built_at: L6-T1
diagram: false
---

# Common Design Patterns (GoF, Selected)

## Definition

Five frequently-asked "Gang of Four" patterns, each solving a distinct recurring problem:

- **Singleton** — ensure a class has exactly one instance, globally accessible. Overused in practice;
  it's effectively global mutable state and makes testing harder (hidden shared dependency).
- **Factory** — delegate object creation to a method/class instead of calling a constructor directly,
  so the caller doesn't need to know the concrete type being created.
- **Observer** — one object (subject) notifies a list of dependents (observers) automatically when its
  state changes, without the subject knowing anything about who's listening.
- **Strategy** — define a family of interchangeable algorithms, select one at runtime, without the
  calling code branching on type.
- **Decorator** — wrap an object to add behavior dynamically, without subclassing or modifying the
  original class.

## Example

Strategy pattern, replacing a branching mess:

```python
# Before: every new discount type means editing this function
def apply_discount(order, type):
    if type == "percentage": ...
    elif type == "flat": ...

# After: each strategy is its own class implementing a shared interface
class PercentageDiscount:
    def apply(self, order): ...

class FlatDiscount:
    def apply(self, order): ...

order.discount_strategy.apply(order)  # caller never branches on type
```

Observer pattern is the same shape as a pub/sub event bus, or a UI framework re-rendering a component
when its subscribed store changes (see `study_material/frontend/state-management.md`).

## Where AOSDF Uses This Shape

`tracker_sync_agent`'s `TrackerAdapter` and `AOSDF-Hosting`'s `DeploymentProvider` (Principle 25) are
both Strategy pattern in practice — one interface, several interchangeable implementations, selected by
config rather than a hard-coded branch.
