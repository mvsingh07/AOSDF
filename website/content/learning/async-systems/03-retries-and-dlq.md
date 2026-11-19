# Timeouts, retries, and dead-letter queues

Retries can recover from temporary failure, but they also repeat work and add load. Treat each retry as a deliberate decision based on the failure, the job's deadline, and the safety of its effect.

## Classify failures before setting a policy

For an export worker, distinguish:

| Failure | First response | Why |
| --- | --- | --- |
| File store returns a transient `503` | Retry with bounded backoff and jitter | The dependency may recover |
| Source document no longer exists | Mark failed or skip by policy | Repeating cannot restore the input |
| Message schema version is unsupported | Quarantine and alert | Every retry would fail the same way |
| Worker times out after file creation | Check durable result before retrying | The effect may already exist |
| Tenant loses permission | Stop and record a safe failure | Authorization must be checked at execution |

Use **timeouts** at every network call so a stuck dependency does not occupy a worker indefinitely. Allow a little margin between the dependency timeout, the worker's overall deadline, and the broker visibility lease. A circuit breaker can temporarily stop calls to a clearly failing dependency, but a queued job still needs a later retry or explicit failure outcome.

## Bound the retry budget

One policy might attempt after about 0, 2, 6, and 14 seconds, with jitter, then quarantine the job. The numbers are illustrative; derive them from the dependency's recovery behavior and the user's completion promise. Jitter spreads retries from many workers so they do not all strike a recovering service together. Avoid stacking independent SDK, worker, and broker retries without counting their combined attempts.

Keep a **deadline** or maximum elapsed time as well as an attempt limit. A four-attempt policy that stretches beyond the user's useful window is not reliable delivery. Record attempt count, last error class, and next eligible time without leaking document content into logs.

## Diagram: bounded failure handling

![A claimed job calls a dependency; success persists a result, while repeated failure moves through retry to a dead-letter queue and reviewed replay.](/learning/async-systems/retries.svg)

```aosdf-diagram
Claim job ──▶ call file store ──▶ success ──▶ persist result ──▶ acknowledge
                    │
                    ├── transient ──▶ backoff + jitter ──▶ retry
                    └── permanent / exhausted ──▶ DLQ + failed status + alert
```

[Explore the full queue delivery diagram](/queue-delivery-lifecycle.archify.html) for the retry and quarantine branch.

## A dead-letter queue is a holding area

A DLQ preserves messages that repeatedly fail so operators can inspect them without blocking healthy work. It is not a substitute for a user-facing failure state. For each quarantined export, correlate the message to its operation and record a safe reason. Provide a controlled replay procedure: fix the cause, inspect whether the effect already happened, choose one message or a bounded batch, replay with the same operation ID, and observe the outcome. Preserve redrive history so a poison message does not loop forever.

## Try it

Write a retry table for the five failures above. Choose a dependency timeout, worker deadline, visibility lease, maximum attempts, and overall completion deadline. Explain one case in which the worker should **not** retry.

## Check your understanding

- Why can an immediate retry storm extend an outage?
- Why must a timeout be treated as an uncertain outcome?
- What must be checked before replaying a DLQ message?

**Answer guide:** retries consume scarce capacity; the remote effect may have completed before the response was lost; inspect the cause and whether the operation's effect already exists.

## Read further

- [Amazon Builders' Library: timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- [Amazon SQS dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
