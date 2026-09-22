---
concepts: [unit-testing, integration-testing, e2e-testing, tdd]
concept_category: Testing
difficulty: fundamental
prerequisites: []
interview_angle: >
  Be ready to justify the pyramid's shape (why fewer E2E tests, not zero) with a concrete cost
  argument — flakiness and runtime, not just "best practice."
built_at: L6-T1
diagram: true
---

# The Testing Pyramid

## Definition

- **Unit tests:** test one function/class in isolation, dependencies mocked/stubbed. Fast (milliseconds),
  cheap to write, precise about *what* broke — should be the largest layer by count.
- **Integration tests:** test how multiple real components work together (e.g. a service against a real
  test database) — catch issues unit tests can't (wrong SQL, serialization mismatches), slower and
  fewer in number.
- **E2E (end-to-end) tests:** drive the whole system through its real interface (a browser, a full API
  call chain) — highest confidence that the system actually works for a user, but slow, flaky (network,
  timing), and expensive to maintain — should be the smallest layer by count.
- **TDD (Test-Driven Development):** write a failing test first, then the minimum code to pass it, then
  refactor. A workflow discipline, not a test *type* — orthogonal to the pyramid, but commonly taught
  alongside it.

## Example

```python
# Unit test — mocks the database entirely
def test_calculate_discount():
    assert calculate_discount(price=100, percent=10) == 90

# Integration test — hits a real (test) database
def test_order_service_creates_order(test_db):
    service = OrderService(db=test_db)
    order = service.create_order(user_id=1, items=[...])
    assert test_db.query(Order).count() == 1
```

## Diagram

```aosdf-diagram
        ╱╲
       ╱E2E╲          few, slow, high confidence
      ╱──────╲
     ╱Integration╲    moderate count, moderate speed
    ╱──────────────╲
   ╱   Unit Tests    ╲  many, fast, cheap
  ╱────────────────────╲
```

## Why the Shape, Not Just the Name

An inverted pyramid (mostly E2E tests, few unit tests) is a real, common anti-pattern: the test suite
becomes slow and flaky, and a failure gives almost no information about *where* the bug is — you get a
failing checkout flow, not a failing `calculate_discount`. This framework's own `AOSDF-Hosting` project
follows the standard shape: `pytest -q` runs a large unit/integration suite fast on every change, with no
browser-driven E2E layer yet at MVP scale.
