# AI-Orchestrated Software Development Framework (AOSDF)
# Version 1.6

> Changes in v1.1 are marked `[v1.1]`
> Changes in v1.2 are marked `[v1.2]`
> Changes in v1.3 are marked `[v1.3]`
> Changes in v1.4 are marked `[v1.4]`
> Changes in v1.5 are marked `[v1.5]`
> Changes in v1.6 are marked `[v1.6]`

---

## What This Framework Does

- Breaks product → phases → milestones → tasks → subtasks
- Attaches agent prompts to every execution unit
- Defines artifacts with strict input/output contracts
- Enforces security + architecture discipline before any code is written
- Tracks execution with full traceability
- **[v1.1]** Supports both single-agent and multi-agent execution strategies
- **[v1.1]** Minimizes human intervention after `05_AI_Agent_System` is complete
- **[v1.2]** Defines a clear execution-ready gate via `project_status.md`
- **[v1.2]** Introduces commander → execution/validator agent delegation pattern
- **[v1.2]** Defines implementation prompts as tracked artifacts
- **[v1.2]** Isolates all AI documentation from source code via `.gitignore`
- **[v1.3]** Introduces `captain_agent` — bridges product/architecture docs to executable plan
- **[v1.3]** Execution plan and milestones are agent-generated with FRD coverage validation, not written manually
- **[v1.3]** Defines missing Strategy B agents: `reviewer_agent` and `validator_agent`
- **[v1.4]** Introduces `research_and_refine_agent` — task-driven research outputting `research_results.md`; never modifies existing documents
- **[v1.4]** Defines the global Document Formatting Standard — padded columns, separator dashes match column width; applies to all agent-generated files with tables
- **[v1.5]** Defines the `{project_name}-Orchestrum` workspace layout — AOSDF is a separate reusable directory, not embedded in the project; application code and project documentation are cleanly separated
- **[v1.6]** Integrates LLM Wiki as a persistent, file-based context layer (`llm-wiki/` fourth directory); agents read wiki before any design/architecture task; wiki is human-maintained, never agent-written

---

## Core Principles (Non-Negotiable)

**1. Security-first**
Security document must exist and be reviewed before any coding begins.

**2. Contract-first development**
API contracts and schemas must exist before implementation tasks are assigned.

**3. AI-agent compatible structure**
Every task = executable prompt. Outputs are deterministic and verifiable.

**4. Iterative milestones**
Each milestone = a working, testable system slice. Not a feature dump.

**5. Traceability**
Every task → output → validation → status. Nothing exists outside the tracking system.

**[v1.1] 6. Research-before-design**
Before finalizing product definition and architecture, a research pass on comparable systems is required.

**[v1.1] 7. Gap-tracking as first-class concern**
Every identified gap logged in `identified_gaps.md` with classification and status.

**[v1.1] 8. Manual action tracking**
Every human-required step logged in `manual_action.md`.

**[v1.1] 9. Minimum human intervention after 05_AI_Agent_System**
System runs on agent execution with human approval gates only.

**[v1.2] 10. Execution-ready gate**
`project_status.md` is the single source of truth for whether the project is ready to begin execution. No agent begins implementation work unless `project_status.md` shows `READY`.

**[v1.2] 11. Implementation prompts are tracked artifacts**
Every prompt generated for a task is saved to `05_AI_Agent_System/implementation_prompts/` before execution. Not ephemeral — they are part of the project record.

**[v1.2] 12. AI documentation is never committed to source control**
All AOSDF documentation (00–11 folders, agents, prompts, tracking) lives in `{project_name}-Documents/` and `AOSDF/` at the workspace root, both excluded from git via `.gitignore`. **[v1.5]** See Workspace Layout section for the canonical structure.

**[v1.2] 13. M0 is always the first milestone**
Every project starts with Milestone 0: project repo and tech stack setup. No infrastructure or code work begins before M0 is complete.

**[v1.3] 14. Execution plan and milestones are agent-generated artifacts**
After 00–05 documentation is complete, `captain_agent` reads the FRD, architecture, and security documents and generates the execution plan and milestone files. Manually writing these without running captain_agent is not permitted — coverage validation would be skipped.

