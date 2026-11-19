> Follow the project current-workflow-rules entry; initial review depth follows Small/Standard/High-risk. Further review or plan revision requires explicit founder approval.

# Review Prompt Template

> **Current workflow rules (2026-11-06):** [single rules entry](../../reference/current-workflow-rules.md) — order of authority, the 2026-11-04/11-05 directives and clarifications C1–C12. Where this file conflicts, that entry wins.

# Use this template when asking an agent to review code, design, or documents.

---

## Context

**Project:** {project_name} (comms-engine)
**CLAUDE.md location:** `Microservices/Comms-Engine/CLAUDE.md` — READ THIS FIRST

---

## Review Request

**Review Type:** `<Code Review / Architecture Review / Document Review / Security Review>`
**Reviewer Agent:** `<Architect / Backend / QA>`
**Artifact:** `<file path or description>`
**Task it belongs to:** `<TASK-ID>`

---

## What Was Built

<Brief description of what the artifact does and why it was built. Reference the task and milestone.>

---

## Review Checklist

### Architecture & Design
- [ ] Does this follow the service design in `03_System_Design/service_design.md`?
- [ ] Are service boundaries respected? (no cross-service DB access)
- [ ] Is state only mutated via State Transition Service?
- [ ] Is this contract-first? (API spec or schema existed before implementation)
- [ ] Does this introduce any scope beyond the task definition?

### Security
- [ ] No hardcoded secrets
- [ ] All DB queries use parameterized queries
- [ ] Input validation present at service boundary
- [ ] PII not logged
- [ ] API key handling follows bcrypt standard
- [ ] Webhook signature verification implemented (if applicable)

### Multi-Tenancy
- [ ] RLS context set before every DB query
- [ ] No queries without tenant filter on tenant-scoped tables
- [ ] No cross-tenant data exposure possible

### Code Quality
- [ ] Tests written for all logic
- [ ] Tests use real DB (no DB mocks in integration tests)
- [ ] Error handling present at all external boundaries
- [ ] Correlation ID propagated through the request

### Domain-specific persistence (if applicable)
- [ ] State changes produce events in `message_events`
- [ ] No direct status column updates outside State Transition Service
- [ ] State transitions match allowed graph (queued→sent→delivered etc.)

---

## Expected Review Output

| Item                         | Required                                          |
| ---------------------------- | ------------------------------------------------- |
| Approval decision            | YES — Approved / Rejected / Approved with changes |
| List of issues found         | YES — numbered, specific, with line references    |
| Severity per issue           | YES — Blocker / Major / Minor                     |
| Suggested fix (for blockers) | YES                                               |

---

## Decision

**Approved:** `<YES / NO / CONDITIONAL>`

**Issues:**
1. [Severity] Description — file:line — Suggested fix
2. ...

**Notes:**
<Any patterns to flag for future tasks>

### Efficiency in the initial scope and review

Apply [the founder-approved workflow](../../reference/2026-11-05_strategy-b-role-boundaries-and-founder-review-control.md). Before initial approval, identify the bounded usable deliverable, compatible batched steps, existing reusable baseline/session/isolation, relevant checks versus the final required integration set, reusable revision-bound evidence, and a task-specific phase time budget. These can be brief fields in the existing plan, not extra documents. Review only whether the approach covers applicable real risks; don't add optional machinery. Approved active plans remain unchanged; later necessary amendments or extra reviews require founder approval.
