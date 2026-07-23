# AOSDF Setup Guide
# How to Initialize AOSDF for a New Project + How to Upgrade an Existing Project
# AOSDF v2.2

---

## Overview

This guide walks you through setting up AOSDF for a brand-new project. By the end:
- Your workspace is structured correctly
- All boilerplate files are created
- General agents are copied and ready to customize
- Claude knows what questions to ask and what to build first

**Estimated time:** 20–40 minutes (depending on how much product context you have ready)

---

## Step 1 — Create the Workspace Structure

Create this folder layout manually. Nothing is automated until Claude starts.

```
{ProjectName}-Orchestrum/              ← workspace root (not a git repo itself)
├── AOSDF/                             ← copy this entire AOSDF folder here
├── {ProjectName}/                     ← application code (empty for now)
└── {ProjectName}-Documents/           ← will be created by Claude in Step 3
```

**Copy the AOSDF folder** from wherever you have it into `{ProjectName}-Orchestrum/AOSDF/`.

---

## Step 2 — Prepare the Setup Prompt

Copy the prompt below. Fill in the `[BRACKETS]` with your project details before pasting.

Some answers can be rough — Claude will ask follow-up questions.

---

## THE SETUP PROMPT
> Copy everything from the line below to the END OF PROMPT marker and paste it into a new Claude session.

---

```
You are acting as the AOSDF Workflow Initiator for a new project.

Read the AOSDF framework at: AOSDF/framework.md
Read the general agent templates at: AOSDF/agents/
Read the templates at: AOSDF/templates.md

Your job is to set up this project from scratch following AOSDF v2.2.

---

## Project Context (filled by human)

Project name:        [e.g., Auction Engine]
Workspace root:      [e.g., /Users/yourname/Auction-Engine-Orchestrum]
One-line description: [e.g., Multi-tenant real-time auction platform with bidding, payments, and notifications]
Application code dir: [e.g., Auction-Engine]
Documents dir:       [e.g., Auction-Engine-Documents]

Has UI (Phase 1):    [yes / no]
Primary cloud:       [AWS / GCP / Azure / none / self-hosted]
Tech stack:          [e.g., TypeScript, Node.js, NestJS, PostgreSQL, Redis]
Team size:           [solo / small (2-5) / large (6+)]
Execution strategy:  [Strategy A (single-agent) / Strategy B (multi-agent pipeline) / unsure]
Compliance:          [none / DLT-India / GDPR / HIPAA / PCI / other: specify]
Related systems:     [e.g., "Auth Service (internal)", "Stripe (payments)", "none"]
Phase strategy:      [describe what Phase 1 covers vs future phases, or "TBD"]

---

## What I Need You to Do

Work through these steps in order. Do not skip any step. Ask me to clarify before proceeding if any answer above is missing or unclear.

### Step 1 — Ask Setup Questions

Ask me the following questions. If the answer is already provided above, skip that question.

1. What is the project name? (used for folder naming — no spaces, use hyphens)
2. What does this product do in one sentence? (used to calibrate required documents)
3. Does Phase 1 include a UI? (yes/no — determines if frontend_agent is active)
4. What is the primary cloud provider? (determines infrastructure checklist)
5. What is the tech stack? (language, framework, database, queue, cache)
6. What is the team size? (solo / small / large — informs execution strategy choice)
7. Which execution strategy do you prefer? (Strategy A = single-agent sequential; Strategy B = multi-agent pipeline with reviewer + validator)
8. Are there compliance requirements? (DLT, GDPR, HIPAA, PCI, other — informs security and legal sections)
9. Are there any related or consuming systems? (systems that will call this project's API or receive its events)
10. What does Phase 1 cover? What is explicitly out of scope?

Once I answer, confirm the answers back to me and proceed to Step 2.

### Step 2 — Create the Folder Structure

Create the following directory structure inside `{ProjectName}-Documents/documents/`:

```
documents/
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
│   └── implementation_prompts/
├── 06_Execution_Plan/
├── 07_Milestones/
│   ├── M0_Project_Setup/
│   ├── M1_Foundation/
│   ├── M2_Core_Features/
│   └── M3_Hardening/
├── 08_Tracking_System/
├── 09_Testing_Validation/
├── 10_Deployment_Runbook/
├── 11_Future_Extensibility/
├── 12_Manual_Actions/
├── 13_Legal_Requirements/     (create only if compliance ≠ none)
├── 14_Future_Migrations/      (always create — recommended for all projects)
└── 15_Addendums/
```

Also create at the `{ProjectName}-Documents/` root:
- `project_status.md`
- `identified_gaps.md`
- `reference/` folder with a `README.md` (see Step 3a)

### Step 3 — Create Initial Files

Create the following files with their starter content:

#### `{ProjectName}-Documents/reference/README.md`
```markdown
# Reference — Raw Product Knowledge
# {ProjectName}

