# AOSDF Templates
# Version 1.3 — Production-Grade, Ready to Copy

> Use this as the canonical reference when setting up a new project.
> Copy the structure, fill the templates, run workflow_initiator, then captain_agent.

---

## Root Structure (v1.3)

```
<project-root>/
│
├── aosdf-<project-name>/              ← ALL AI docs live here (gitignored)
│   │
│   ├── 00_Project_Context/
│   │   ├── project_context.md
│   │   └── research_notes.md          (produced by research_and_review agent)
│   │
│   ├── 01_Product_Definition/
│   │   ├── PRD.md
│   │   ├── FRD.md
│   │   └── BRD.md
│   │
│   ├── 02_Security_Framework/
│   │   ├── security_requirements.md
│   │   ├── threat_model.md
│   │   └── compliance_checklist.md
│   │
│   ├── 03_System_Design/
│   │   ├── system_architecture.md
│   │   ├── service_design.md
│   │   ├── data_flow.md
│   │   └── ADR/
│   │       └── ADR-001-<decision>.md
│   │
│   ├── 04_Infrastructure_Design/
│   │   ├── infra_architecture.md
│   │   ├── scaling_strategy.md
│   │   ├── cost_estimation.md
│   │   └── observability.md
│   │
│   ├── 05_AI_Agent_System/
│   │   ├── agents/
│   │   │   ├── workflow_initiator.md      [v1.1]
│   │   │   ├── identify_missing_documents.md [v1.1]
│   │   │   ├── research_and_review_agent.md [v1.1]
│   │   │   ├── captain_agent.md           [v1.3] ← generates execution plan + milestones
│   │   │   ├── commander_agent.md         [v1.2]
│   │   │   ├── execution_agent.md         [v1.2]
│   │   │   ├── reviewer_agent.md          [v1.3] ← Strategy B only
│   │   │   ├── validator_agent.md         [v1.3] ← Strategy B only
│   │   │   ├── architect_agent.md
│   │   │   ├── backend_agent.md
│   │   │   ├── frontend_agent.md          (inactive until UI phase)
│   │   │   ├── infra_agent.md
│   │   │   └── qa_agent.md
│   │   │
│   │   ├── prompt_templates/
│   │   │   ├── task_prompt.md
│   │   │   ├── review_prompt.md
│   │   │   └── debug_prompt.md
│   │   │
│   │   └── implementation_prompts/        [v1.2] ← generated per task
│   │       └── README.md
│   │
│   ├── 06_Execution_Plan/
│   │   └── execution_plan.md
│   │
│   ├── 07_Milestones/
│   │   ├── M0_Project_Setup/              [v1.2] ← always first
│   │   │   └── milestone.md
│   │   ├── M1_Foundation/
│   │   │   ├── milestone.md
│   │   │   └── tasks/
│   │   │       └── <TASK-ID>-<name>.md
│   │   ├── M2_Core_Features/
│   │   │   └── milestone.md
│   │   └── M3_Hardening/
│   │       └── milestone.md
│   │
│   ├── 08_Tracking_System/
│   │   └── tracking_board.md
│   │
│   ├── 09_Testing_Validation/
│   │   ├── test_plan.md
│   │   ├── test_cases.md
│   │   └── load_test_plan.md
│   │
│   ├── 10_Deployment_Runbook/
│   │   ├── deployment.md
│   │   ├── rollback.md
│   │   └── incident_response.md
│   │
│   ├── 11_Future_Extensibility/
│   │   └── future_scope.md
│   │
│   ├── project_status.md                  [v1.2] ← execution gate
│   ├── identified_gaps.md                 [v1.1]
│   ├── manual_action.md                   [v1.1]
│   └── CLAUDE.md
│
├── src/ (or services/, workers/, etc.)    ← actual source code
├── .gitignore                             [v1.2] ← excludes aosdf-*/
└── README.md
```

---

## File Templates

