---
concepts: [dead-letter-queue, outbox-pattern, idempotency]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [message-queue]
interview_angle: >
  Be ready to explain the specific bug the outbox pattern prevents (a DB commit succeeding but the
  matching event never being published, because a process crashed between the two separate calls) —
  this is the single most common "why isn't this durable" mistake in event-driven systems.
built_at: L6-T1
diagram: true
---

# Dead Letter Queue, Outbox Pattern & Idempotency

## Definition

- **Dead letter queue (DLQ):** a message that repeatedly fails processing (after N retries) is moved to a
  separate queue instead of being retried forever or silently dropped — lets the failure be inspected and
  reprocessed manually later, without blocking the main queue on one poison message.
- **Outbox pattern:** writing to a database *and* publishing an event about that write are two separate
  operations — if the process crashes between them, the database commit succeeds but the event is never
  published (or vice versa), a silent inconsistency. The outbox pattern writes the event into an
  `outbox` table in the **same transaction** as the business data change, then a separate publisher
  process reads unsent outbox rows and publishes them (often via change data capture,
  `change-data-capture.md`) — the event's existence is now atomic with the business write itself.
- **Idempotency:** processing the same message/request twice produces the same result as processing it
  once. Required because message queues typically only guarantee at-least-once delivery
  (`message-delivery-semantics.md`) — a consumer *will* see duplicates eventually, and must handle that
  safely, usually via an idempotency key checked against already-processed IDs.

## Example

```python
# Outbox pattern — event write is atomic with the business write
with db.transaction():
    order = create_order(...)
    db.execute("INSERT INTO outbox (event_type, payload) VALUES (%s, %s)",
               ("OrderCreated", order.to_json()))
# separate publisher process later reads unsent outbox rows and publishes them, then marks sent

# Idempotent consumer, keyed on a request/message ID
def handle(event):
    if ProcessedEvents.objects.filter(id=event.id).exists():
        return  # duplicate delivery — safe no-op
    process(event)
    ProcessedEvents.objects.create(id=event.id)
```

## Diagram

```aosdf-diagram
Without outbox:  DB write ──▶ [CRASH HERE] ──▶ publish event   ← event never sent, DB already committed
With outbox:     DB write + outbox row (1 transaction) ──▶ publisher reads outbox ──▶ publishes
                 (crash after the transaction still leaves the outbox row to publish later)
```

## Why These Three Together

They're the standard toolkit for building an event-driven system that's actually reliable end-to-end: the
outbox pattern guarantees an event is never silently lost at the source, idempotency guarantees a
consumer is safe when that same event is (correctly, per at-least-once semantics) delivered more than
once, and a DLQ guarantees a message that genuinely can't be processed doesn't block or get lost either.