This folder holds raw product knowledge documents — source material that informs the structured 00–05 docs.
Agents READ this folder. No agent writes to or modifies files here.

## What Goes Here
- Product briefs, vision docs, pitch deck content, founder notes
- Raw stakeholder requirements (before structured into PRD/FRD)
- User research: interview notes, survey results, persona sketches
- Competitor / market research
- Vendor / API documentation excerpts (e.g., Twilio, Stripe, Supabase)
- Integration specs from systems this project connects to
- Design references: brand guidelines, UI inspiration (if has_ui: true)

## What Does NOT Go Here
- Structured docs (PRD, FRD, BRD) → 01_Project_Definition/
- Architecture decisions → 03_System_Design/
- Agent research output → research_results.md at Documents root

## Index
| File | Type | Description | Date Added |
| ---- | ---- | ----------- | ---------- |
|      |      |             |            |
```

**Ask the human:** "Do you have any raw product documents to add to `reference/` now? (product briefs, research notes, vendor docs, stakeholder requirements)"
- If yes: list them and explain the folder is ready to receive them
- If no: note that the folder is ready whenever documents are available

---

#### `{ProjectName}-Documents/project_status.md`
```markdown
# Project Status
# {ProjectName}
# AOSDF v2.2

**Status:** SETUP

## Milestone Progress
| Milestone | Name          | Status  | Started | Completed |
| --------- | ------------- | ------- | ------- | --------- |
| M0        | Project Setup | Planned |         |           |
| M1        | Foundation    | Planned |         |           |
| M2        | Core Features | Planned |         |           |
| M3        | Hardening     | Planned |         |           |

## Status History
| Date | Status     | Notes                |
| ---- | ---------- | -------------------- |
| [today] | SETUP  | Project initialized  |
```

#### `{ProjectName}-Documents/identified_gaps.md`
```markdown
# Identified Gaps
# {ProjectName}
# AOSDF v2.2

All gaps identified during development are logged here immediately.
Never defer gap logging — log it now, resolve it later.

## Open Gaps

| Gap ID | Category      | Severity | Description | Resolution | Status |
| ------ | ------------- | -------- | ----------- | ---------- | ------ |
|        |               |          |             |            |        |

## Resolved Gaps

| Gap ID | Category | Description | Resolution | Resolved Date |
| ------ | -------- | ----------- | ---------- | ------------- |
|        |          |             |            |               |
```

#### `{ProjectName}-Documents/documents/12_Manual_Actions/actions.md`
```markdown
# Manual Actions Tracker
# {ProjectName}
# AOSDF v2.2 [v1.7]

All human-required steps are logged here. Never defer — log the row before finishing the task that generates it.

## Pending Actions

| Action ID | Description | Milestone Task | Blocks | Category | Priority | Dev Status | Staging Status | Prod Status | Owner |
| --------- | ----------- | -------------- | ------ | -------- | -------- | ---------- | -------------- | ----------- | ----- |
|           |             |                |        |          |          |            |                |             |       |

## Completed Actions

| Action ID | Description | Completed Date | Notes |
| --------- | ----------- | -------------- | ----- |
|           |             |                |       |
```

#### `{ProjectName}-Documents/documents/12_Manual_Actions/guides.md`
```markdown
# Manual Action Guides
# {ProjectName}
# AOSDF v2.2 [v1.7]

Step-by-step instructions for each action ID. Add a section here when a new action is logged in actions.md.

---

<!-- Template for each action:

## MA-001 — <Action Name>
**Category:** Infrastructure | Credentials | Compliance | DNS | Other
**Priority:** P1 | P2 | P3

### Steps
1. <step 1>
2. <step 2>

### Validation
- <how to confirm this is done>

-->
```

#### `{ProjectName}-Documents/documents/14_Future_Migrations/alternatives.md`
```markdown
# Future Migrations — Alternatives & Portability Guide
# {ProjectName}
# AOSDF v2.0

> Required reading for captain_agent and any architecture agent.
> Every infrastructure client must be wrapped behind an abstraction interface.

## Portability-First Principle

All infrastructure clients (database, queue, cache, storage, secrets) must be wrapped behind
abstraction interfaces. Provider SDK calls are confined to adapter implementation files only —
never in business logic. Swapping a provider must require only a new adapter, not a business-logic change.

## Infrastructure Alternatives by Layer

