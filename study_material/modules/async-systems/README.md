# Queues and reliable delivery

A queue is a place to hold work until a worker is ready to process it. For example, a website can accept a document export request, put an export job in a queue, and let a background worker create the file while the user continues using the site. This module begins with that basic flow, then explains the failure and scaling decisions needed to run it reliably.

## Start here: what is a queue?

Think of a queue as a waiting line for tasks. A **producer** adds a message describing a task; a **worker** (also called a consumer) takes a message and performs it. The queue is usually managed by a **broker** or queue service. Unlike a person waiting in line, the website can respond before the task is finished. That is **asynchronous processing**.

![A user asks for an export; the API produces a job, the queue holds it, and a worker creates the file.](/learning/async-systems/queue-basics.svg)

```aosdf-diagram
User request ──▶ API (producer) ──▶ Queue ──▶ Worker (consumer) ──▶ Finished export
                    │
                    └──▶ returns an operation ID so the user can check progress
```

Queues are useful when work is slow, can happen later, arrives in bursts, or needs independent retries. Common examples include document exports, image processing, email delivery, and importing files. A queue adds moving parts, so a short, fast operation that must finish before a response may be simpler as a direct call. A queue alone does not guarantee a task runs once, finishes in order, or succeeds; the later lessons show how to define those promises.

## Who this is for

People new to background jobs and engineers building or reviewing event consumers, scheduled tasks, webhooks, or live progress updates. The first lesson assumes only basic familiarity with a website request. Later lessons use HTTP and database transactions, defining the queue terms as they appear. No specific broker is required; the examples use an at-least-once queue such as an Amazon SQS standard queue, and provider-specific behavior is called out where relevant.

## What you will be able to do

- Explain what a queue, producer, message, and worker do, and when a queue is useful.
- Define what an API promises when it accepts asynchronous work and how a client checks completion.
- Write a job contract with an operation ID, version, owner, attempt policy, and safe acknowledgement point.
- Estimate queue growth and choose backpressure before overload damages downstream services.
- Classify failures, set timeouts and retry budgets, quarantine poison messages, and plan replay.
- Prevent a duplicate delivery from repeating an external effect.
- Choose between a work queue, pub/sub event, outbox, saga, webhook, or browser update based on the communication contract.
- Operate the system with queue age, result state, tracing, alerts, and a recovery runbook.

## Learning approach

Follow one general example: a user requests a **document export**. The API records an export operation and returns `202 Accepted` with its ID. A worker creates a file and marks the operation complete. The UI polls or receives a progress update. If generation fails, the user should see an honest status and an operator should be able to diagnose or replay the job safely.

If queues are new to you, read [What a queue is and when to use one](/learn/ai-engineer-fde/async-systems/what-is-a-queue) before the engineering contracts. If you already operate workers, use that lesson to check your vocabulary and move into the failure cases. After each **Try it**, add one section to a short design note: queue choice, request contract, job schema, capacity estimate, retry table, idempotency rule, event boundary, and runbook. The final lesson checks that these sections agree.

## Diagram: the delivery and recovery path

The main path records intent, publishes work, claims a job, applies an effect, and acknowledges completion. A transient failure follows a bounded retry path; repeated failures move to a dead-letter queue for inspection. The diagram is a teaching model: a real system must also handle a worker crash between the effect and acknowledgement.

![The API records an operation, sends it to a queue, and a worker creates a result after returning a status ID to the user.](/learning/async-systems/acceptance.svg)

<!-- QUEUE_LIFECYCLE_DIAGRAM -->

## Lesson index

| Order | Lesson | Question it answers |
| --- | --- | --- |
| 1 | [What a queue is and when to use one](/learn/ai-engineer-fde/async-systems/what-is-a-queue) | What waits in a queue, who processes it, and why use one? |
| 2 | [The queue boundary and worker contract](/learn/ai-engineer-fde/async-systems/queue-boundary) | What does accepting work promise, and when may a worker acknowledge it? |
| 3 | [Capacity, backpressure, and scheduling](/learn/ai-engineer-fde/async-systems/backpressure) | What happens when arrivals outrun workers? |
| 4 | [Timeouts, retries, and dead-letter queues](/learn/ai-engineer-fde/async-systems/retries-and-dlq) | Which failures deserve another attempt? |
| 5 | [Idempotency and delivery guarantees](/learn/ai-engineer-fde/async-systems/idempotency) | How can duplicate deliveries avoid duplicate effects? |
| 6 | [Events, outbox, and sagas](/learn/ai-engineer-fde/async-systems/events-and-sagas) | How do services publish facts and coordinate partial work? |
| 7 | [Webhooks, live updates, and scheduled jobs](/learn/ai-engineer-fde/async-systems/delivery-channels) | Which channel fits a recipient or timing need? |
| 8 | [Operating and reviewing a delivery system](/learn/ai-engineer-fde/async-systems/operations) | How do we know work is moving and recover it safely? |

## Completion check

Explain one export request from acceptance through a successful result, a duplicate delivery, an unavailable file store, and a poison job. Name the durable record, acknowledgement point, effect deduplication rule, queue-age alert, and manual replay procedure. If one is undefined, the architecture is not ready to rely on.

## Primary references

- [Amazon SQS standard queue semantics](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html)
- [Amazon SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)
- [AWS decision guide: SQS, SNS, or EventBridge](https://docs.aws.amazon.com/decision-guides/latest/decision-guides/sns-or-sqs-or-eventbridge.html)
