# Operating and reviewing a delivery system

The architecture is incomplete until someone can answer: **Are accepted operations finishing within the promise, and what do we do when they do not?** Broker health alone cannot answer that. Compare queue signals with the durable operation states visible to users.

## Define a small service objective

For a sample export product, suppose the promise is “99% of accepted exports reach a terminal state within ten minutes.” Measure from the durable acceptance timestamp to `succeeded` or a clear `failed` state. Report successful completion separately: failing fast is observable but does not satisfy a success goal. Segment by tenant, job type, size, and dependency so one noisy group does not hide another.

Useful signals include:

- Oldest visible message age and queue depth: is accepted work waiting?
- In-flight count and lease expirations: are workers stuck or timing out?
- Attempt count, retry rate, and DLQ arrivals: is a failure repeating?
- Operation age by state: are records stuck in `accepted` or `running`?
- End-to-end completion latency and success rate: what does a user experience?
- Outbox unpublished age: did durable intent stop reaching the broker?

Broker counts are often approximate. Use them for operational trends and alerts; use the operation store for exact product state.

## Diagram: signals lead to a recovery decision

![Queue age, operation age, and dead-letter messages lead to triage, then overload controls or poison-job isolation, followed by verified recovery.](/learning/async-systems/operations.svg)

```aosdf-diagram
Queue age + operation age + DLQ count
                 │
                 ▼
Triage: intake? broker? worker? dependency? result store?
                 │
         ├── transient outage ──▶ limit intake / restore / drain
         └── poison job ──▶ isolate / fix / replay bounded set
```

[Explore the full queue delivery diagram](/queue-delivery-lifecycle.archify.html) while tracing a stuck operation.

## Write the runbook before the incident

An operator should be able to find a job by operation ID, see its schema version and attempts, inspect a sanitized error, determine whether the effect happened, and choose **retry**, **mark failed**, **cancel**, or **replay after repair**. Limit replay to a selected set with an owner and audit record. Define who may pause producers or workers, and how to resume without releasing a second wave of retries onto a recovering dependency.

Trace the request, outbox relay, broker publish, worker claim, provider call, result write, and acknowledgement with the same correlation ID. Avoid storing full document bodies or secrets in traces. Alert on user-impacting age and failure thresholds; route pages to someone who can take action.

## Worked review

At 09:00, export intake rises to 120/minute while workers complete 90/minute. By 09:20, backlog is about 600 jobs. At 09:25 the file store returns `503`, and retry rate rises. Adding workers would increase pressure on the store. A safer response is to limit new intake, cap concurrent file writes, keep bounded retries with jitter, and watch oldest age and success rate. Once the store recovers, drain deliberately. Inspect DLQ messages before replay and confirm an existing result for each uncertain timeout.

## Try it

Write a one-page design review containing: request/status contract, message schema, backlog calculation, failure classification, retry budget, deduplication key, outbox boundary, progress channel, three alerts, and a DLQ replay procedure. Walk through a worker crash after file creation.

## Check your understanding

- Why can a low queue depth coexist with broken user outcomes?
- Why should replay require an effect check?
- When is scaling workers the wrong incident response?

**Answer guide:** messages may be consumed but operations stuck or failed; an uncertain attempt may already have applied the effect; a saturated dependency can fail harder under extra concurrency.

## Read further

- [Amazon SQS CloudWatch metrics](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-available-cloudwatch-metrics.html)
- [Amazon SQS dead-letter queues and redrive](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
