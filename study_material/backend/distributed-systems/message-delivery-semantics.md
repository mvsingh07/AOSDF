---
concepts: [at-least-once-delivery, at-most-once-delivery, exactly-once-processing]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: [message-queue, idempotency]
interview_angle: >
  Be ready to say plainly that "exactly-once delivery" over an unreliable network is impossible in
  the strict sense — what systems actually offer is at-least-once delivery plus idempotent
  processing, which behaves like exactly-once from the consumer's point of view.
built_at: L6-T1
diagram: false
---

# Message Delivery Semantics

## Definition

- **At-most-once delivery:** a message is sent once, with no retry — if it's lost in transit or the
  consumer crashes before processing it, it's simply gone. Simple, but silently loses messages under
  failure — rarely acceptable for anything that matters.
- **At-least-once delivery:** the sender keeps redelivering until it receives an acknowledgment — no
  message is ever silently lost, but a consumer **will** occasionally see the same message more than
  once (e.g. it processed the message but crashed before the acknowledgment reached the sender). The most
  common real-world guarantee (SQS, RabbitMQ, Kafka's default consumer behavior).
- **Exactly-once processing:** the *effect* of a message is applied exactly once, even though the message
  itself might be delivered more than once. This is not solved at the delivery layer — it's achieved by
  combining at-least-once delivery with an **idempotent** consumer
  (`reliable-messaging-patterns.md`), so redelivery is a safe no-op rather than a duplicate effect.

## Example

```python
# At-least-once delivery + idempotent handling ≈ exactly-once processing, from the effect's point of view
def handle_payment_event(event):
    if PaymentLedger.objects.filter(idempotency_key=event.id).exists():
        return  # already applied — redelivery is a no-op
    charge_card(event.amount)
    PaymentLedger.objects.create(idempotency_key=event.id, amount=event.amount)
```

## Why "True" Exactly-Once Delivery Doesn't Exist

This traces back to the **Two Generals' Problem** — over an unreliable network, a sender can never be
100% certain whether its message was received (an acknowledgment can be lost just as easily as the
original message), so it can never safely decide "send exactly once and never retry" without risking
silent loss. The practical resolution the industry actually uses is at-least-once delivery paired with
idempotent processing, not a delivery mechanism that magically guarantees exactly one delivery.