**[v1.3] 15. captain_agent validates FRD → task coverage**
Every service specification in the FRD must map to at least one task in the execution plan. Unmapped requirements are logged to `identified_gaps.md` as Critical gaps before execution begins.

**[v1.3] 16. project_status.md transitions have defined owners**
- `SETUP` → `PLANNING`: `workflow_initiator` (after structure is confirmed)
- `PLANNING` → `READY`: `captain_agent` (after execution plan passes coverage validation)
- `READY` → `IN_PROGRESS`: `commander_agent` (on first task delegation)
- `IN_PROGRESS` → `COMPLETE`: `commander_agent` (after all M3 exit criteria pass)
- Any state → `BLOCKED`: any agent that hits an unresolvable blocker

**[v1.6] 17. LLM Wiki as persistent context layer**
Every project following AOSDF has an `llm-wiki/` folder as its fourth directory.
Agents READ from the wiki for context before starting any task that involves design,
research, or architecture. Agents NEVER write to `llm-wiki/` — the wiki is updated
by the human via direct session commands. The wiki and the project documents are
separate systems that must never overlap in write access.

---

## Root Structure (v1.2) — Superseded by v1.5 Workspace Layout below

> **[v1.5]** The workspace layout below is the canonical structure. The v1.2 single-folder pattern is deprecated.

---

## [v1.5] Workspace Layout

Every project using AOSDF v1.5 uses the `{project_name}-Orchestrum` workspace root. AOSDF lives as a **separate reusable directory** — not embedded inside any project. Application code and documentation are cleanly separated.

```
{project_name}-Orchestrum/                     ← WORKSPACE ROOT (not a git repo itself)
│
├── .gitignore                                  [v1.5] ← excludes AOSDF/ and {project_name}-Documents/
│
├── AOSDF/                                      [v1.5] ← General, reusable AI Development Model
│   ├── framework.md                            This file
│   ├── manual.md
│   ├── captain_agent.md
│   ├── research_and_refine_agent.md
│   ├── workflow_initiator.md
│   ├── identify_missing_documents.md
│   ├── templates.md
│   ├── initiator_format.md
│   └── designing_aosfd/
│
├── {project_name}/                             ← Application Code only
│   ├── comms-service/                      (backend — NestJS / Fastify / etc.)
│   └── supagram/                        (optional UI — e.g. (customized react-email-editor)/, Phase 2+)
│
├── {project_name}-Documents/                   ← Project Documentation (gitignored)
    ├── CLAUDE.md                               ← AI agent context file (entry point)
    ├── project_status.md                       [v1.2] execution readiness gate
    ├── identified_gaps.md                      [v1.1]
    ├── manual_action.md                        [v1.1]
    ├── research_results.md                     [v1.4] output from research_and_refine_agent
    └── documents/
        ├── 00_Project_Context/
        ├── 01_Project_Definition/
        ├── 02_Security_Framework/
        ├── 03_System_Design/
        │   ├── ADR/
        │   └── additional-documents/
        ├── 04_Infrastructure_Design/
        ├── 05_AI_Agent_System/
        │   ├── agents/
        │   ├── prompt_templates/
        │   └── implementation_prompts/         [v1.2] ← generated prompts stored here
        ├── 06_Execution_Plan/
        ├── 07_Milestones/
        │   ├── M0_Project_Setup/               [v1.2] ← always first milestone
        │   ├── M1_Foundation/
        │   ├── M2_Core_Features/
        │   └── M3_Hardening/
        ├── 08_Tracking_System/
        ├── 09_Testing_Validation/
        ├── 10_Deployment_Runbook/
        └── 11_Future_Extensibility/
│
└── llm-wiki/                            [v1.6] ← persistent wiki, LLM-maintained
    ├── WIKI.md                          ← wiki schema and rules
    ├── index.md                         ← content catalog
    ├── log.md                           ← append-only event log
    ├── overview.md                      ← evolving synthesis
    ├── sessions/
    │   └── session-contexts.md
    ├── sources/
    ├── entities/
    ├── concepts/
    └── analyses/
```

### Naming Convention

