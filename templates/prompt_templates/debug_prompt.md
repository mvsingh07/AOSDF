> Follow the project current-workflow-rules entry; initial review depth follows Small/Standard/High-risk. Further review or plan revision requires explicit founder approval.

# Debug Prompt Template
# Use this when an agent needs to investigate a failure, bug, or unexpected behavior.

---

## Context

**Project:** {project_name} (comms-engine)
**CLAUDE.md location:** `Microservices/Comms-Engine/CLAUDE.md` — READ THIS FIRST

---

## Problem Statement

**Task / Feature affected:** `<TASK-ID or feature name>`
**Service affected:** `<API Gateway / Orchestrator / Rendering / State Transition / etc.>`
**Environment:** `<dev / staging / production>`
**Severity:** `<Critical / High / Medium / Low>`

**Description of the problem:**
<Clear description of what is failing. What was expected vs. what actually happened.>

---

## Reproduction Steps

1. `<Step 1>`
2. `<Step 2>`
3. `<Observed result>`

---

## Evidence

**Error message / stack trace:**
```
<paste error here>
```

**Relevant log entries (with correlation_id):**
```
correlation_id: <value>
<paste log lines here>
```

**Relevant `message_events` records (if state issue):**
```sql
SELECT * FROM message_events WHERE communication_id = '<uuid>' ORDER BY created_at;
```
```
<paste result here>
```

---

## What Has Been Tried

<List anything already attempted, with outcome. Do not repeat failed attempts.>

---

## Hypotheses

<List your current hypotheses for the root cause, ordered by likelihood.>

1. `<Hypothesis 1>`
2. `<Hypothesis 2>`

---

## Debug Instructions for Agent

1. Start from the evidence above — do not guess without data
2. Check `message_events` event sequence — identify the last valid event and what should have followed
3. Trace the correlation_id across service logs to find where the failure occurred
4. Identify whether the issue is: input validation, state transition, queue processing, rendering, or adapter
5. Do NOT introduce a workaround that violates architecture rules (e.g., do not bypass State Transition Service)
6. If the fix requires a schema change or API contract change, flag it for Architect Agent review first

---

## Expected Output

| Output                | Description                                             |
| --------------------- | ------------------------------------------------------- |
| Root cause            | Specific line/function/service where failure originates |
| Fix                   | Code change or configuration change                     |
| Test                  | Regression test that would have caught this             |
| Tracking board update | Task ID, resolution, status = Done                      |

---

## Resolution

**Root cause:**
<Filled by agent after investigation>

**Fix applied:**
<File path, change description>

**Regression test added:**
<Test file and test name>

**Status:** `Resolved / Escalated / Needs Architecture Review`
