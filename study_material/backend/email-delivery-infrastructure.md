---
concepts: [email-deliverability, spf-dkim-dmarc, bounce-suppression, provider-failover]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: [retry-policy, idempotency, message-queue]
interview_angle: >
  Explain why a provider's accepted response does not mean inbox delivery, and how
  authentication, suppression, throttling, and ambiguous retries affect reliability.
built_at: framework-learning-roadmap
diagram: true
---

# Email Delivery Infrastructure

## Definition

SMTP transfers mail and MX records route inbound mail. SPF, DKIM, and DMARC help receiving
systems authenticate sending domains, but they do not guarantee inbox placement. A delivery
platform must handle provider throttling, bounces, complaints, suppressions, tenant quotas,
and reputation. A provider timeout may be ambiguous: the message might have been accepted.

## Example

Comms accepts an email job, checks tenant quota and suppression, sends with a stable message
ID, then records provider status. A hard bounce suppresses future sends to that address.
A transient throttle backs off. A timeout after send triggers reconciliation instead of an
unconditional duplicate send or immediate switch to a second provider.

## Diagram

```aosdf-diagram
API ──▶ queue ──▶ quota + suppression ──▶ provider router ──▶ SMTP/API provider
                    ▲                      │                        │
                    └──── retry / DLQ ◀───┴──── status + feedback ◀─┘
```

## Use It While Building

Write a failure table for throttle, hard bounce, complaint, 5xx, and timeout-after-accept.
Track accepted-to-provider latency and bounce/complaint rates; test suppression and provider
failover with the same message ID.

## Sources

- [Amazon SES DMARC guidance](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html)
- [Amazon SES deliverability concepts](https://docs.aws.amazon.com/ses/latest/dg/send-email-concepts-deliverability.html)