| Component               | Pattern                          | Example                      |
| ----------------------- | -------------------------------- | ---------------------------- |
| Workspace root          | `{project_name}-Orchestrum`      | `Comms-Engine-Orchestrum`    |
| Application code        | `{project_name}`                 | `Comms-Engine`               |
| Project documentation   | `{project_name}-Documents`       | `Comms-Engine-Documents`     |
| AI Development Model    | `AOSDF`                          | `AOSDF` (same for all)       |
| Persistent wiki         | `llm-wiki`                       | `llm-wiki` (same for all)    |

### Why Separate AOSDF from the Project

- AOSDF is framework-level, not project-level — it should be shared and reusable across projects
- Upgrading AOSDF (e.g., v1.4 → v1.5) does not affect project documentation
- Git history for application code is not polluted with AI planning artifacts
- `.gitignore` at workspace root excludes both `AOSDF/` and `{project_name}-Documents/` in one place

---

## Section Guide

### 00_Project_Context
**Purpose:** Define what we are building and why.
**File:** `project_context.md`
**Required sections:** System Name, Problem Statement, Target Users, Business Context, Constraints, Related Systems, Phase Strategy

### 01_Product_Definition
**Files:** `PRD.md`, `FRD.md`, `BRD.md`

### 02_Security_Framework
**CRITICAL — complete before any coding.**
**Files:** `security_requirements.md`, `threat_model.md`, `compliance_checklist.md`

### 03_System_Design
**Files:** `system_architecture.md`, `service_design.md`, `data_flow.md`, `ADR/`

### 04_Infrastructure_Design
**Files:** `infra_architecture.md`, `scaling_strategy.md`, `cost_estimation.md`, `observability.md`

### 05_AI_Agent_System
**Files:**
```
agents/
  workflow_initiator.md     [v1.1]  ← project setup, structure validation
  identify_missing_docs.md  [v1.1]  ← scans project against checklist
  research_and_review.md    [v1.1]  ← references research before architecture locks
  research_and_refine.md    [v1.4]  ← task-driven research + 00-04 doc updates; inputs: task.md + project_root_path
  captain_agent.md          [v1.3]  ← reads 00-05 docs, generates execution plan + milestones
  commander_agent.md        [v1.2]  ← orchestrates execution, reads status, delegates
  execution_agent.md        [v1.2]  ← Strategy A: single-agent implementor
  reviewer_agent.md         [v1.3]  ← Strategy B: reviews prompt for security + scale
  validator_agent.md        [v1.3]  ← Strategy B: runs tests, updates tracking board
  architect_agent.md
  backend_agent.md
  frontend_agent.md
  infra_agent.md
  qa_agent.md

prompt_templates/
  task_prompt.md
  review_prompt.md
  debug_prompt.md

implementation_prompts/     [v1.2]
  <TASK-ID>_prompt.md       ← generated per task, saved before execution
```

### [v1.2] implementation_prompts/ — Tracking Rule

Every prompt generated by the Commander or Architect Agent for a task MUST be saved as:
```
implementation_prompts/<TASK-ID>_<short-name>_prompt.md
```
before the Execution/Implementor Agent runs it.

Naming example: `M1-T3-api-gateway-auth_prompt.md`

The tracking board references the prompt file path. This creates a full audit trail: task → prompt → output.

### 06_Execution_Plan
**Format:** Phase → Milestone → Task → Subtask | Owner | Input | Output | Validation | Status
See execution plan format below.

### [v1.2] 07_Milestones — M0 Always First

M0 = Project Setup. Contains:
- Repo initialization with chosen tech stack
- Folder structure creation
- Package/dependency setup
- Local dev environment setup
- Linting, formatting, pre-commit hooks
- Environment variable template (`.env.example`)

No code is written in M1+ until M0 is complete.

### 08_Tracking_System — `tracking_board.md`
Master status view. Updated by: `execution_agent` (Strategy A) or `validator_agent` (Strategy B) only.

### [v1.2] project_status.md — Execution Gate

This file tracks the project's overall readiness. Located at `{project_name}-Documents/project_status.md`.

States: `SETUP` → `PLANNING` → `READY` → `IN_PROGRESS` → `BLOCKED` → `COMPLETE`

