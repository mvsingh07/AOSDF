> Follow the project current-workflow-rules entry; initial review depth follows Small/Standard/High-risk. Further review or plan revision requires explicit founder approval.

# Task Prompt Template
# Use this template for every task assigned to an AI agent.

---

## Context

**Project:** {project_name} (comms-engine)
**Framework:** AOSDF (AI-Orchestrated Software Development Framework)
**CLAUDE.md location:** `Microservices/Comms-Engine/CLAUDE.md` — READ THIS FIRST

**System summary:**
{project_name} is a multi-tenant, API-first, event-driven communication platform. It handles transactional messaging across email, SMS, PDF, and WhatsApp (stub). State is managed via event sourcing — `message_events` is the source of truth. Only the State Transition Service may mutate communication status.

**Current phase:** Phase 1 — Internal backbone for Auction Engine

---

## Task

**Task ID:** `<TASK-ID from execution_plan.md>`
**Milestone:** `<M1 / M2 / M3>`
**Agent:** `<Backend / Infra / Architect / QA>`

**Task description:**
<Clear, specific description of what needs to be done. One thing at a time. No ambiguity.>

---

## Constraints

- Follow the architecture in `03_System_Design/service_design.md` — no deviations
- API contracts and schemas MUST exist before implementation begins
- Do NOT update communication status directly — only via State Transition Service
- Do NOT add scope beyond this task definition
- Do NOT make assumptions — if something is unclear, state it as a blocker
- All DB queries MUST use parameterized queries
- All secrets via environment variables — no hardcoding
- Tests MUST be written for all implemented logic

---

## Input

| Input               | Location                                       |
| ------------------- | ---------------------------------------------- |
| FRD section         | `01_Project_Definition/FRD.md` section `<X.X>` |
| API contract        | `<path to contract or inline below>`           |
| DB schema           | `<path to schema or inline below>`             |
| ADR (if applicable) | `03_System_Design/ADR/<ADR-XXX.md>`            |

**Inline input (if applicable):**
```
<paste relevant schema / API spec / data contract here>
```

---

## Expected Output

| Output       | Format                       | Location      |
| ------------ | ---------------------------- | ------------- |
| `<output 1>` | `<code / document / config>` | `<file path>` |
| `<output 2>` | `<test file>`                | `<file path>` |

---

## Validation Criteria

- [ ] `<Specific verifiable condition 1>`
- [ ] `<Specific verifiable condition 2>`
- [ ] All unit tests pass
- [ ] Integration tests pass against real DB
- [ ] No hardcoded secrets
- [ ] Tracking board updated with output

---

## Notes / Known Issues

<Any known constraints, edge cases, or dependencies on other tasks>