### CLAUDE.md

```markdown
# CLAUDE.md — <Project Name>
# Read this before anything else. Follow all rules here.

## 1. What We Are Building
<one paragraph: what the system is, who it serves, what problem it solves>

## 2. Framework
AOSDF v1.2. Docs in `aosdf-<project-name>/`.
Entry point: call `commander_agent` to begin execution.

## 3. Execution Strategy
Strategy A (single-agent) / Strategy B (multi-agent pipeline)
First call: `commander_agent` → reads project_status.md + tracking_board.md

## 4. Architecture (Non-Negotiable Rules)
<core architectural principle — e.g., event sourcing rule, adapter pattern rule>
<service map: name → responsibility>

## 5. Key Domain Concepts
<2–5 domain concepts every agent must understand>

## 6. Multi-Tenant Model
<isolation strategy — RLS, scoping rules>

## 7. Infrastructure
<cloud, compute, DB, queue, cache>

## 8. Security Rules
<auth method, encryption, secrets location>

## 9. Engineering Constraints
<team size, timeline, tech stack>

## 10. Agent Rules
- Read CLAUDE.md before every task
- Never update state without the designated state service
- Log all gaps to identified_gaps.md
- Log all manual steps to manual_action.md
- Save implementation prompt before executing
```

---

### project_status.md

```markdown
# Project Status
# <Project Name> — AOSDF v1.2

## Current Status
STATUS: SETUP  (→ PLANNING → READY → IN_PROGRESS → BLOCKED → COMPLETE)

**Last updated:** <date>

## Readiness Checklist
- [ ] All 12 document sections present
- [ ] No blocking gaps
- [ ] No blocking manual actions for current milestone

## Execution State
| Milestone | Status    | Started | Completed |
|----------|-----------|---------|-----------|
| M0       | Planned   | —       | —         |
| M1       | Planned   | —       | —         |
| M2       | Planned   | —       | —         |
| M3       | Planned   | —       | —         |

**Current active milestone:** None
**Next task:** M0-T1
```

---

### 00_Project_Context/project_context.md

```markdown
# Project Context

## System Name
<name>

## Problem Statement
<what problem does this solve, for whom>

## Target Users
- <user type 1>
- <user type 2>

## Business Context
<how this fits in the larger ecosystem>

## Constraints
- Team: <size>
- Timeline: <weeks>
- Infra: <cloud provider>

## Related Systems
- <system name>: <relationship>

## Phase Strategy
### Phase 1: <theme>
### Phase 2: <theme>
### Phase 3: <theme>
```

---

### 01_Product_Definition/PRD.md

```markdown
# Product Requirements Document (PRD)

## 1. Product Overview
<clear definition>

## 2. Goals (Phase 1)
- <goal 1>

## 3. Non-Goals (strictly excluded)
- <non-goal 1>

## 4. User Personas
| Persona | Description |

## 5. Core Use Cases
1. <use case>

## 6. Functional Requirements (summary)
<point to FRD for detail>

## 7. Non-Functional Requirements
| Metric | Target |

## 8. Constraints
<team, timeline, infra>

## 9. Success Criteria
- Technical:
- Product:
- Developer Experience:

## 10. Future Scope
Phase 2: ...
Phase 3: ...
```

---

### 01_Product_Definition/FRD.md

