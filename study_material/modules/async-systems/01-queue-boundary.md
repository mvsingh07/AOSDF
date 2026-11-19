# The queue boundary and worker contract

The [first lesson](/learn/ai-engineer-fde/async-systems/what-is-a-queue) introduced a queue as a waiting place between a producer and a worker. The next question is what the website may promise when it places a job there. An asynchronous API acknowledges **acceptance**, not completion. In the document export example, a successful request means the operation was durably recorded and can be found again. It does not mean a file exists yet.

## Model the states a user can observe

A small state machine is enough: `accepted → running → succeeded`, with `failed` and `cancelled` as explicit exits. `GET /exports/{id}` returns status, a safe error code, and a file URL only after success. An unknown ID is different from a known failed export. A request with the same idempotency key should return the existing operation rather than create another export.

The API can return `202 Accepted` with `Location: /exports/{id}`. Return it only after the operation and a publishable intent are durable. If the database commit fails, return an error. If the queue publish is separate from the database commit, the outbox pattern in lesson 5 closes that gap.

## Put a contract in each job

The broker message should point to durable business state; it need not carry an entire document or sensitive payload.

```json
{
  "jobId": "job_82",
  "operationId": "exp_82",
  "tenantId": "tenant_7",
  "type": "export.generate",
  "version": 1,
  "traceId": "trace_19"
}
```

`jobId` identifies the delivery; `operationId` identifies the effect across deliveries. The worker checks that the tenant and operation still match, validates the schema version, and loads authorized source data from the system of record. Do not trust a message merely because it came from a queue: producers can be buggy or compromised, and old messages can outlive an authorization change.

## Diagram: acceptance is separate from completion

![The API durably records an operation and returns an ID; a queue then delivers work to a worker that records the finished result.](/learning/async-systems/acceptance.svg)

```aosdf-diagram
POST /exports ──▶ commit operation + intent ──▶ 202 + operation ID
                         │
                         └──▶ queue ──▶ worker ──▶ file ──▶ status: succeeded
                                            └──▶ failure ──▶ status: failed / retrying
```

[Explore the full queue delivery diagram](/queue-delivery-lifecycle.archify.html) to inspect the acknowledgement and recovery branches.

## Acknowledge after the durable effect

A worker claims a message, reads the current operation, performs or confirms the effect, durably records the result, then acknowledges the message. Acknowledging first can lose work if the worker crashes before recording the result. Acknowledging last can lead to redelivery if the acknowledgement is lost, which is why the effect must tolerate duplicates.

For SQS, a received message becomes temporarily invisible. If processing does not finish and delete the message within that visibility timeout, it can reappear; standard queues may also deliver more than once during the timeout. Other brokers use leases or acknowledgement mechanisms with their own details. Match the lease to expected work, extend it when supported, and still design for overlap.

## Try it

Write the request and status response for an export. Specify the durable acceptance point, the message fields, the state transition that makes the file downloadable, and the exact step after which the worker acknowledges. Simulate a crash just before acknowledgement.

## Check your understanding

- Why does `202` need an operation ID and status URL?
- What can happen if the worker acknowledges before writing the result?
- Why is a visibility lease not a duplicate-prevention guarantee?

**Answer guide:** the client needs a stable way to observe an unfinished operation; early acknowledgement can lose accepted work; a crash, timeout, or broker duplicate can cause another delivery.

## Read further

- [HTTP 202 Accepted, MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/202)
- [Amazon SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)
