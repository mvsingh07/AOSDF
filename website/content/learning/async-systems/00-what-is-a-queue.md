# What a queue is and when to use one

You click **Export document**. Creating the file may take a minute, but the website can respond immediately: “Your export has started.” How can it finish the work after the response? It can place an export job in a **queue** for a background worker to process.

## The basic idea

A queue holds messages representing work that has not yet been completed. One part of a system **produces** a message; another part **consumes** it. A queue service, often called a **broker**, stores and delivers messages between them. The producer and consumer do not have to run at the same time or at the same speed.

| Term | Plain meaning | Export example |
| --- | --- | --- |
| Producer | Adds work | The export API |
| Message or job | A description of work | “Generate export `exp_82`” |
| Queue or broker | Holds and delivers waiting work | An export-jobs queue |
| Consumer or worker | Takes work and performs it | A process that creates the file |
| Result store | Records what happened | An export status row and file reference |

The queue normally holds a **small instruction or reference**, not the entire document. The worker uses the export ID to load the current inputs and records the result where the website can find it. The queue and the result store have different jobs: the queue transports work; the result store answers “what happened to my export?”

## Diagram: one request, two paths

![An export request enters an API, an export job waits in a queue, and a worker creates the file while the user continues.](/learning/async-systems/queue-basics.svg)

```aosdf-diagram
User ──▶ Export API ──▶ Queue ──▶ Worker ──▶ File + completed status
           │
           └──▶ “Started: exp_82” ──▶ User checks status later
```

The upper path performs the work in the background. The lower path lets the user continue without waiting for file creation. [Open the full delivery and recovery diagram](/queue-delivery-lifecycle.archify.html) when you are ready to inspect failures and acknowledgements.

## Why use a queue?

**Keep slow work off the request path.** If a file takes a minute to generate, keeping the browser request open can time out or tie up server capacity. The API can return an operation ID after it has safely accepted the request.

**Absorb short bursts.** If 200 people request exports at once and workers can handle 20 at a time, the queue holds the rest. This buys time; it does not increase processing capacity. If arrivals stay high, waiting time grows, as lesson 3 calculates.

**Separate responsibilities.** The API handles validation and acceptance; workers handle file creation. They can be deployed and scaled independently. A worker failure does not have to erase an accepted request, provided the job and its state are stored durably.

**Retry uncertain failures.** A worker can try again after a temporary file-store outage. Repeating work may also repeat an effect, so later lessons add bounded retries and idempotency.

Queues also help with image processing, email delivery, imports, and scheduled jobs. The same concept can connect services, though a **work queue** and **publish-subscribe event** have different ownership: one task needs a worker to complete it, while an event may inform several independent subscribers.

## When is a direct call simpler?

Use a direct request when the caller needs the result now, the work is consistently quick, and a separate failure or progress state would add unnecessary complexity. For example, checking whether a form field is valid usually belongs in the request. Use a queue when the user can receive an operation ID and come back for the result, or when a background task can safely proceed without holding the request open.

Ask three questions before adding a queue:

1. Can the caller continue without the completed result?
2. Where will the caller see success or failure later?
3. What happens if the same job is delivered again?

If you cannot answer the second question, the queue may hide failed work. If you cannot answer the third, retries may cause duplicate effects.

## A first professional check

The waiting-line analogy is useful, but it has limits. Some brokers do not promise strict first-in-first-out order, and a message may be delivered again after a worker crash or lost acknowledgement. For example, Amazon SQS **standard queues** use at-least-once delivery and can deliver messages out of order. Define the exact guarantees your chosen broker provides, then make the worker safe when those guarantees are weaker than your business promise.

## Try it

Choose one task from **password check**, **generate a PDF**, **resize uploaded images**, and **show an account balance**. Decide whether the user needs an immediate result or can receive an operation ID. For a queued task, name its producer, message, queue, worker, and result store. Write the status the user sees if the worker fails.

## Check your understanding

- Does putting a job in a queue mean it has finished?
- If a queue fills faster than workers process jobs, what grows?
- Why should the result be stored outside the queue?
- Does “first in line” always mean “first completed”?

**Answer guide:** no, the job is waiting or being processed; backlog and waiting time grow; a status store makes the outcome queryable after the message is consumed; concurrent workers and broker semantics can change completion order.

## Read further

- [AWS decision guide: SQS, SNS, or EventBridge](https://docs.aws.amazon.com/decision-guides/latest/decision-guides/sns-or-sqs-or-eventbridge.html)
- [Amazon SQS standard queues and delivery semantics](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html)