No execution agent may begin implementation until status = `READY`.

---

## [v1.2] Agent Architecture

### [v1.3] captain_agent — Planning & Execution Architect

- **Role:** Reads all completed 00–05 documents and generates the execution plan and milestones. This is the bridge from "documentation complete" to "ready to build." Must be run before `commander_agent` ever starts.
- **Inputs:** FRD, PRD, security_requirements.md, system_architecture.md, service_design.md, data_flow.md, infra_architecture.md
- **Outputs:** `06_Execution_Plan/execution_plan.md`, `07_Milestones/M*/milestone.md`, updated `08_Tracking_System/tracking_board.md`, updated `project_status.md`
- **Coverage validation:** Every FRD service spec → at least one task. Unmapped specs → `identified_gaps.md` as Critical.
- **Never starts if:** 00–05 docs are incomplete (defers back to workflow_initiator).
- **Sets:** `project_status.md` → `READY` on success, `PLANNING` if gaps remain.
- **Called by:** Human (after 00–05 are complete), or workflow_initiator if all docs are present.

### [v1.4] research_and_refine_agent — Task-Driven Research Output

- **Role:** Receives a `task.md` describing a research question and a `project_root_path`. Reads the listed 00–04 documents as context, researches the defined scope using public sources, and writes findings + a recommendation to `research_results.md` at the project root. **Never modifies any existing document.**
- **Inputs:** `task.md` (objective, research scope, context documents, constraints), `project_root_path`
- **Output:** `project_root_path/research_results.md` — appended if it already exists
- **Does not:** modify FRD, architecture docs, ADRs, gaps, or any other existing file
- **Human decides:** what to do with the findings (update docs, create ADRs, re-run captain_agent)
- **Called by:** Human only. Never called by commander or captain_agent.

---

### [v1.3] reviewer_agent (Strategy B)

- **Role:** Receives the implementation prompt generated by architect_agent. Reviews for security vulnerabilities, architectural violations (especially state mutation rules), scalability concerns, and missing test coverage. Returns approval or redline.
- **Called by:** architect_agent (Strategy B only)
- **Calls:** implementor (on approval) or architect_agent (on redline)

### [v1.3] validator_agent (Strategy B)

- **Role:** Receives completed implementation from implementor. Runs tests (unit, integration, schema validation). If all pass: marks task `Done` in tracking board and notifies commander. If fail: returns to implementor with failure details.
- **Called by:** implementor (Strategy B only)
- **Updates:** `tracking_board.md` (the only agent in Strategy B that does so)

### New Agents in v1.2

#### commander_agent
- **Role:** The sole orchestrator of execution. Called once per session. Reads `project_status.md` and `tracking_board.md`, finds the next work, and delegates to the right agent.
- **Never implements.** Only directs.
- **Calls:** `execution_agent` (Strategy A) or `architect_agent` (Strategy B)
- **Called by:** Human, once per session

#### execution_agent (Strategy A)
- **Role:** Single-agent implementor. Receives task from commander, generates prompt, saves to `implementation_prompts/`, executes, validates, updates tracking board.
- **Updates:** `tracking_board.md` after every subtask
- **Called by:** Commander Agent

#### For Strategy B — the validator_agent responsibility
The validator_agent (final step of the 4-agent pipeline) is the only one that updates `tracking_board.md` with `Done` status. The commander reads this to know what to delegate next.

### Agents That Require Manual Invocation

These agents are NOT called by the commander. They are called by a human at specific points:

| Agent | When to Call Manually | Why |
|------|---------------------|-----|
| `workflow_initiator` | At project start, or when resuming after a gap | Needs human to answer setup questions |
| `research_and_review` | Before architecture is finalized | Human decides which reference systems to research |
| `research_and_refine` | Any time a research question needs a structured answer | Needs human-authored `task.md` + `project_root_path`; outputs to `research_results.md` only; never modifies existing docs |
| `identify_missing_documents` | Called by workflow_initiator, or manually before a milestone | Needs current project path |
| `captain_agent` | After 00–05 docs are complete; before commander starts | Needs human to confirm 00–05 are final and locked |

---

## [v1.1] Execution Plan Format

