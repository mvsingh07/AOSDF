# Webhooks, live updates, and scheduled jobs

Once an export is running, different recipients need different ways to learn its state. A browser, another server, and a scheduled maintenance task do not share the same delivery contract. The queue remains the internal work path; these are ways to trigger or report work.

## Choose by recipient and direction

| Channel | Good fit | Important boundary |
| --- | --- | --- |
| Status polling | Browser checks an export every few seconds | Bound frequency, use caching, stop on terminal state |
| Server-sent events (SSE) | Server pushes progress to a browser | One-way stream; reconnect and fetch current state |
| WebSocket | Browser and server exchange frequent bidirectional messages | Connection lifecycle, auth renewal, and backpressure |
| Webhook | Your server notifies another server | Sign requests, handle retries and receiver deduplication |
| Cron / scheduled job | Periodic cleanup or reconciliation | Prevent overlap; use a durable operation ID |

**Long polling** is a request held open until an update or timeout, followed by another request. It can fit environments without a persistent stream, but it still needs timeouts and connection budgets. None of these channels replaces the durable operation record. After reconnect, the client should query current state; an update can be delayed or missed.

## Design a webhook as at-least-once notification

For `ExportCompleted`, create a webhook delivery record with an event ID and destination. Sign the body using a secret scoped to that endpoint, include a timestamp, enforce a replay window, and validate destination URLs to reduce server-side request forgery risk. Acknowledge a receiver's successful response; retry transient failures with a bounded schedule and show delivery status. Receivers should deduplicate on event ID and respond quickly, handing slow work to their own queue.

A webhook should not expose a private download URL to a recipient who lacks access. Include a stable export ID and let the recipient retrieve details through an authorized API.

## Diagram: one status, several subscribers

![Browser polling reads a durable status record, while the server pushes updates through server-sent events and signed partner webhooks.](/learning/async-systems/delivery-channels.svg)

```aosdf-diagram
Export status store ──▶ GET status (polling)
         │
         ├──▶ SSE / WebSocket update to browser
         └──▶ webhook delivery queue ──▶ signed POST to partner
```

[Explore the full queue delivery diagram](/queue-delivery-lifecycle.archify.html) for the durable processing path behind these notifications.

## Treat schedules as producers

A nightly reconciliation job should emit bounded work units, not hold one process open for hours. Give each run a unique ID and each item a stable operation key. If a run overlaps its predecessor, either skip, join, or partition explicitly. Reconciliation can compare accepted exports against completed files and repair a missed outbox publication or status update. Keep the same duplicate-safe worker rule.

## Try it

Choose a progress channel for a browser that only needs updates every five seconds, and another for a live collaborative editor. Design a partner webhook payload with event ID, timestamp, and signature. Describe what the browser does after losing its connection.

## Check your understanding

- Why does an SSE progress update not replace `GET /exports/{id}`?
- What should a webhook receiver do with the same event ID twice?
- Why can a cron job overload the same queue as user requests?

**Answer guide:** live messages can be missed; the receiver should make the repeated event harmless; scheduled work can arrive as a large burst and consume worker capacity.

## Read further

- [MDN: using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [MDN: WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [GitHub webhook delivery and validation guidance](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)
