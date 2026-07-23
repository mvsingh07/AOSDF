# Agent Index
# AOSDF v2.3 — Quick Reference
# Read this to understand which agent to call and when.

---

## Agent Call Sequence (Full Lifecycle)

```
[ONE TIME — Setup]
workflow_initiator     ← human calls; creates folder structure, CLAUDE.md, initial files

[ONE TIME — Pre-execution]
research_and_review    ← human calls before architecture locks (optional)
research_and_refine    ← human calls any time a research question needs a structured answer
captain_agent          ← human calls after 00–05 docs complete; generates plan + milestones

[PER SESSION — Execution]
commander_agent        ← human calls once per session; reads state, delegates
  └─ Strategy A: execution_agent (implements → validates → marks Done)
  └─ Strategy B: architect_agent → reviewer_agent → implementor → validator_agent

[ON DEMAND — Post-baseline]
addendum_agent         ← human calls when a cross-cutting requirement arrives after plan is locked
```

---

## Agent Reference Table

| Agent | Defined In | Called By | Calls | Updates |
| ----- | ---------- | --------- | ----- | ------- |
| `workflow_initiator` | `AOSDF/workflow_initiator.md` | Human | `identify_missing_documents` | `CLAUDE.md`, `project_status.md`, `identified_gaps.md`, `12_Manual_Actions/` |
| `identify_missing_documents` | `AOSDF/identify_missing_documents.md` | `workflow_initiator` or Human | Nothing | `identified_gaps.md` (append) |
| `research_and_review` | `agents/research_and_review_agent.md` | Human | Nothing | `research_notes.md`, `identified_gaps.md` |
| `research_and_refine` | `agents/research_and_refine_agent.md` | Human | Nothing | `research_results.md` only — never existing docs |
| `captain_agent` | `agents/captain_agent.md` | Human or `workflow_initiator` | Nothing | `execution_plan.md`, `07_Milestones/*/milestone.md`, `08_Tracking_System/decisions_log.md` (created if absent — decisions log only, not a task board), `project_status.md` |
| `commander_agent` | `agents/commander_agent.md` | Human | `execution_agent` (A) or `architect_agent` (B) | `project_status.md` |
| `execution_agent` | `agents/execution_agent.md` | `commander_agent` | Nothing | `implementation_prompts/`; `execution_plan.md` Status column (the only status record); `identified_gaps.md`, `12_Manual_Actions/actions.md` |
| `architect_agent` | `agents/architect_agent.md` | `commander_agent` (B) | `reviewer_agent` | `ADR/`, `service_design.md`, `implementation_prompts/` |
| `reviewer_agent` | `agents/reviewer_agent.md` | `architect_agent` (B) | Nothing (returns decision) | Nothing |
| `validator_agent` | `agents/validator_agent.md` | Implementor (B) | Nothing | `execution_plan.md` Status column (the only status record — the only agent in Strategy B that does so); `identified_gaps.md`, `12_Manual_Actions/actions.md` |
| `infra_agent` | `agents/infra_agent.md` | `commander_agent` | Nothing | IaC code; `execution_plan.md` Status column |
| `qa_agent` | `agents/qa_agent.md` | `commander_agent` | Nothing | Test results; `execution_plan.md` Status column |
| `frontend_agent` | `agents/frontend_agent.md` | `commander_agent` | Nothing | UI code, tests; `execution_plan.md` Status column |
| `addendum_agent` | `agents/addendum_agent.md` | Human | Nothing | `15_Addendums/<slug>_plan.md`, `15_Addendums/tracking_addendums.md` |

---

## Agents That Must Be Called by a Human

These agents require human judgment or human-authored input — they are never called automatically:

| Agent | Trigger |
| ----- | ------- |
| `workflow_initiator` | Project start or resume after a gap |
| `research_and_review` | Before architecture docs are finalized |
| `research_and_refine` | When a specific research question needs a structured answer |
| `captain_agent` | After all 00–05 docs are complete and locked |
| `addendum_agent` | After human writes `15_Addendums/<slug>.md` |

---

## project_status.md State Machine

| From | To | Who Transitions | Condition |
| ---- | -- | --------------- | --------- |
| `SETUP` | `PLANNING` | `workflow_initiator` | Folder structure confirmed, CLAUDE.md created |
| `PLANNING` | `READY` | `captain_agent` | All 00–05 docs read, execution plan + milestones generated, FRD coverage validated |
| `READY` | `IN_PROGRESS` | `commander_agent` | First task delegated |
| `IN_PROGRESS` | `COMPLETE` | `commander_agent` | All M3 exit criteria pass |
| Any | `BLOCKED` | Any agent | Unresolvable blocker found |

---

## What Agents Can Write — Permission Summary

| Permission Level | What It Means | Agents With It |
| ---------------- | ------------- | -------------- |
| READ | Read any project file | All agents |
| WRITE_LOCAL | Create/edit project files | `execution_agent`, `validator_agent`, `architect_agent`, `infra_agent`, `qa_agent`, `captain_agent`, `addendum_agent` |
| WRITE_INFRA | Provision/modify cloud resources | `infra_agent` only (requires human approval before apply) |
| WRITE_DATA | Mutate production data | None — human only |
| WRITE_REMOTE | Push to remote git | **None — git push is always a human action** |
| ADMIN | Cross-cutting (secrets, IAM, DNS) | Human only |