| Phase | Milestone | Task | Subtask | Owner | Input | Output | Validation | Status |
|------|----------|-----|--------|------|------|--------|----------|--------|

Human-readability rule: Group rows visually by milestone using blank separator rows between milestone groups.

---

## [v1.1] Execution Strategies

### [v1.3] Pre-Execution Phase (always required, both strategies)

```
[After 00-05 docs complete]

Human calls captain_agent
  → captain_agent reads FRD + architecture + security docs
  → captain_agent maps services → tasks → milestones
  → captain_agent writes execution_plan.md
  → captain_agent writes 07_Milestones/M*/milestone.md
  → captain_agent validates FRD coverage
  → captain_agent updates tracking_board.md
  → captain_agent sets project_status.md = READY (or PLANNING if gaps remain)

[Now commander_agent can begin]
```

### Strategy A: Single-Agent Execution

```
Human calls Commander Agent
  → Commander reads project_status.md + tracking_board.md
  → Commander finds next Planned subtask
  → Commander calls Execution Agent with task context
  → Execution Agent generates prompt → saves to implementation_prompts/
  → Human approves prompt (one gate)
  → Execution Agent implements → validates
  → Execution Agent updates tracking_board.md: Done
  → Execution Agent reports back to Commander
  → Commander finds next task
```

### Strategy B: Multi-Agent Pipeline

```
Human calls Commander Agent
  → Commander finds next Planned subtask
  → Commander calls Architect Agent

Architect → generates implementation prompt → saves to implementation_prompts/
Reviewer Agent → reviews prompt for security + scale violations
  → if approved: passes to Implementor
  → if rejected: returns to Architect with redline comments
Implementor → executes approved prompt
Validator Agent → runs tests → if pass: updates tracking_board.md: Done → notifies Commander
               → if fail: returns to Implementor with failure details
```

**[v1.2] Notification hook (optional):** For steps requiring human approval (e.g., production deploy), agents post to a Slack/Discord webhook and poll for a reaction before proceeding.

---

## [v1.1] Agent Permission Model

| Level | Scope | Example Actions |
|------|------|---------------|
| READ | Read files, SELECT | Research, gap analysis, plan review |
| WRITE_LOCAL | Create/edit project files | Code, migrations, config |
| WRITE_INFRA | Provision/modify cloud resources | Terraform apply, ECS deploy |
| WRITE_DATA | Mutate production data | Migration, seed |
| ADMIN | Cross-cutting permissions | Secrets, IAM, DNS |

Each agent declares a `## Permissions` section. WRITE_INFRA requires explicit human approval before `apply`.

---

## [v1.5] .gitignore Rule (updated from v1.2)

The workspace `.gitignore` at `{project_name}-Orchestrum/` MUST contain:

```gitignore
# AOSDF — AI Development Model (not project-specific, not committed)
AOSDF/

# Project documentation — planning docs, agent definitions, gap trackers, never committed
{project_name}-Documents/
```

This ensures AI planning artifacts never enter source control. The `.gitignore` lives at the workspace root, not inside the application code directory.

> **v1.2 note:** The old pattern was `aosdf-*/` inside the project repo. v1.5 moves the gitignore to the workspace root and excludes the entire `AOSDF/` and `{project_name}-Documents/` directories.

---

## [v1.4] Document Formatting Standard

**This standard applies to every file created or updated by any agent in any AOSDF project. It is non-negotiable and not overridable at the agent level.**

### Rule 1 — Separator dashes must match column width

Count the maximum character width of each column (header or longest data value, whichever is greater). Fill the separator row with exactly that many dashes.

```
✅ Correct
| Task ID | Task Name                | Owner        | Status    |
| ------- | ------------------------ | ------------ | --------- |

❌ Wrong
| Task ID | Task Name | Owner | Status |
|---------|-----------|-------|--------|
```

### Rule 2 — Data cells must be padded to fill column width

Every value in a column is padded with trailing spaces to match the column width. All rows in a column align to the same width.

```
✅ Correct
| M1-T1   | Infra Provisioning       | Infra        | Planned   |
| M1-T2   | DB Schema                | Backend      | Planned   |

❌ Wrong
| M1-T1 | Infra Provisioning | Infra | Planned |
| M1-T2 | DB Schema | Backend | Planned |
```