| Layer          | Current Choice | OSS / Self-hosted Alternative | Cloud Alternative | Migration Complexity |
| -------------- | -------------- | ----------------------------- | ----------------- | -------------------- |
| Database       | [e.g., RDS PostgreSQL] | [e.g., Supabase, self-hosted Postgres] | [e.g., Cloud SQL, AlloyDB] | Low |
| Queue          | [e.g., SQS] | [e.g., RabbitMQ, NATS] | [e.g., Google Pub/Sub] | Medium |
| Cache          | [e.g., ElastiCache] | [e.g., Valkey, self-hosted Redis] | [e.g., Memorystore] | Low |
| Storage        | [e.g., S3] | [e.g., MinIO] | [e.g., GCS, Azure Blob] | Medium |
| Secrets        | [e.g., Secrets Manager] | [e.g., Vault, Infisical] | [e.g., Secret Manager] | Low |
| Compute        | [e.g., ECS Fargate] | [e.g., Docker Compose, k8s] | [e.g., Cloud Run, GKE] | High |

## Agent Design Guidelines

- Every infrastructure client has an interface: `IQueueClient`, `ICacheClient`, `IStorageClient`, etc.
- Adapter files implement the interface for a specific provider
- Business logic imports only the interface — never the SDK directly
- Provider configuration is injected, not hardcoded

## Migration Timeline (By Blast Radius)

| Phase | What Can Be Swapped | Risk Level |
| ----- | ------------------- | ---------- |
| Phase 1 | Secrets, cache | Low — stateless or easily flushed |
| Phase 2 | Queue | Medium — requires consumer migration |
| Phase 3 | Storage, compute | High — data migration required |
| Phase 4 | Database | Very high — full data migration + downtime window |
```

### Step 4 — Create Boilerplate Project Context

Create `{ProjectName}-Documents/documents/00_Project_Context/project_context.md` with a starter template based on my answers. Fill in what you know; leave placeholders for what the human must fill.

Use this structure:
```markdown
# Project Context
# {ProjectName}

## System Name
{ProjectName}

## Problem Statement
[Fill in: what problem does this product solve?]

## Target Users
[Fill in: who uses this product?]

