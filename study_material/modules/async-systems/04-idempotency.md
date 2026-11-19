# Idempotency and delivery guarantees

An at-least-once broker may deliver the same logical job more than once. A worker can also finish its work and crash before acknowledging the message. Design the **effect** to be safe under repetition rather than equating one delivery with one action.

## Name the logical effect

In the export example, `operationId` is stable across retries. Use it to name the output object, such as `exports/exp_82/result.pdf`, and to guard the status transition. The `jobId` or broker receipt may change; neither is a suitable deduplication key for the business operation.

An idempotent result write can follow this outline:

```text
claim operation exp_82
if status == succeeded: acknowledge existing result
if status == cancelled: acknowledge without new effect
acquire a bounded processing claim for exp_82
create result at deterministic key or staging key
commit result reference and succeeded state conditionally
acknowledge message
```

The processing claim prevents ordinary overlap, but its lease can expire. The final result write still needs a uniqueness or conditional-update rule. If creating the file has a non-repeatable side effect, use a provider idempotency key when available and retain the provider's result ID. A local “processed” flag alone cannot atomically guarantee what an external provider did.

## Diagram: the lost acknowledgement

![Worker A completes an export but loses its acknowledgement; Worker B sees the existing result after redelivery and acknowledges without creating a second file.](/learning/async-systems/idempotency.svg)

```aosdf-diagram
Worker A ──▶ writes exports/exp_82/result.pdf ──▶ commits succeeded
                                         │
                                         └── crash before queue ack
Queue ──▶ redelivers exp_82 ──▶ Worker B sees succeeded ──▶ ack only
```

[Explore the full queue delivery diagram](/queue-delivery-lifecycle.archify.html) and look at the gap between applying an effect and acknowledgement.

## Be precise about guarantees

**At-most-once** processing can lose work but avoids broker-driven repeats. **At-least-once** prioritizes retry after uncertainty and requires duplicate-safe consumers. “Exactly once” claims usually apply within a narrow subsystem or transaction boundary; they do not magically cover an external API, object store, and database together. Describe the actual observable effect: for example, “one downloadable export per operation ID, despite duplicate queue delivery.”

Ordering is a separate concern. A standard queue may deliver out of order. If two jobs update the same document, use a version or sequence check so an older export request cannot overwrite a newer result. A FIFO queue can help with broker order, but it does not replace state validation.

## Try it

Trace two workers that receive `exp_82` concurrently. One completes while the other's claim expires. Write the unique key or conditional update that prevents two visible files, and explain what changes if the worker also charges a credit card.

## Check your understanding

- Why should deduplication use `operationId` instead of the delivery receipt?
- What happens after a successful effect but lost acknowledgement?
- Why is a local processed flag insufficient for an external payment?

**Answer guide:** the operation remains the same across deliveries; the job can be redelivered; the database and external provider may disagree unless the provider offers an idempotency contract or reconciliation path.

## Read further

- [Amazon SQS standard queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html)
- [Amazon SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)