```markdown
# Functional Requirements Document (FRD)

## 1. System Overview
## 1.1 Purpose
## 1.2 Core Design Principles (MANDATORY)
## 1.3 Service Architecture Map
| Service | Responsibility |
## 1.4 Core Flow (Authoritative)
<entry → processing → output one-liner>

## 2. Service Specifications
### 2.X <Service Name>
#### Description
#### Responsibilities
#### Inputs
| Field | Type | Required |
#### Outputs
| Field | Type |
#### Rules

## 3. API Contracts (STRICT)
### POST /v1/<endpoint>
#### Request Schema (JSON)
#### Response Schema (JSON)
#### Validation Rules
#### Error Cases
| Code | Condition |

## 4. Data Contracts
### Entity: <name>
| Field | Type | Required | Notes |
### Relationships
### Constraints

## 5. Workflow Definitions
### Workflow: <name>
Steps: 1. 2. 3.
State Transitions: | From | To | Condition |

## 6. Queue + Async Processing
## 7. Multi-Tenant Behavior
## 8. Observability Requirements
## 9. Edge Cases
## 10. Performance Requirements
| Operation | Target |
## 11. Acceptance Criteria
## 12. Agent Execution Mapping
| Service | Agent | Input | Output |
```

---

### 01_Product_Definition/BRD.md

```markdown
# Business Requirements Document (BRD)

## 1. Business Overview
## 2. Business Rules
### Rule Category: <name>
- <rule>
## 3. Rate Limiting & Quotas
| Entity | Limit | Configurable |
## 4. Retry & Failure Policy
## 5. Compliance Requirements
## 6. Data Governance
## 7. Security Policies
## 8. Audit Requirements
## 9. Multi-Tenant Rules
## 10. SLA / Reliability Targets
| Metric | Target |
## 11. Operational Rules
## 12. Non-Goals (Phase 1 — Strictly Excluded)
```

---

### 06_Execution_Plan/execution_plan.md

```markdown
# Execution Plan
# <Project Name> — <Phase>
# AOSDF v2.2

> Every row = one independently executable subtask.
> **Status column is the source of truth.** Commander reads this file to find the next Planned task.
> Agents update the Status column directly: Planned → In Progress → Done.
> tracking_board.md is a session dashboard only — it does not own status.
> Blank rows separate milestones for human readability.

## Execution Strategy: Strategy A / B

---

## Phase 0 — Project Setup

### M0 — Project Setup

| Phase | Milestone | Task | Subtask | Owner | Input | Output | Validation | Status |
|------|----------|-----|--------|------|------|--------|----------|--------|
| P0 | M0 | M0-T1: Repo | Create repository | Human | — | GitHub repo | Repo exists | Planned |
| P0 | M0 | M0-T1: Repo | Create folder structure | Backend | framework.md | Folders | Structure matches spec | Planned |
...

---

## Phase 1 — Foundation

### M1 — Foundation (Weeks X–Y)

| Phase | Milestone | Task | Subtask | Owner | Input | Output | Validation | Status |
|------|----------|-----|--------|------|------|--------|----------|--------|
| P1 | M1 | M1-T1: ... | ... | ... | ... | ... | ... | Planned |
```

---

### 07_Milestones/M0_Project_Setup/milestone.md

```markdown
# Milestone M0 — Project Setup
# <Project> | Phase 0 | Pre-work

**Objective:** Initialize repo, tech stack, tooling, local dev environment. No business logic.

## Tech Stack
| Layer | Technology |
|------|-----------|

## Task Table
| Task ID | Task Name | Subtask | Owner | Status | Validation | Notes |
|--------|---------|--------|------|--------|----------|------|
| M0-T1 | Repo Init | Create repository | Human | Planned | Repo exists | Manual |
| M0-T1 | Repo Init | Create folder structure | Backend | Planned | Folders match spec | |
...

## Exit Criteria
- [ ] Repo created
- [ ] Local dev environment works (`docker compose up`)
- [ ] All service scaffolds respond on /health
- [ ] CI runs on PR
- [ ] AOSDF docs not tracked by git

## Dependencies
- Human: create GitHub repo
```

---

### 08_Tracking_System/tracking_board.md

