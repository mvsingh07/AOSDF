---
concepts: [monolithic-architecture, microservices-architecture, event-driven-architecture, layered-architecture]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: []
interview_angle: >
  Never present microservices as strictly "better" — be ready to argue for a monolith first, and
  name the specific organizational or scaling signal that would justify splitting it later.
built_at: L6-T1
diagram: true
---

# Architecture Styles

## Definition

- **Layered architecture:** code organized into horizontal layers (presentation, business logic, data
  access), each only calling the layer directly below it. Simple to reason about; the risk is a "big ball
  of mud" if layer boundaries aren't enforced.
- **Monolithic architecture:** the entire application ships and deploys as one unit. Simple to develop,
  test, and deploy early on; the cost shows up later as team size and codebase size grow — one bad
  deploy can take down everything, and every change requires understanding a larger shared codebase.
- **Microservices architecture:** the application is split into independently deployable services, each
  owning its own data, communicating over the network (REST/gRPC/messaging). Buys independent scaling
  and deployment per team, at the cost of distributed-systems complexity (network failures, data
  consistency across services, operational overhead) that a monolith never has to face.
- **Event-driven architecture:** services communicate by publishing/reacting to events rather than
  direct request/response calls — decouples producers from consumers, but makes the overall flow harder
  to trace end-to-end (see `study_material/backend/message-queues.md`).

## Example

A monolith handling an order: one process, one deploy, direct function calls between the order module
and the inventory module — a bug in the inventory module can crash the whole process.

The same system as microservices: an `OrderService` and `InventoryService` deployed and scaled
independently, communicating over HTTP or a message queue — an inventory outage degrades checkout, but
doesn't crash it outright, at the cost of needing to handle that partial failure explicitly.

## Diagram

```aosdf-diagram
Layered (monolith)                    Microservices
┌───────────────────────┐             ┌─────────────┐    ┌─────────────┐
│   Presentation Layer   │             │ Order Svc   │───▶│ Inventory   │
├───────────────────────┤             │ (own deploy)│    │ Svc         │
│   Business Logic Layer │             └──────┬──────┘    └─────────────┘
├───────────────────────┤                     │ event/API call
│   Data Access Layer    │                     ▼
└───────────────────────┘             ┌─────────────┐
        one deploy unit                │ Payment Svc │
                                        └─────────────┘
```

## AOSDF's Own Call

This framework itself defaulted to a single-owner monolith for `AOSDF-Hosting` (`OD-H9`) rather than a
services split — the MVP has one team, one deploy target, and no scaling signal yet that would justify
the distributed-systems cost. That's the actual decision process this topic is testing: start simple,
split when a real signal (team ownership boundaries, independent scaling needs) appears.