### Rule 3 — Column widths are consistent across all files in the same project

When a table schema appears in multiple files (e.g., the task table in every milestone file), determine column widths once from the widest values across all files, then use those same widths everywhere.

### Rule 4 — Blank separator rows between logical groups

In tables that span multiple milestones, phases, or sections, add a blank row between groups to aid human scanning. Example: blank row between M0 rows and M1 rows in `execution_plan.md`.

### Rule 5 — This standard applies to every agent output

Every agent that writes a file containing a table must follow Rules 1–4. This includes:
- `captain_agent` → `execution_plan.md`, `milestone.md` files, `tracking_board.md`
- `execution_agent` / `validator_agent` → `tracking_board.md` updates
- `research_and_refine_agent` → `research_results.md`
- Any agent writing `identified_gaps.md`, `manual_action.md`, or ADR files

**No exceptions for "quick" or "small" tables.** A two-row table must be formatted the same as a fifty-row table.

---

## [v1.6] LLM Wiki Integration

### What the Wiki Is
A persistent, compounding knowledge base maintained by the LLM across sessions.
It lives in `llm-wiki/` and contains structured summaries, entity pages, concept pages,
and session records derived from `{project_name}-Documents/`.

### Agent Read Protocol
Before starting any task involving design, research, or architecture decisions:
1. Read `llm-wiki/index.md` — identify relevant pages
2. Read those pages — extract relevant context
3. Proceed with the task using that context
4. If context is missing from wiki but exists in Documents: use Documents directly;
   note in output that wiki may be stale (human should run `Wiki: re-ingest <file>`)

### Write Boundary (Non-Negotiable)
- Agents: READ from `llm-wiki/` only
- Agents: WRITE to `{project_name}-Documents/` and source code only
- Wiki updates: initiated by human only via `Wiki:` commands in direct session
- After `research_and_refine_agent` runs: human must run `Wiki: re-ingest research_results.md`

### Wiki Sync Trigger Table
After any of these agent actions, the human must sync the wiki:

| Agent Action                             | Files Changed                                                           | Wiki Command                                   |
| ---------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------- |
| captain_agent re-run                     | execution_plan.md, tracking_board.md, project_status.md, identified_gaps.md | `Wiki: full-sync`                         |
| New ADR created                          | ADR file + system_architecture.md                                       | `Wiki: re-ingest <adr-file>`                   |
| research_and_refine_agent run            | research_results.md                                                     | `Wiki: re-ingest research_results.md`          |
| Milestone completed                      | tracking_board.md, project_status.md                                    | `Wiki: re-ingest <each file>`                  |
| New gap logged                           | identified_gaps.md                                                      | `Wiki: re-ingest identified_gaps.md`           |
| Manual action completed                  | manual_action.md                                                        | `Wiki: re-ingest manual_action.md`             |
| block-schema or template-schema updated  | Those files + renderer-contracts.md                                     | `Wiki: re-ingest <each file>`                  |

### Conflict Prevention Rules
1. `llm-wiki/` and `{project_name}-Documents/` have no overlapping files — ever
2. Agents never run `Wiki:` commands — those are human-only
3. Wiki agent never runs AOSDF agent commands (`Dev:` prefix = agent mode)
4. If an agent finds wiki and source document contradict: trust source document;
   flag contradiction in output so human can sync
5. `project_status.md` in Documents is always authoritative over any wiki page about status

---

## Critical Rules

**No code without:** API contract + schema definition + security review (02 complete)

**No agent freedom:** Agents follow prompts exactly. Blocked tasks escalated, not improvised.

**Everything must be:** Versioned | Testable | Traceable

**[v1.1]** Gaps logged to `identified_gaps.md` immediately. Manual steps logged to `manual_action.md` immediately.

**[v1.2]** `project_status.md` = READY before execution. Implementation prompts saved before running. M0 complete before M1.

**[v1.4]** All agent-generated files with tables must follow the Document Formatting Standard. Separator dashes match column width. Data cells padded. Consistent widths across files.
