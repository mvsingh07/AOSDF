# Events, outbox, and sagas

A work queue distributes tasks to workers. A published event states that something happened and may be consumed independently by several subscribers. The distinction shapes who owns success: an export command has one processing owner; an `ExportCompleted` event might inform a notification service and an audit service without making either responsible for creating the file.

## Pick a communication contract

| Contract | Example | Consumer relationship |
| --- | --- | --- |
| Command / work queue | `GenerateExport(exp_82)` | One logical task is claimed by a worker |
| Event / pub-sub | `ExportCompleted(exp_82)` | Independent subscribers react to a fact |
| Request / response | `GET /exports/exp_82` | Caller needs a current answer |

Pub/sub fan-out can produce different outcomes for each subscriber. A notification failure should not silently reverse a completed export. Each subscriber needs its own retry and deduplication policy. Include event ID, type, schema version, subject ID, time, and trace context. Version payloads so older consumers can handle or reject them deliberately.

## Close the database-to-broker gap

This code is unsafe: `UPDATE exports ...; COMMIT; publish(message)`. If the process crashes after commit and before publish, the operation stays accepted but no worker sees it. Publishing first has the opposite problem: a worker may act on state that later rolls back.

A **transactional outbox** stores the operation and an outbox row in one database transaction. A relay publishes pending rows and marks them sent. The relay can publish the same row twice if it crashes after publishing, so consumers still need idempotency. The outbox solves loss between one database and broker; it does not make all downstream effects atomic.

## Diagram: durable event publication

![The API commits state and an outbox row together; a relay publishes to a broker for a worker and other subscribers.](/learning/async-systems/outbox-events.svg)

```aosdf-diagram
API ──▶ DB transaction: export row + outbox row
                              │
                              └──▶ relay ──▶ broker ──▶ export worker
                                              └──────▶ audit subscriber
```

[Explore the full queue delivery diagram](/queue-delivery-lifecycle.archify.html) to see where the outbox fits before publishing.

## Coordinate multi-service work with a saga

Suppose a paid export requires reserving a credit and then generating a file. Those steps cross service boundaries. A saga records progress and, on failure, runs a business **compensation** such as releasing an unused credit. Compensation is not a database rollback: a notification already sent or a file already downloaded may be irreversible. Define what can be compensated, what must be reconciled, and when a human must intervene.

Avoid distributed transactions by default when a local transaction plus outbox and explicit compensation meets the business need. If a stronger cross-system atomic guarantee is truly required, state that requirement and evaluate the participating systems' transaction support and operational cost.

## Try it

Design the export outbox row and `ExportCompleted` event. Simulate a relay crash after publish. Then add a credit reservation and write the compensation step for file generation failure. Name one effect that cannot be undone.

## Check your understanding

- Why can the outbox relay still publish twice?
- Why should each event subscriber own its own deduplication rule?
- Why is a saga compensation different from rolling back a SQL transaction?

**Answer guide:** the relay can crash before recording delivery; subscribers perform different effects and fail independently; a compensation is a new business action after earlier steps may already be visible.

## Read further

- [Transactional outbox pattern, Chris Richardson](https://microservices.io/patterns/data/transactional-outbox)
- [Saga pattern, Chris Richardson](https://microservices.io/patterns/data/saga.html)
- [AWS decision guide: SQS, SNS, or EventBridge](https://docs.aws.amazon.com/decision-guides/latest/decision-guides/sns-or-sqs-or-eventbridge.html)