## Business Context
[Fill in: why are we building this now? what's the business motivation?]

## Constraints
- Team size: {team_size}
- Primary cloud: {cloud}
- Tech stack: {tech_stack}
- Phase 1 timeline: [Fill in]
- Compliance: {compliance}

## Phase Strategy
### Phase 1 (Current)
{phase_1_scope}

### Phase 2 (Future)
[Fill in: what comes after Phase 1]

## Related Systems
{related_systems}
```

### Step 5 — Copy and Label General Agents

Copy all files from `AOSDF/agents/` into `{ProjectName}-Documents/documents/05_AI_Agent_System/agents/`.

For each agent file copied:
- Replace `{project_name}` with the actual project name
- Add a `## Project: {ProjectName}` header below the role
- Do NOT customize the constraints yet — that comes after the human fills 00–05 docs

If `has_ui: false`: update `frontend_agent.md` Phase Status to INACTIVE with a note.

Both `captain_agent.md` and `research_and_refine_agent.md` are already in `AOSDF/agents/` — copy them along with the rest.

### Step 6 — Create Prompt Templates

Create the three standard prompt templates in `05_AI_Agent_System/prompt_templates/`:

#### `task_prompt.md`
```markdown
# Task Prompt Template
# Fill this template for each implementation task

## Context
Project: {project_name}
CLAUDE.md: [path]
Current milestone: [milestone name]
Task ID: [e.g., M1-T2]

## Task Definition
[Precise description of what needs to be built]

## Constraints
- [Constraint from CLAUDE.md]
- [Constraint from FRD]

## Input
- File: [path to input file or inline schema]

## Expected Output
- File: [output file path and format]

## Validation Criteria
- [ ] [Binary pass/fail condition 1]
- [ ] [Binary pass/fail condition 2]
- [ ] All tests pass
- [ ] No hardcoded secrets
```

#### `review_prompt.md`
```markdown
# Review Prompt Template

## Context
Reviewing implementation for Task: [Task ID]
Prompt file: [path]

## Review Checklist
- [ ] Security: no secrets in code, auth required, inputs validated
- [ ] Architecture: no service boundary violations, contract-first respected
- [ ] Scalability: no blocking calls without timeout, no N+1 queries
- [ ] Tests: unit + integration tests specified
- [ ] Traceability: output traces to FRD requirement

## Decision
[ ] Approved
[ ] Redlined — see issues below

## Issues (if redlined)
1. [Issue + prompt section + rule violated]
```

#### `debug_prompt.md`
```markdown
# Debug Prompt Template

## Context
Project: {project_name}
Task ID: [Task ID]
Failure point: [where in the validation did it fail]

## Failure Description
[Exact error or test output]

## What Was Tried
[Steps already attempted]

## Constraints (must not be violated during fix)
- [Constraint 1]
- [Constraint 2]

## Expected Fix Output
- Same file path(s) as original task
- All validation criteria must pass after fix
```

### Step 7 — Create CLAUDE.md

Create `{ProjectName}-Documents/CLAUDE.md` as the authoritative context file for all agents. Use the answers from Step 1 to populate it.

Structure (required sections):
```markdown
# CLAUDE.md — {ProjectName} Development Context

Read this before doing anything. Follow every rule here. No exceptions.

## 1. What We Are Building
[Product name, definition, primary consumer, future vision]

## 2. Framework — AOSDF v2.2
[Note that this project follows AOSDF v2.2. List key principles.]

## 3. Execution Strategy
[Strategy A or B. Entry point each session. Commander reads project_status.md.]

## 4. Project Root Structure
[Workspace layout showing all directories]

## 5. System Architecture
[Fill after 03_System_Design is complete]

## 6. Key Domain Concepts
[Fill after 01_Product_Definition is complete]

## 7. Infrastructure
[Fill after 04_Infrastructure_Design is complete]

## 8. Non-Functional Targets
[Fill after PRD is complete]

## 9. Security Rules
[Fill after 02_Security_Framework is complete]

## 10. Engineering Constraints
[Team size, timeline, cloud constraints, strict non-goals]

## 11. Agent Execution Rules
[Must read this file, contract-first, test alongside code, no git push by agents]

## 12. Phase Strategy
[Phase 1 scope, Phase 2, Phase 3]

## 13. Document Status
[Table of all docs with completion status]

## 14. Gap & Manual Action Summary
[Pointers to identified_gaps.md and 12_Manual_Actions/actions.md]
```

### Step 8 — Create Workspace .gitignore

Create `.gitignore` at `{ProjectName}-Orchestrum/` (workspace root):
```gitignore
# AOSDF — AI Development Model (not project-specific, not committed)
AOSDF/

# Project documentation — planning docs, agent definitions, gap trackers, never committed
{ProjectName}-Documents/
```

### Step 9 — Report Project Readiness

Output a structured readiness report:

```
=== AOSDF Setup Complete ===
Project: {ProjectName}
AOSDF Version: v2.2
Date: {today}

✅ Created:
  - {ProjectName}-Documents/ folder structure (00–15 sections)
  - project_status.md (Status: SETUP)
  - identified_gaps.md (empty)
  - 12_Manual_Actions/actions.md + guides.md
  - 14_Future_Migrations/alternatives.md (starter)
  - 05_AI_Agent_System/agents/ (all {N} agents copied)
  - 05_AI_Agent_System/prompt_templates/ (3 templates)
  - 00_Project_Context/project_context.md (starter)
  - CLAUDE.md (shell — sections 5-13 need product content)
  - .gitignore at workspace root

⚠️  Human input required before captain_agent can run:
  1. 01_Project_Definition/PRD.md       — product requirements
  2. 01_Project_Definition/FRD.md       — functional requirements + service specs
  3. 01_Project_Definition/BRD.md       — business rules + SLA targets
  4. 02_Security_Framework/security_requirements.md
  5. 02_Security_Framework/threat_model.md
  6. 02_Security_Framework/compliance_checklist.md
  7. 03_System_Design/system_architecture.md
  8. 03_System_Design/service_design.md
  9. 03_System_Design/data_flow.md
  10. 04_Infrastructure_Design/infra_architecture.md
  11. 04_Infrastructure_Design/scaling_strategy.md
  12. 04_Infrastructure_Design/cost_estimation.md
  13. 04_Infrastructure_Design/observability.md
  [If compliance ≠ none] 14. 13_Legal_Requirements/concern_1.md

🔲 Optional but recommended before captain_agent:
  - Research pass: call research_and_review_agent before locking 03_System_Design
  - Fill 14_Future_Migrations/alternatives.md with project-specific alternatives
  - Initialize llm-wiki/ (run LLM Wiki setup prompt)

📋 Next steps:
  1. Fill the ⚠️ documents above
  2. Run: call captain_agent (after all 00–05 docs are complete and locked)
  3. captain_agent will generate execution_plan.md + milestones + tracking board
  4. Status will advance: SETUP → PLANNING → READY
  5. Once READY: call commander_agent to start execution
```

---

## END OF PROMPT
```

---

## Step 3 — After Claude Runs the Setup Prompt

After Claude finishes, you will have a skeleton project. Here is what still requires human input before execution can begin:

### Required Human-Authored Documents (00–05)

These cannot be generated by AI — they require your product knowledge:

| Document | Section | What to Write |
| -------- | ------- | ------------- |
| `PRD.md` | 01 | What the product does, non-functional requirements, what's explicitly out of scope |
| `FRD.md` | 01 | Every service, every API endpoint, every acceptance criterion — this drives the execution plan |
| `BRD.md` | 01 | Business rules, SLA targets, retry policies, pricing constraints |
| `security_requirements.md` | 02 | Auth model, secrets management, data protection rules |
| `threat_model.md` | 02 | Attack surface, threat scenarios, mitigations |
| `compliance_checklist.md` | 02 | Compliance requirements and how each is addressed |
| `system_architecture.md` | 03 | Services, how they connect, core architectural principles |
| `service_design.md` | 03 | Per-service responsibilities, contracts, boundary rules |
| `data_flow.md` | 03 | How data moves between services, queue flows, ordering constraints |
| `infra_architecture.md` | 04 | What infrastructure components are needed and why |
| `scaling_strategy.md` | 04 | How the system scales under load |
| `cost_estimation.md` | 04 | Monthly cost breakdown at expected scale |
| `observability.md` | 04 | Logging, metrics, alerting strategy |

### Required Agent Customization (05)

After filling 00–04, go into each agent file in `05_AI_Agent_System/agents/` and:
1. Add project-specific constraints to each agent's Constraints section
2. Add project-specific service boundary rules to `architect_agent.md` and `backend_agent.md`
3. Add project-specific security rules to `backend_agent.md` and `qa_agent.md`
4. Set `frontend_agent.md` phase status based on whether Phase 1 has UI

### Optional but Recommended

- **LLM Wiki**: run the LLM Wiki setup prompt to initialize `llm-wiki/`
- **Research pass**: run `research_and_review_agent` before finalizing `03_System_Design/`
- **14_Future_Migrations**: fill `alternatives.md` with project-specific portability options

---

## Step 4 — Running captain_agent

Once all 00–05 documents are complete and locked:

```
Call captain_agent.

Project: {ProjectName}
AOSDF docs root: {ProjectName}-Documents/

Please:
1. Read all 00–05 documents (FRD, PRD, BRD, security, architecture, infra)
2. Read 13_Legal_Requirements/ (if present — all files)
3. Read 14_Future_Migrations/alternatives.md (if present)
4. Extract all services, security controls, and infra components
5. Map them to tasks grouped into milestones M0–M3 (or M0–M4 if needed)
6. Write execution_plan.md (flat Phase→Milestone→Task→Subtask table)
7. Write each milestone.md with task table, exit criteria, and dependencies
8. Write 08_Tracking_System/decisions_log.md if absent (decisions log only — not a task board)
9. Validate FRD coverage — every service must have ≥1 task
10. Log unmapped requirements to identified_gaps.md as Critical gaps
11. Set project_status.md → READY if coverage is complete
```

---

## Step 5 — Starting Execution

Once `project_status.md` = `READY`:

```
Call commander_agent.

Project: {ProjectName}
AOSDF docs root: {ProjectName}-Documents/
Execution strategy: Strategy A [or B]

Please:
1. Read project_status.md and execution_plan.md
2. Identify the next Planned task (Status column — the only status record)
3. Verify no blocking manual actions for this milestone
4. Run Gap Validation Gate (Step 2.5)
5. Delegate to execution_agent with full context
```

Repeat this at the start of every session. Compact between sessions.

---

## Questions Claude Will Ask During Setup

When you paste the Setup Prompt, Claude will ask these if your answers are missing or unclear:

| # | Question | Why It Matters |
|---|----------|---------------|
| 1 | Project name | Used for folder naming throughout the workspace |
| 2 | One-line product description | Calibrates which sections are required |
| 3 | Has UI in Phase 1? | Determines if frontend_agent is active + if design_language_system.md is required |
| 4 | Cloud provider | Determines infrastructure checklist and IaC tool |
| 5 | Tech stack | Used in CLAUDE.md and agent constraint files |
| 6 | Team size | Solo → Strategy A default; larger → Strategy B may be better |
| 7 | Execution strategy | Determines which agents are active (reviewer + validator only needed for B) |
| 8 | Compliance requirements | Triggers 13_Legal_Requirements/ creation and compliance_checklist.md sections |
| 9 | Related systems | Populates CLAUDE.md integration section |
| 10 | Phase 1 scope | Sets non-goals in CLAUDE.md; prevents scope creep during execution |

---

## What You Get After Setup

```
{ProjectName}-Orchestrum/
├── .gitignore                          ← excludes AOSDF/ and Documents/ from git
├── AOSDF/                              ← framework (shared, not project-specific)
├── {ProjectName}/                      ← application code (empty — M0 creates it)
└── {ProjectName}-Documents/
    ├── CLAUDE.md                       ← agent context (shell — fill sections 5-13)
    ├── project_status.md               ← Status: SETUP
    ├── identified_gaps.md              ← empty tracker
    ├── reference/
    │   └── README.md                   ← ready to receive raw product docs
    └── documents/
        ├── 00_Project_Context/
        │   └── project_context.md      ← starter with your answers
        ├── 01_Project_Definition/      ← EMPTY — requires human input
        ├── 02_Security_Framework/      ← EMPTY — requires human input
        ├── 03_System_Design/ADR/
        ├── 04_Infrastructure_Design/   ← EMPTY — requires human input
        ├── 05_AI_Agent_System/
        │   ├── agents/                 ← 13 agents copied from AOSDF, {project_name} replaced
        │   ├── prompt_templates/       ← 3 templates
        │   └── implementation_prompts/ ← empty (filled by execution agent)
        ├── 06_Execution_Plan/          ← filled by captain_agent
        ├── 07_Milestones/              ← filled by captain_agent
        ├── 08_Tracking_System/         ← filled by captain_agent
        ├── 09_Testing_Validation/      ← EMPTY — requires human input or QA agent
        ├── 10_Deployment_Runbook/      ← EMPTY — requires human input or infra agent
        ├── 11_Future_Extensibility/    ← EMPTY — fill after M0
        ├── 12_Manual_Actions/
        │   ├── actions.md              ← empty tracker (header created)
        │   └── guides.md               ← empty guide (header created)
        ├── 13_Legal_Requirements/      ← created only if compliance ≠ none
        ├── 14_Future_Migrations/
        │   └── alternatives.md         ← starter with infrastructure alternatives table
        └── 15_Addendums/               ← empty (used post-baseline by addendum_agent)
```

---

## Additional Actions Required in the New Project

Beyond what Claude creates automatically, these actions must be taken manually or documented:

| Action | When | Who | Notes |
| ------ | ---- | --- | ----- |
| Fill PRD, FRD, BRD | Before captain_agent | Human | Product-specific — cannot be auto-generated |
| Fill 02_Security_Framework | Before captain_agent | Human | Security doc must exist before any coding |
| Fill 03_System_Design | Before captain_agent | Human | Run research_and_review first if uncertain |
| Fill 04_Infrastructure_Design | Before captain_agent | Human | Include cost_estimation.md |
| Customize agents in 05/ | After filling 00-04 | Human | Add project-specific constraints and boundary rules |
| Initialize llm-wiki/ | Before first execution session | Human | Run LLM Wiki setup prompt |
| Sync wiki after setup | After CLAUDE.md is filled | Human | `Wiki: ingest all` |
| Fill 14_Future_Migrations/alternatives.md | Before captain_agent | Human | Add project-specific portability options |
| Create 13_Legal_Requirements/*.md | Before captain_agent (if applicable) | Human | One file per legal topic |
| Review + approve captain_agent plan | After captain_agent runs | Human | Before first commander session |
| Register external credentials | Before M2 typically | Human | API keys, cloud accounts, DNS — add to 12_Manual_Actions/ |

---

## Checklist: Ready to Call captain_agent?

- [ ] `00_Project_Context/project_context.md` — filled
- [ ] `01_Project_Definition/PRD.md` — complete
- [ ] `01_Project_Definition/FRD.md` — complete (all services + API endpoints + acceptance criteria)
- [ ] `01_Project_Definition/BRD.md` — complete
- [ ] `02_Security_Framework/security_requirements.md` — complete
- [ ] `02_Security_Framework/threat_model.md` — complete
- [ ] `02_Security_Framework/compliance_checklist.md` — complete
- [ ] `03_System_Design/system_architecture.md` — complete
- [ ] `03_System_Design/service_design.md` — complete
- [ ] `03_System_Design/data_flow.md` — complete
- [ ] `04_Infrastructure_Design/infra_architecture.md` — complete
- [ ] `04_Infrastructure_Design/scaling_strategy.md` — complete
- [ ] `04_Infrastructure_Design/cost_estimation.md` — complete
- [ ] `04_Infrastructure_Design/observability.md` — complete
- [ ] `05_AI_Agent_System/agents/` — all agents customized for this project
- [ ] `14_Future_Migrations/alternatives.md` — filled with project-specific alternatives
- [ ] `13_Legal_Requirements/` — populated if compliance ≠ none
- [ ] `CLAUDE.md` — all sections filled (not just the shell)
- [ ] `llm-wiki/` — initialized and synced

If all checked → call `captain_agent`. If not → fill the missing items first.

---

---

# How to Upgrade AOSDF for an Already-Setup Project

> Use this section if you already have AOSDF running on a project and want to bring it up to v2.2.
> Work through the steps in order. Each step is independent — skip any that are already done.

---

## What Changed in v2.2 (Summary of Gaps to Fix)

| Change | Version | What to Do |
| ------ | ------- | ---------- |
| `AOSDF/agents/` folder — all agents moved here | v2.2 | Replace your AOSDF copy; update any agent references |
| `AOSDF/reference/` folder — 4 quick-reference docs | v2.2 | Add to your AOSDF copy |
| `reviewer_agent.md` + `validator_agent.md` | v1.3 | Add to project's `05_AI_Agent_System/agents/` |
| `addendum_agent.md` | v2.1 | Add to project's `05_AI_Agent_System/agents/` |
| `12_Manual_Actions/` — two-file system | v1.7 | Create folder, migrate legacy `manual_action.md` |
| `14_Future_Migrations/alternatives.md` | v2.0 | Create if missing |
| `15_Addendums/` directory | v2.1 | Create if missing |
| `commander_agent.md` — Gap Validation Gate (Step 2.5) | v1.3+ | Add to project's commander agent |
| `commander_agent.md` — uses `12_Manual_Actions/` | v1.7 | Update `manual_action.md` references |
| `execution_agent.md` — uses `12_Manual_Actions/` | v1.7 | Update `manual_action.md` references |
| `captain_agent.md` — reads `13_Legal_Requirements/` + `14_Future_Migrations/` | v1.9/v2.0 | Ensure project captain agent reads these sections |

---

## Step-by-Step Upgrade

### Step U1 — Replace Your AOSDF Folder

Replace the `AOSDF/` folder in your workspace root with the latest version.

If you want to keep local customizations:
- `AOSDF/designing_aosfd/` — safe to keep your existing copy
- All other files — replace with latest versions
- The new `AOSDF/agents/` folder replaces the old root-level `captain_agent.md` and `research_and_refine_agent.md`

**Verify after replacement:**
```
AOSDF/
├── agents/           ← 14 agent files (incl. identify_missing_documents.md)
├── reference/        ← 4 reference files
├── framework.md
├── manual.md
├── setup_aosdf.md
├── workflow_initiator.md
└── templates.md
```

---

### Step U2 — Add Missing Agents to Your Project

Copy these agents from `AOSDF/agents/` into your project's `{ProjectName}-Documents/documents/05_AI_Agent_System/agents/`:

**Always missing in pre-v2.2 projects:**
- `reviewer_agent.md` — Strategy B reviewer (mark INACTIVE if you use Strategy A)
- `validator_agent.md` — Strategy B validator (mark INACTIVE if you use Strategy A)
- `addendum_agent.md` — Post-baseline change planning

**For each copied file:**
1. Replace `{project_name}` with your project name
2. Add project-specific constraints (copy from your existing agents as reference)
3. If Strategy A: add `> **Status:** INACTIVE — [ProjectName] uses Strategy A.` to reviewer and validator

---

### Step U3 — Create `12_Manual_Actions/` (if using legacy `manual_action.md`)

**Check if already done:**
```
ls {ProjectName}-Documents/documents/12_Manual_Actions/
```
If the folder exists with `actions.md` and `guides.md`, skip this step.

**If not done:**

1. Create the directory: `{ProjectName}-Documents/documents/12_Manual_Actions/`

2. Create `actions.md` with this header:
```markdown
# Manual Actions Tracker
# {ProjectName}
# AOSDF v2.2 [v1.7]

## Pending Actions

| Action ID | Description | Milestone Task | Blocks | Category | Priority | Dev Status | Staging Status | Prod Status | Owner |
| --------- | ----------- | -------------- | ------ | -------- | -------- | ---------- | -------------- | ----------- | ----- |
```

3. Create `guides.md` with this header:
```markdown
# Manual Action Guides
# {ProjectName}
# AOSDF v2.2 [v1.7]
```

4. **Migrate legacy `manual_action.md`:**
   - Move all pending action rows into `actions.md`'s Pending table
   - Add Dev/Staging/Prod status columns (default to `Pending`)
   - Move any step-by-step instructions into `guides.md` as `## MA-NNN — <Name>` sections
   - Archive `manual_action.md` by renaming it to `manual_action.md.archived`

5. Update `CLAUDE.md` — change any reference from `manual_action.md` to `12_Manual_Actions/actions.md`

---

### Step U4 — Create `14_Future_Migrations/` (if missing)

**Check if already done:**
```
ls {ProjectName}-Documents/documents/14_Future_Migrations/
```

**If not done:**

1. Create the directory
2. Create `alternatives.md` using the starter template from Step 3 of the Setup Prompt (or copy from the project you've already set up)
3. Fill in your project's actual infrastructure alternatives
4. Sync wiki: `Wiki: ingest 14_Future_Migrations/alternatives.md`

---

### Step U5a — Create `reference/` (if missing)

Create `{ProjectName}-Documents/reference/` with a `README.md`.

Use the README template from `AOSDF/templates/reference_readme.md`, replacing `{ProjectName}`.

Then add any raw product knowledge documents you have — product briefs, research notes, vendor docs, stakeholder requirements. These are read-only source material for agents and humans.

---

### Step U5b — Create `15_Addendums/` (if missing)

Create the directory: `{ProjectName}-Documents/documents/15_Addendums/`

No files needed initially — `addendum_agent` creates them when called.

---

### Step U6 — Update Your commander_agent.md

Open your project's `05_AI_Agent_System/agents/commander_agent.md`.

**Fix 1 — Add Gap Validation Gate (Step 2.5)** between Step 2 and Step 3:

```markdown
### Step 2.5 — Gap Validation Gate (MANDATORY — runs before every delegation)

Read `identified_gaps.md` and check for any gap where ALL of the following are true:
1. `Status` = `Open`
2. `Severity` = `Critical` or `High`
3. The gap's Category or Resolution note references the same service, feature, or data model as the task about to be delegated

If such a gap exists: **STOP. Do not delegate.** Report to the human:
```
=== GAP BLOCK ===
Task [TASK-ID] is blocked by [GAP-ID] ([Severity], Open).
[GAP-ID] affects the same [component].
Implement or Accept [GAP-ID] before [TASK-ID] is executed.
```

Only continue after the human resolves the gap (marks it Resolved, In Progress with scope-out, or Accepted).
```

**Fix 2 — Update manual action references:**
- Find every reference to `manual_action.md` in commander_agent.md
- Replace with `12_Manual_Actions/actions.md`

---

### Step U7 — Update Your execution_agent.md

Open your project's `05_AI_Agent_System/agents/execution_agent.md`.

Replace every reference to `manual_action.md` with `12_Manual_Actions/actions.md`.

Also verify Step 6 in the agent says:
```
If a manual action is needed: add to `12_Manual_Actions/actions.md` immediately (never defer).
```

---

### Step U8 — Update CLAUDE.md

1. Update the AOSDF version line to: `This project follows AOSDF v2.2`
2. Replace any remaining `manual_action.md` references with `12_Manual_Actions/actions.md`
3. Update the workspace layout diagram to show `agents/` under AOSDF and the new `reference/` folder
4. Add `15_Addendums/` to the folder structure if not present
5. Add the two new agents (reviewer, validator, addendum) to the Agent Status table in section 15

---

### Step U9 — Sync the Wiki

After all steps above are done:

```
Wiki: full-sync
```

This updates the wiki with all the new files, new agents, and updated CLAUDE.md.

---

## Quick Checklist — Upgrade Complete?

- [ ] AOSDF/ folder replaced with v2.2 (agents/ and reference/ folders present)
- [ ] `reviewer_agent.md` added to `05_AI_Agent_System/agents/`
- [ ] `validator_agent.md` added to `05_AI_Agent_System/agents/`
- [ ] `addendum_agent.md` added to `05_AI_Agent_System/agents/`
- [ ] `12_Manual_Actions/actions.md` + `guides.md` created
- [ ] Legacy `manual_action.md` migrated and archived
- [ ] `14_Future_Migrations/alternatives.md` created
- [ ] `reference/` directory created with `README.md`
- [ ] `15_Addendums/` directory created
- [ ] `commander_agent.md` — Step 2.5 Gap Validation Gate added
- [ ] `commander_agent.md` — `manual_action.md` refs updated to `12_Manual_Actions/actions.md`
- [ ] `execution_agent.md` — `manual_action.md` refs updated to `12_Manual_Actions/actions.md`
- [ ] `CLAUDE.md` — version updated to v2.2, refs updated
- [ ] Wiki synced: `Wiki: full-sync`