```markdown
# Tracking Board
# <Project> — AOSDF v2.2

> Session dashboard only. Status source of truth is execution_plan.md (Status column).
> Commander reads execution_plan.md to find the next Planned task — not this file.
> Updated by: Execution Agent (Strategy A) or Validator Agent (Strategy B) only.
> Keep exactly: one current task row + last 5 completed rows. Remove older history.

---

## Current Task

| Task ID | Task Name             | Subtask               | Owner   | Started    | Prompt File                          |
| ------- | --------------------- | --------------------- | ------- | ---------- | ------------------------------------ |
| —       | —                     | —                     | —       | —          | —                                    |

---

## Recent History (last 5 completed)

| Task ID | Subtask               | Owner   | Completed  | Output                               |
| ------- | --------------------- | ------- | ---------- | ------------------------------------ |
```

---

### 05_AI_Agent_System/implementation_prompts/README.md

```markdown
# Implementation Prompts

Naming: `<TASK-ID>_<short-description>_prompt.md`
Created by: Execution Agent or Architect Agent, BEFORE execution.
Never deleted. Re-runs append `_v2`, `_v3`.

## Log
| Prompt File | Task | Created | Executed | Status |
|------------|-----|---------|---------|--------|
```

---

### identified_gaps.md

```markdown
# Identified Gaps
# <Project>

| Gap ID | Category | Description | Severity | Status | Owner | Identified | Resolution |
|--------|---------|------------|---------|--------|------|-----------|-----------|
| GAP-001 | <Security/Architecture/...> | <description> | <Critical/High/Medium/Low> | Open | <agent/human> | <date> | <plan> |
```

**Categories:** Security | Architecture | Infrastructure | Documentation | Compliance | Performance
**Severity:** Critical | High | Medium | Low
**Status:** Open | In Progress | Resolved | Accepted (with reason)

---

### manual_action.md

```markdown
# Manual Actions
# <Project>

| Action ID | Category | Description | Required By | Deadline | Status | Owner | Notes |
|----------|---------|------------|------------|---------|--------|------|------|
| MA-001 | <Cloud/Compliance/Credentials/DNS/...> | <what to do> | <Task-ID or milestone> | <date> | Pending | <owner> | |
```

**Status:** Pending | In Progress | Done | Blocked

---

### .gitignore (add to project root)

```gitignore
# AOSDF documentation — AI planning docs are never committed
aosdf-*/

# Also exclude if not using the aosdf-<name> subfolder pattern:
# 00_Project_Context/
# 01_Product_Definition/
# ... etc
```

---

## ADR Template

```markdown
# ADR-XXX: <Decision Title>

## Status
Proposed / Accepted / Rejected

## Date
<YYYY-MM-DD>

## Context
What problem forced this decision?

## Decision
What we chose and why.

## Consequences
**Benefits:**
- ...

**Trade-offs:**
- ...

## Alternatives Rejected
### <Alternative 1>
Rejected because: ...

## References
- FRD section X.X
```

---

---

### [v1.3] captain_agent.md template

