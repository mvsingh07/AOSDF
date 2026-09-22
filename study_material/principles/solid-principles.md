---
concepts: [solid-principles]
concept_category: Software Design
difficulty: fundamental
prerequisites: []
interview_angle: >
  Be ready to name all five, explain each with a one-line example, and — more importantly —
  explain a real case where blindly applying one (usually Single Responsibility or Open/Closed)
  produced worse code than a simpler, less "correct" design would have.
built_at: L6-T1
diagram: false
---

# SOLID Principles

## Definition

SOLID is five object-oriented design guidelines, coined by Robert C. Martin, aimed at producing code
that's easier to change without breaking unrelated things:

- **S — Single Responsibility:** a class/module should have exactly one reason to change.
- **O — Open/Closed:** open for extension, closed for modification — add new behavior via new code,
  not by editing existing, tested code.
- **L — Liskov Substitution:** a subtype must be usable anywhere its base type is expected, without
  breaking the caller's assumptions.
- **I — Interface Segregation:** many small, client-specific interfaces beat one large general-purpose
  one — no client should depend on methods it doesn't use.
- **D — Dependency Inversion:** depend on abstractions, not concretions — high-level modules shouldn't
  import low-level implementation details directly.

## Example

Violating Dependency Inversion:

```python
class EmailNotifier:
    def send(self, msg): ...

class OrderService:
    def __init__(self):
        self.notifier = EmailNotifier()  # hard-wired to one concrete implementation
```

Applying it:

```python
class Notifier(Protocol):
    def send(self, msg: str) -> None: ...

class OrderService:
    def __init__(self, notifier: Notifier):
        self.notifier = notifier  # any Notifier — email, SMS, push — can be swapped in
```

This is the exact same shape as this framework's own `DeploymentProvider`/`TrackerAdapter` pattern
(Principle 25) — one interface, swappable concrete implementations, no rewrite of the caller to add a
new provider.

## Where This Bites in Practice

SOLID is guidance, not law. Applying Single Responsibility too aggressively produces a maze of tiny
classes that are individually simple but collectively hard to trace — a common, real interview follow-up
is "when have you *not* followed SOLID, and why was that the right call?"
