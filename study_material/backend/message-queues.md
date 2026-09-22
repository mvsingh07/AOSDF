---
concepts: [message-queue, pub-sub-pattern, event-driven-architecture]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: [event-driven-architecture]
interview_angle: >
  Be ready to explain the durability/ordering trade-off between a simple queue and a log-based
  system like Kafka, and why "at-least-once delivery" means consumers must be idempotent.
built_at: L6-T1
diagram: true
---

# Message Queues & Pub/Sub

## Definition

- **Message queue** (RabbitMQ, SQS): a producer places a message on a queue; one consumer picks it up
  and processes it — decouples producer and consumer in time (the consumer doesn't need to be running
  when the message is sent) and load (a slow consumer doesn't block the producer).
- **Pub/sub (publish-subscribe):** a producer publishes an event to a topic; every subscriber to that
  topic receives a copy — one event, many independent consumers, none of which know about each other.
- **At-least-once delivery:** most queue systems guarantee a message is delivered at least once, not
  exactly once — a consumer can receive the same message twice (e.g. after a delivery acknowledgment is
  lost). Consumers must be **idempotent** (processing the same message twice produces the same result as
  processing it once) to be safe under this guarantee.

## Example

```python
# Idempotent consumer — safe even if this message is redelivered
def handle_order_paid(event):
    if Order.objects.filter(id=event.order_id, status="paid").exists():
        return  # already processed — redelivery is a no-op, not a duplicate charge
    mark_order_paid(event.order_id)
```

## Diagram

```aosdf-diagram
Queue (point-to-point):        Pub/Sub (fan-out):
┌──────────┐   ┌───────┐        ┌──────────┐   ┌───────┐  Consumer A
│ Producer │──▶│ Queue │──▶ 1   │ Producer │──▶│ Topic │─▶
└──────────┘   └───────┘  consumer└──────────┘   └───────┘  Consumer B
                                                              (each gets a copy)
```

## Why This Matters for Reliability

This is what makes event-driven architecture (`study_material/principles/architecture-styles.md`)
resilient to a downstream service being temporarily down — the message waits on the queue instead of the
request simply failing — at the direct cost of the harder-to-trace, eventually-consistent flow that
architecture style already trades for that resilience.
