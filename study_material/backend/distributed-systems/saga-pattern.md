---
concepts: [saga-pattern, two-phase-commit]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [microservices-architecture, database-transactions]
interview_angle: >
  Be ready to explain why 2PC doesn't scale well across microservices (a coordinator failure blocks
  every participant holding locks) and how a saga trades that away for eventual consistency plus
  explicit compensating actions.
built_at: L6-T1
diagram: true
---

# Saga Pattern vs. Two-Phase Commit

## Definition

- **Two-Phase Commit (2PC):** a coordinator asks every participant to *prepare* (lock resources, confirm
  it can commit) — only once all participants say yes does the coordinator tell everyone to *commit*.
  Gives strong atomicity across multiple databases, but participants hold locks for the whole round trip,
  and a coordinator crash mid-protocol can leave participants blocked indefinitely holding those locks.
  Rarely used across independently-owned microservices for exactly this reason.
- **Saga pattern:** a sequence of local transactions, each in a different service, where every step has a
  matching **compensating transaction** that undoes it if a later step fails. No distributed lock is ever
  held across services — each local transaction commits immediately — trading strong atomicity for
  eventual consistency plus explicit, hand-written rollback logic.

## Example

An order saga: `ReserveInventory` → `ChargePayment` → `ScheduleShipping`. If `ChargePayment` fails after
`ReserveInventory` succeeded, the saga runs `ReserveInventory`'s compensating transaction
(`ReleaseInventory`) rather than rolling back a distributed transaction that never existed in the first
place:

```python
steps = [(reserve_inventory, release_inventory),
         (charge_payment, refund_payment),
         (schedule_shipping, cancel_shipping)]

completed = []
for do, undo in steps:
    try:
        do()
        completed.append(undo)
    except Exception:
        for undo_fn in reversed(completed):
            undo_fn()  # compensate everything that already succeeded
        raise
```

## Diagram

```aosdf-diagram
2PC:   Coordinator ──prepare──▶ A, B, C (all lock & vote) ──commit──▶ A, B, C (all commit together)
Saga:  Reserve Inventory ──▶ Charge Payment ──▶ Schedule Shipping
             │ (if a later step fails, run compensating actions in reverse)
             ▼
       Release Inventory ◀── Refund Payment ◀── Cancel Shipping
```

## Where This Connects

This is the practical, distributed-scale version of the same "all-or-nothing" goal Atomicity
(`study_material/backend/acid-transactions.md`) gives for free inside a single database — a saga is what
you reach for once "single database" is no longer true.