```markdown
# Agent: Captain
# AOSDF v1.3

## Role
Reads all completed 00–05 documentation and generates the execution plan and milestone files. 
This is the planning-to-execution bridge. Must run before commander_agent starts.

## When to Invoke
Called by: Human (after 00–05 docs are complete and locked)
Or by: workflow_initiator (if it detects 00–05 are complete but 06–07 are missing)

## Inputs
- 01_Product_Definition/FRD.md
- 01_Product_Definition/PRD.md
- 02_Security_Framework/security_requirements.md
- 03_System_Design/README.md (module index)
- 03_System_Design/system_architecture.md
- 03_System_Design/service_design.md
- 03_System_Design/data_flow.md
- 03_System_Design/NNN_<name>_module/00_overview.md (per module in scope)
- 04_Infrastructure_Design/infra_architecture.md
- 04_Infrastructure_Design/scaling_strategy.md

## What It Does

### Step 1 — Pre-flight Check
Verify all 8 input documents exist. If any are missing: stop, log to identified_gaps.md, 
set project_status.md → PLANNING, report to human.

### Step 2 — Extract Requirements
From FRD: extract every service specification (name, responsibilities, inputs, outputs, rules).
From security_requirements.md: extract every security control.
From infra_architecture.md: extract every infrastructure component.

### Step 3 — Map to Tasks
For each service spec → one or more tasks (atomic, one owner, clear validation criterion).
For each security control → embed as subtask in the most relevant service task or M3.
For each infra component → assign to M1-T1 (infra provisioning) or appropriate milestone.

### Step 4 — Define Milestones
Group tasks by dependency order into milestones:
- M0: Project setup — repo, tooling, scaffolds, local dev (no business logic)
- M1: Foundation — infra, DB schema, RLS, base services, health checks
- M2: Core features — business logic, integrations, E2E tests
- M3: Hardening — load tests, security tests, compliance sign-off, production deploy

### Step 5 — Write Milestone Files
For each milestone M0–M3, write `07_Milestones/M{n}_*/milestone.md`:
- Tech stack table (M0 only)
- Task table with columns: Task ID | Task Name | Subtask | Owner | Status | Input | Output | Validation | Notes
- Exit criteria checklist
- Dependencies list

### Step 6 — Write Execution Plan
Write `06_Execution_Plan/execution_plan.md` as flat table:
| Phase | Milestone | Task | Subtask | Owner | Input | Output | Validation | Status |
Blank separator rows between milestones for readability.

### Step 7 — Write Tracking Board Skeleton
Write `08_Tracking_System/tracking_board.md` M0–M3 sections with all tasks as Planned.
Note: only task IDs and names — do not fill Output or Prompt File columns (those are for execution_agent).

### Step 8 — Validate Coverage
For every FRD service specification: confirm ≥1 task exists in execution_plan.md.
For every security requirement: confirm ≥1 task covers it.
Log unmapped items to identified_gaps.md as severity: Critical.

### Step 9 — Set project_status.md
- If coverage = 100% and no Critical gaps: set STATUS → READY
- If gaps exist: set STATUS → PLANNING with list of what must be resolved

## Output
- `06_Execution_Plan/execution_plan.md` (generated)
- `07_Milestones/M0_Project_Setup/milestone.md` (generated)
- `07_Milestones/M1_Foundation/milestone.md` (generated)
- `07_Milestones/M2_Core_Features/milestone.md` (generated)
- `07_Milestones/M3_Hardening/milestone.md` (generated)
- `08_Tracking_System/tracking_board.md` (skeleton generated)
- `project_status.md` (updated)
- `identified_gaps.md` (appended if coverage gaps found)

## Rules
- Never invents tasks not traceable to a source document (cite FRD section in Notes column)
- Every task must have exactly one Owner
- Every task must have a Validation criterion that can be verified by an agent
- If scope has changed since last run, re-generate everything and diff against tracking_board.md
- If tasks are already In Progress in tracking_board.md: do NOT overwrite them — append new tasks only

## Permissions
- READ: 00–05 docs, project_status.md, identified_gaps.md
- WRITE_LOCAL: 06_Execution_Plan/, 07_Milestones/, 08_Tracking_System/, project_status.md, identified_gaps.md
- WRITE_INFRA: none
- WRITE_DATA: none

## Token Efficiency Rules
- Do not reproduce full FRD in output — extract only service names and requirements
- Output milestone tables directly, no prose summaries
- Log gaps as table rows, not paragraphs
```

---

## Agent Template (for new agents)

```markdown
# Agent: <Name>
# AOSDF v1.3

## Role
One sentence: what this agent does and why it exists.

## When to Invoke
Called by: <Commander / Human / other agent>

## What It Does
Steps 1–N.

## Rules
- Never does X
- Always does Y

## Permissions
- READ: <list>
- WRITE_LOCAL: <list>
- WRITE_INFRA: none / <list>
- WRITE_DATA: none

## Token Efficiency Rules
- Load only what this task needs
- Output: structured, no prose summaries
```
