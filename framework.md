# AI-Orchestrated Software Development Framework (AOSDF)
# Version 2.3

---

## How AOSDF Works — Simulation Flow

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                         AOSDF — Full Lifecycle Flow                              ║
╚══════════════════════════════════════════════════════════════════════════════════╝

 ┌─────────────────────────────────────────────────────────────────────────────┐
 │  PHASE 0 — DOCUMENTATION  (Human-driven, one-time)                          │
 │                                                                             │
 │  Human writes:                                                              │
 │  00_Project_Context → 01_Product_Definition (PRD/FRD/BRD)                   │
 │                      → 02_Security_Framework                                │
 │                      → 03_System_Design (+ ADRs)                      │
 │                      → 04_Infrastructure_Design                             │
 │                      → 05_AI_Agent_System                                   │
 │                      → 13_Legal_Requirements (optional)                     │
 │                      → 14_Future_Migrations  (optional)                     │
 │                                                                             │
 │  Human runs:  Wiki: ingest all  ──► llm-wiki/ populated                     │
 └───────────────────────────┬─────────────────────────────────────────────────┘
                             │  all 00–05 docs complete & locked
                             ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │  PHASE 0 — PLANNING  (captain_agent — called once by Human)                 │
 │                                                                             │
 │  captain_agent reads:                                                       │
 │    llm-wiki/index.md + overview.md  (context layer)                         │
 │    FRD, PRD, BRD, security, architecture, infra docs                        │
 │    13_Legal_Requirements/*.md  (if exists)                                  │
 │    14_Future_Migrations/alternatives.md  (if exists)                        │
 │                                                                             │
 │  captain_agent produces:                                                    │
 │    06_Execution_Plan/execution_plan.md  (the only task-status record)       │
 │    07_Milestones/M{0–3}_*/milestone.md                                      │
 │    08_Tracking_System/decisions_log.md  (if absent — decisions log only)    │
 │    identified_gaps.md  (coverage gaps → Critical)                           │
 │                                                                             │
 │  Validates FRD coverage → every service spec maps to ≥1 task                │
 │  Sets: project_status.md ──► READY  (or PLANNING if gaps remain)            │
 └───────────────────────────┬─────────────────────────────────────────────────┘
                             │  project_status = READY
                             ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │  PHASE 1–3 — EXECUTION  (per-session loop, Human starts each session)       │
 │                                                                             │
 │  ┌─────────────┐  compact session                                           │
 │  │   Human     │──────────────────────────────────────────────┐             │
 │  │  invokes    │                                              │             │
 │  │  commander  │                                              ▼             │
 │  └──────┬──────┘                               ┌─────────────────────────┐  │
 │         │                                      │  [compact → re-invoke]  │  │
 │         ▼                                      └─────────────────────────┘  │
 │  ┌─────────────────────────────────┐                                        │
 │  │       commander_agent           │                                        │
 │  │  reads project_status.md        │                                        │
 │  │  reads execution_plan.md        │                                        │
 │  │  finds next Planned subtask     │                                        │
 │  └──────────────┬──────────────────┘                                        │
 │                 │                                                           │
 │        ┌────────┴────────┐                                                  │
 │        │                 │                                                  │
 │   Strategy A        Strategy B                                              │
 │        │                 │                                                  │
 │        ▼                 ▼                                                  │
 │  ┌───────────┐    ┌──────────────┐                                          │
 │  │ execution │    │  architect   │──► reviewer ──► implementor ──► validator│
 │  │  _agent   │    │   _agent     │       ↑ redline if rejected              │
 │  └─────┬─────┘    └──────────────┘                                          │
 │        │                 │  (validator updates execution_plan.md Status)    │
 │        │                 │                                                  │
 │        └────────┬────────┘                                                  │
 │                 ▼                                                           │
 │  ┌──────────────────────────────────────────────────────────────┐           │
 │  │  For each task:                                              │           │
 │  │  generate prompt → save to implementation_prompts/           │           │
 │  │  → Human approves → execute → validate → execution_plan Done │           │
 │  └──────────────────────────────────────────────────────────────┘           │
 └───────────────────────────┬─────────────────────────────────────────────────┘
                             │  all M3 exit criteria pass
                             ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │  DONE — commander_agent sets project_status.md ──► COMPLETE                 │
 └─────────────────────────────────────────────────────────────────────────────┘

 ─────────────────────────────────────────────────────────────────────────────
  SCOPE CHANGE at any point:  Human re-runs captain_agent
    → diffs new plan against execution_plan.md (Done rows preserved)
    → appends new tasks, marks removed tasks Cancelled
    → project_status stays IN_PROGRESS if execution had started
 ─────────────────────────────────────────────────────────────────────────────

  MANUAL ACTIONS (any agent, any time):
    identified gap   ──► identified_gaps.md  (immediate, never deferred)
    human step found ──► 12_Manual_Actions/actions.md  (immediate)

  WIKI SYNC (Human, after agent actions that change docs):
    Wiki: re-ingest <file>  |  Wiki: full-sync  |  Wiki: ingest <new-file>

  ADDENDUMS (any time after M0, for post-baseline cross-cutting requirements):
    Human writes 15_Addendums/<slug>.md
    Human calls addendum_agent ──► <slug>_plan.md + tracking_addendums.md (scoped to 15_Addendums/)
    Main execution_plan.md and milestone files are NOT touched
```

---

> Changes in v1.1 are marked `[v1.1]`
> Changes in v1.2 are marked `[v1.2]`
> Changes in v1.3 are marked `[v1.3]`
> Changes in v1.4 are marked `[v1.4]`
> Changes in v1.5 are marked `[v1.5]`
> Changes in v1.6 are marked `[v1.6]`
> Changes in v1.7 are marked `[v1.7]`
> Changes in v1.8 are marked `[v1.8]`
> Changes in v1.9 are marked `[v1.9]`
> Changes in v2.0 are marked `[v2.0]`
> Changes in v2.1 are marked `[v2.1]`

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
- **[v1.7]** Introduces `12_Manual_Actions/` as a structured two-file system: `actions.md` (tracker with per-environment status + milestone reference) and `guides.md` (step-by-step instructions); supersedes the flat `manual_action.md` root file
- **[v1.9]** Introduces `13_Legal_Requirements/` as an optional section — when present, all files are required reading for `captain_agent` and any architecture agent before planning or design work begins; legal constraints must produce concrete execution plan tasks
- **[v2.0]** Introduces `14_Future_Migrations/` as a portability reference section — `alternatives.md` is required reading for `captain_agent` and any architecture agent; every infrastructure client must be wrapped behind an abstraction interface so providers can be swapped without business-logic rewrites
- **[v2.1]** Introduces `15_Addendums/` as a post-baseline change management section — `addendum_agent` parses a human-authored addendum document and produces a scoped implementation plan and tracking file, entirely contained within `15_Addendums/`; the main tracking board and milestone files are never touched
- **[v2.2]** `execution_plan.md` is the only task-status record — the Status column in every row is the canonical record of whether a task is Planned / In Progress / Done. There is no separate tracking board: `tracking_board.md` is removed; `08_Tracking_System/` holds only `decisions_log.md`, a lightweight decisions log with no status authority.
- **[v2.3]** `03_System_Design` replaces `03_Architecture_Design` — cross-cutting design stays at the folder root; per-module design lives in numbered `NNN_<name>_module/` folders (seven-document set, cloned from `_template/`). Module numbers are permanent, never reused or renumbered.

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
Every human-required step logged immediately. **[v1.7]** Use `12_Manual_Actions/actions.md` (not the legacy `manual_action.md` root file). Add a row before finishing the task prompt — never defer.

**[v1.1] 9. Minimum human intervention after 05_AI_Agent_System**
System runs on agent execution with human approval gates only.

**[v1.2] 10. Execution-ready gate**
`project_status.md` is the single source of truth for whether the project is ready to begin execution. No agent begins implementation work unless `project_status.md` shows `READY`.

**[v2.2] 22. execution_plan.md is the only task-status record — no separate tracking board**
The Status column in `execution_plan.md` is the canonical record of task progress. Agents update the Status column directly when a task moves from `Planned` → `In Progress` → `Done`. There is no `tracking_board.md`. `08_Tracking_System/decisions_log.md` holds only a lightweight decisions log — it has no status authority and is never the source agents read to determine what to execute next.

**[v2.3] 23. System design is per-module**
`03_System_Design/` (formerly `03_Architecture_Design/`) splits into cross-cutting root docs (`system_architecture.md`, `service_design.md`, `data_flow.md`, `ADR/`) and one `NNN_<name>_module/` folder per core module, cloned from `_template/`. See the `03_System_Design` section below for the full module convention.

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

**[v1.7] 17. Manual actions are tracked with per-environment status and milestone reference**
`12_Manual_Actions/actions.md` is the authoritative tracker for all human-required steps. Every row must include: Action ID, description, the milestone task it unblocks, priority (P1/P2/P3), and per-environment status (Dev · Staging · Prod). `12_Manual_Actions/guides.md` holds the step-by-step completion instructions for every action. Agents add rows to `actions.md` before completing any task prompt that generates a human step. Agents never defer this logging.

**[v1.6] 18. LLM Wiki as persistent context layer**
Every project following AOSDF has an `llm-wiki/` folder as its fourth directory.
Agents READ from the wiki for context before starting any task that involves design,
research, or architecture. Agents NEVER write to `llm-wiki/` — the wiki is updated
by the human via direct session commands. The wiki and the project documents are
separate systems that must never overlap in write access.

**[v1.9] 19. Legal requirements are binding architecture constraints**
When `13_Legal_Requirements/` exists in a project, all files in it are required reading
for `captain_agent` before generating or re-running the execution plan, and for any
design or architecture agent before finalizing service design, tenant onboarding flows,
or data handling decisions. Every legal constraint must map to at least one concrete
task in the execution plan — they are not passive context. A legal constraint overrides
an optional design decision whenever there is a conflict.

**[v2.0] 20. Design for portability — every infrastructure client behind an abstraction interface**
When `14_Future_Migrations/alternatives.md` exists in a project, it is required reading
for `captain_agent` and any architecture or backend agent before designing services or
writing infrastructure-touching code. Every infrastructure client (queue, cache, storage,
secrets, database) must be wrapped behind an abstraction interface. Provider SDK calls
are confined to adapter implementation files only — never in business logic. Swapping a
provider must require only a new adapter, never a business-logic change. This principle
applies from M0 — it is an architectural discipline, not a migration task.

**[v2.1] 21. Post-baseline changes are managed through Addendums — never through ad-hoc milestone edits**
After the execution plan is locked and work has begun, requirements that arrive
post-baseline are handled through `15_Addendums/`. Each addendum is a human-authored
document describing the change; `addendum_agent` converts it into a scoped implementation
plan and tracking file, both contained within `15_Addendums/`. The main tracking board,
execution plan, and milestone files are read-only for the addendum workflow — they are
only modified by `captain_agent` on explicit scope-change re-runs. Addendum tasks are
tracked in `15_Addendums/tracking_addendums.md`, not in the main tracking board.

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
│   ├── setup_aosdf.md                          ← New project setup guide + upgrade guide
│   ├── workflow_initiator.md
│   ├── templates.md
│   ├── agents/                                 ← All agent definitions (general templates)
│   │   ├── identify_missing_documents.md
│   │   ├── captain_agent.md
│   │   ├── research_and_refine_agent.md
│   │   ├── research_and_review_agent.md
│   │   ├── architect_agent.md
│   │   ├── backend_agent.md
│   │   ├── infra_agent.md
│   │   ├── qa_agent.md
│   │   ├── frontend_agent.md
│   │   ├── commander_agent.md
│   │   ├── execution_agent.md
│   │   ├── reviewer_agent.md
│   │   ├── validator_agent.md
│   │   └── addendum_agent.md
│   ├── reference/                              ← Quick-reference docs for Claude + humans
│   │   ├── agent_index.md
│   │   ├── folder_map.md
│   │   ├── formatting_standard.md
│   │   └── rules.md
│   └── designing_aosfd/
│
├── {project_name}/                             ← Application Code only
│   ├── nest-microservice/                      (backend — NestJS / Fastify / etc.)
│   └── {ui_component}/                         (optional UI — e.g. react-email-editor, Phase 2+)
│
├── {project_name}-Documents/                   ← Project Documentation (gitignored)
    ├── CLAUDE.md                               ← AI agent context file (entry point)
    ├── project_status.md                       [v1.2] execution readiness gate
    ├── identified_gaps.md                      [v1.1]
    ├── research_results.md                     [v1.4] output from research_and_refine_agent
    ├── reference/                              [v2.2] ← Raw product knowledge inputs (read by agents, never modified)
    │   ├── README.md                           ← What goes here and how agents use it
    │   └── [human-provided raw docs]           ← briefs, research, vendor docs, stakeholder notes
    └── documents/
        ├── 00_Project_Context/
        ├── 01_Project_Definition/
        ├── 02_Security_Framework/
        ├── 03_System_Design/
        │   ├── README.md                       ← module index
        │   ├── _template/                      ← cloned for every new module
        │   ├── system_architecture.md
        │   ├── service_design.md
        │   ├── data_flow.md
        │   ├── ADR/                            ← cross-cutting ADRs
        │   └── NNN_<name>_module/              ← one per core module
        │       ├── 00_overview.md … 06_operations.md
        │       └── decisions/                  ← module-scoped ADRs
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
        ├── 11_Future_Extensibility/
        ├── 12_Manual_Actions/                  [v1.7] ← two-file manual action system
        │   ├── actions.md                      ← tracker: all human steps, per-env status, milestone ref
        │   └── guides.md                       ← step-by-step instructions per action ID
        ├── 13_Legal_Requirements/              [v1.9] ← OPTIONAL: legal obligations, regulatory liability, compliance constraints
        │   └── concern_<n>.md                  ← one file per legal topic; required reading for captain_agent when directory exists
        ├── 14_Future_Migrations/               [v2.0] ← RECOMMENDED: infra alternatives, OSS exit paths, portability design guide
        │   ├── research.md                     ← raw research source (optional; human-authored)
        │   └── alternatives.md                 ← authoritative alternatives + portability guide; required reading for captain_agent + architecture agents
        └── 15_Addendums/                       [v2.1] ← OPTIONAL: post-baseline change management; one doc per addendum
            ├── <slug>.md                       ← human-authored addendum document (requirement, scope, constraints)
            ├── <slug>_plan.md                  ← generated by addendum_agent: scoped implementation plan
            └── tracking_addendums.md           ← generated by addendum_agent: append-only tracking board for all addendums
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
**Files:** `README.md` (module index), `system_architecture.md`, `service_design.md`, `data_flow.md`, `ADR/`, `_template/`, and one `NNN_<name>_module/` folder per core module.

Split into two tiers:

- **Cross-cutting design** at the folder root — `system_architecture.md`, `service_design.md`, `data_flow.md`, `ADR/`. Design that spans modules.
- **Per-module design** in `NNN_<name>_module/` folders — the design of one core module.

**Module convention.** Every module folder carries the same seven-document set, cloned from `_template/`:

```
NNN_<name>_module/
├── README.md              Module index — ID, status, dependencies, prior art
├── 00_overview.md         Purpose, scope, boundaries, dependencies
├── 01_requirements.md     Functional + non-functional requirements
├── 02_domain_model.md     Entities, invariants, state machine
├── 03_architecture.md     Components, flows, design decisions
├── 04_data_model.md       Schema, RLS/authorization, migrations
├── 05_interfaces.md       API, events, contracts, external integrations
├── 06_operations.md       Failure modes, observability, scaling
└── decisions/             Module-scoped ADRs
```

**Numbering is permanent.** `NNN` is a stable identifier — never reused, never renumbered. Cross-references throughout the workspace depend on it. A new module is appended at the next free number regardless of where it sits conceptually.

**Standing process — every time a module is developed:**

1. `architect_agent` claims the next free number from `03_System_Design/README.md`.
2. Clones `_template/` to `NNN_<name>_module/` and substitutes the `{{ID}}`, `{{SLUG}}`, `{{TITLE}}`, `{{MILESTONE}}` placeholders.
3. Registers the module in the `README.md` index.
4. Authors the document set; `Status: Not Started` holds until `00_overview.md` is real.
5. `identify_missing_documents` flags any module folder missing a file from the set.

A module's design must exist before its implementation milestone opens. No module ships without `00_overview.md`, `02_domain_model.md`, and `03_architecture.md` complete.

### 04_Infrastructure_Design
**Files:** `infra_architecture.md`, `scaling_strategy.md`, `cost_estimation.md`, `observability.md`

### 05_AI_Agent_System
**Files:**
```
agents/
  workflow_initiator.md            [v1.1]  ← project setup, structure validation
  identify_missing_documents.md   [v1.1]  ← scans project against checklist
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
  addendum_agent.md     [v2.1]  ← post-baseline change: parses addendum doc → plan + tracking in 15_Addendums/

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

### 08_Tracking_System — `decisions_log.md`
**[v2.2] No separate tracking board.** `execution_plan.md`'s Status column is the only task-status record — there is no `tracking_board.md`. `08_Tracking_System/` holds only `decisions_log.md`, a lightweight log of cross-cutting decisions made during execution; it has no status authority and agents never read it to find work. Created by `captain_agent` if absent. Commander reads `execution_plan.md` to find the next `Planned` task.

### [v2.0] 14_Future_Migrations — Portability Reference Section

**Status:** Recommended. Every project should have this section to prevent infrastructure lock-in and enable future migrations.

**Files:**
- `research.md` — optional; raw research source (cloud comparisons, OSS alternatives, migration timelines); human-authored; never modified by agents
- `alternatives.md` — **the authoritative document**; structured alternatives by layer, phased migration plan, portability-first principle, and agent design guidelines

**Purpose:** Documents all viable infrastructure alternatives to the current stack (cloud provider alternatives + OSS self-hosted alternatives), defines the phased migration timeline by blast radius, and establishes the mandatory portability-first design principle for all infrastructure-touching code. Distinct from `04_Infrastructure_Design/`, which describes the current chosen infrastructure — this section describes what the system can migrate to and how.

**Agent rule — when this directory exists:**
- `captain_agent` MUST read `14_Future_Migrations/alternatives.md` before generating or re-running the execution plan
- Any architecture or backend agent MUST read `alternatives.md` before designing services or writing infrastructure-touching code
- All infrastructure clients (queue, cache, storage, secrets, database) MUST be wrapped behind abstraction interfaces — this is a design requirement, not a migration task
- When reviewing implementation prompts: verify no provider SDK is imported directly in business logic; if found, require adapter refactor before proceeding
- After ingesting or updating `alternatives.md`, the human MUST run `Wiki: re-ingest <file>` or `Wiki: ingest <file>` to keep the wiki in sync

---

### [v1.9] 13_Legal_Requirements — Optional Section

**Status:** Optional. Not every project requires a dedicated legal section. When this directory exists, it has binding weight on all architecture and planning decisions.

**Files:** `concern_<n>.md` — one file per legal topic, risk, regulatory requirement, or liability constraint. Files may be named descriptively (e.g., `concern_1.md`, `dlt-pe-liability.md`).

**Purpose:** Documents legal obligations that affect system design: regulatory liability for operating as a platform (e.g., TRAI DLT PE registration), industry-specific compliance, contractual constraints from providers or partners, and legal risks from multi-tenant models. Distinct from `02_Security_Framework`, which covers technical security controls.

**Agent rule — when this directory exists:**
- `captain_agent` MUST read all files in `13_Legal_Requirements/` before generating or re-running the execution plan
- Any design or architecture agent MUST read this section before finalizing service design, tenant onboarding flows, or data handling decisions
- Every legal constraint must map to at least one concrete task in the execution plan — these are not passive notes
- Legal requirements take precedence over optional design decisions when there is a conflict
- After ingesting new concern files, the human MUST run `Wiki: ingest <file>` for each new file

---

### [v2.1] 15_Addendums — Post-Baseline Change Management

**Status:** Optional. Created when post-baseline requirements arrive that are too
cross-cutting for a single tracking board row but not large enough to warrant a full
`captain_agent` re-run.

**Files:**
- `<slug>.md` — **human-authored** addendum document; describes the change, affected
  components, constraints, and deadline. One file per addendum.
- `<slug>_plan.md` — **agent-generated** by `addendum_agent`; scoped flat task table with
  `ADD-<slug>-T<seq>` task IDs, owner, validation criterion, and addendum section citation.
- `tracking_addendums.md` — **agent-generated** tracking board; one `---`-separated section
  per addendum; rows mirror the plan file; execution_agent or human updates Status as work
  progresses.

**Purpose:** Handles late-cycle cross-cutting requirements (security policy updates,
provider changes, regulatory notices, platform compatibility fixes) with full traceability
without disrupting the in-progress milestone workflow.

**Agent rule — when this directory exists:**
- `addendum_agent` is the only agent that creates files in `15_Addendums/`
- `addendum_agent` MUST NOT touch `execution_plan.md` or any
  milestone file — those are captain_agent territory
- `tracking_addendums.md` is append-only — earlier addendum blocks are never modified
- When an addendum is complete (all tasks Done, all exit criteria checked), set the
  addendum block's Status to `COMPLETE` and add a `Closed: <date>` line
- After `addendum_agent` runs, the human should run `Wiki: ingest <slug>_plan.md` if the
  addendum affects architecture or infrastructure decisions already documented in the wiki

---

### [v1.7] 12_Manual_Actions — Two-File Manual Action System

**`actions.md`** — The tracker. One row per manual action. Columns: Action ID · Description · Milestone Task · Blocks · Category · Priority · Dev Status · Staging Status · Prod Status · Owner.

**`guides.md`** — The instructions. One section per Action ID with step-by-step completion steps, CLI commands, and validation criterion. Written when the action is first identified; expanded when more detail is known.

**Agent rules:**
- Any agent that identifies a human-required step MUST add a row to `actions.md` before finishing the task prompt
- The row must include at minimum: Action ID (next sequential MA-xxx), Description, Milestone Task, Blocks, Category, Priority
- Env status columns default to `Pending` (or `N/A` for environments where the action doesn't apply)
- When a guide exists or can be written, add it to `guides.md` in the same session
- When a human completes an action: move the row to the **Completed** table in `actions.md` and add the date; update env status columns accordingly
- `manual_action.md` at the project root is the legacy file — `12_Manual_Actions/actions.md` is authoritative for v1.7+ projects

---

### [v1.8] Session Context Management Rules

These rules apply to every agent, every session. Violations cause mid-task failures and higher token costs.

**Commander Agent MUST:**
- Before delegating any task, assess whether sufficient context window remains to complete it, including validation and tracking board update
- If context is not sufficient: stop, do not delegate. Output: "Insufficient context remaining to start [task] safely. Please compact the session and re-invoke the Commander." Nothing else.
- Never chain multiple tasks in one un-compacted session

**All agents MUST:**
- Read only the files explicitly required for the current task — not the full document set
- Never read files speculatively ("in case I need it later")
- Complete each task fully (including validation + tracking board update) before context is exhausted — if this is not possible, halt and report rather than producing partial output

**Compact cadence (enforced by human + agent):**
```
compact → invoke Commander → task runs to completion → compact → repeat
```
- Compact before starting each new task, not after it fails
- Target: never exceed 60% context usage before task start
- A task left half-done is worse than a task not started — partial state is the hardest failure mode to recover from

### [v1.2] project_status.md — Execution Gate

This file tracks the project's overall readiness. Located at `{project_name}-Documents/project_status.md`.

States: `SETUP` → `PLANNING` → `READY` → `IN_PROGRESS` → `BLOCKED` → `COMPLETE`

No execution agent may begin implementation until status = `READY`.

---

## [v1.2] Agent Architecture

### [v1.3] captain_agent — Planning & Execution Architect

- **Role:** Reads all completed 00–05 documents and generates the execution plan and milestones. This is the bridge from "documentation complete" to "ready to build." Must be run before `commander_agent` ever starts.
- **Inputs:** FRD, PRD, security_requirements.md, system_architecture.md, service_design.md, data_flow.md, infra_architecture.md
- **Outputs:** `06_Execution_Plan/execution_plan.md`, `07_Milestones/M*/milestone.md`, `08_Tracking_System/decisions_log.md` (created if absent — decisions log only, not a task board), updated `project_status.md`
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

### [v2.1] addendum_agent — Post-Baseline Change Planning

- **Role:** Receives a human-authored addendum document from `15_Addendums/<slug>.md`.
  Parses the requirement, cross-checks existing `execution_plan.md` Status column for overlap,
  generates a scoped flat implementation plan (`<slug>_plan.md`), and appends an entry to
  `tracking_addendums.md`. All output is confined to `15_Addendums/`. Does not modify the
  main execution plan or milestone files.
- **Inputs:** `15_Addendums/<slug>.md` (addendum doc), `CLAUDE.md`, `project_status.md`,
  `execution_plan.md` (read-only, Status column), `llm-wiki/` (read-only)
- **Outputs:** `15_Addendums/<slug>_plan.md` (implementation plan),
  `15_Addendums/tracking_addendums.md` (tracking entry appended)
- **Task IDs:** `ADD-<slug>-T<seq>` — scoped to the addendum, never conflict with M-series IDs
- **Never:** touches `execution_plan.md` or any milestone file
- **Called by:** Human only. After `15_Addendums/<slug>.md` is saved and reviewed.

---

### [v1.3] reviewer_agent (Strategy B)

- **Role:** Receives the implementation prompt generated by architect_agent. Reviews for security vulnerabilities, architectural violations (especially state mutation rules), scalability concerns, and missing test coverage. Returns approval or redline.
- **Called by:** architect_agent (Strategy B only)
- **Calls:** implementor (on approval) or architect_agent (on redline)

### [v1.3] validator_agent (Strategy B)

- **Role:** Receives completed implementation from implementor. Runs tests (unit, integration, schema validation). If all pass: marks task `Done` in `execution_plan.md` and notifies commander. If fail: returns to implementor with failure details.
- **Called by:** implementor (Strategy B only)
- **Updates:** `execution_plan.md` Status column (the only agent in Strategy B that does so)

### New Agents in v1.2

#### commander_agent
- **Role:** The sole orchestrator of execution. Called once per session. Reads `project_status.md` and `execution_plan.md` (finds the first row with Status = `Planned`), then delegates to the right agent. There is no tracking board to consult.
- **Never implements.** Only directs.
- **Calls:** `execution_agent` (Strategy A) or `architect_agent` (Strategy B)
- **Called by:** Human, once per session

#### execution_agent (Strategy A)
- **Role:** Single-agent implementor. Receives task from commander, generates prompt, saves to `implementation_prompts/`, executes, validates, updates `execution_plan.md`.
- **Updates:** `execution_plan.md` Status column after every subtask — the only status record
- **Called by:** Commander Agent

#### For Strategy B — the validator_agent responsibility
The validator_agent (final step of the 4-agent pipeline) is the only one that updates `execution_plan.md` Status → `Done`. The commander reads `execution_plan.md` to find the next `Planned` task — there is no other file to check.

### Agents That Require Manual Invocation

These agents are NOT called by the commander. They are called by a human at specific points:

| Agent | When to Call Manually | Why |
|------|---------------------|-----|
| `workflow_initiator` | At project start, or when resuming after a gap | Needs human to answer setup questions |
| `research_and_review` | Before architecture is finalized | Human decides which reference systems to research |
| `research_and_refine` | Any time a research question needs a structured answer | Needs human-authored `task.md` + `project_root_path`; outputs to `research_results.md` only; never modifies existing docs |
| `identify_missing_documents` | Called by workflow_initiator, or manually before a milestone | Needs current project path |
| `captain_agent` | After 00–05 docs are complete; before commander starts | Needs human to confirm 00–05 are final and locked |
| `addendum_agent` | When a post-baseline cross-cutting requirement arrives | Needs human-authored `15_Addendums/<slug>.md`; outputs plan + tracking entirely within `15_Addendums/` |

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
  → captain_agent writes execution_plan.md  (Status column = source of truth)
  → captain_agent writes 07_Milestones/M*/milestone.md
  → captain_agent validates FRD coverage
  → captain_agent writes 08_Tracking_System/decisions_log.md if absent  (decisions log only)
  → captain_agent sets project_status.md = READY (or PLANNING if gaps remain)

[Now commander_agent can begin]
```

### Strategy A: Single-Agent Execution

```
Human calls Commander Agent
  → Commander reads project_status.md + execution_plan.md
  → Commander finds next row in execution_plan.md where Status = Planned
  → Commander calls Execution Agent with task context
  → Execution Agent generates prompt → saves to implementation_prompts/
  → Human approves prompt (one gate)
  → Execution Agent implements → validates
  → Execution Agent updates execution_plan.md Status: Done  ← the only status record
  → Execution Agent reports back to Commander
  → Commander finds next task
```

### Strategy B: Multi-Agent Pipeline

```
Human calls Commander Agent
  → Commander reads project_status.md + execution_plan.md
  → Commander finds next row in execution_plan.md where Status = Planned
  → Commander calls Architect Agent

Architect → generates implementation prompt → saves to implementation_prompts/
Reviewer Agent → reviews prompt for security + scale violations
  → if approved: passes to Implementor
  → if rejected: returns to Architect with redline comments
Implementor → executes approved prompt
Validator Agent → runs tests → if pass:
    → updates execution_plan.md Status: Done  ← the only status record
    → notifies Commander
  → if fail: returns to Implementor with failure details
```

**[v1.2] Notification hook (optional):** For steps requiring human approval (e.g., production deploy), agents post to a Slack/Discord webhook and poll for a reaction before proceeding.

---

## [v1.1] Agent Permission Model

| Level        | Scope                           | Example Actions                        |
| ------------ | ------------------------------- | -------------------------------------- |
| READ         | Read files, SELECT              | Research, gap analysis, plan review    |
| WRITE_LOCAL  | Create/edit project files       | Code, migrations, config               |
| WRITE_INFRA  | Provision/modify cloud resources | Terraform apply, ECS deploy           |
| WRITE_DATA   | Mutate production data          | Migration, seed                        |
| WRITE_REMOTE | Push to remote git repositories | git push (any branch)                  |
| ADMIN        | Cross-cutting permissions       | Secrets, IAM, DNS                      |

Each agent declares a `## Permissions` section. WRITE_INFRA requires explicit human approval before `apply`. **WRITE_REMOTE is never granted to any agent** — `git push` is a human-only action.

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
- `captain_agent` → `execution_plan.md`, `milestone.md` files, `08_Tracking_System/decisions_log.md`
- `execution_agent` / `validator_agent` → `execution_plan.md` Status updates (the only status record)
- `research_and_refine_agent` → `research_results.md`
- Any agent writing `identified_gaps.md`, `12_Manual_Actions/actions.md`, or ADR files

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
| captain_agent re-run                     | execution_plan.md, decisions_log.md (if absent), project_status.md, identified_gaps.md | `Wiki: full-sync`              |
| New ADR created                          | ADR file + system_architecture.md                                       | `Wiki: re-ingest <adr-file>`                   |
| research_and_refine_agent run            | research_results.md                                                     | `Wiki: re-ingest research_results.md`          |
| Milestone completed                      | execution_plan.md, project_status.md                                    | `Wiki: re-ingest <each file>`                  |
| New gap logged                           | identified_gaps.md                                                      | `Wiki: re-ingest identified_gaps.md`           |
| Manual action completed                  | manual_action.md                                                        | `Wiki: re-ingest manual_action.md`             |
| block-schema or template-schema updated  | Those files + renderer-contracts.md                                     | `Wiki: re-ingest <each file>`                  |
| New legal requirement file added         | `13_Legal_Requirements/concern_<n>.md`                                  | `Wiki: ingest <concern-file>`                  |
| alternatives.md created or updated      | `14_Future_Migrations/alternatives.md`                                  | `Wiki: re-ingest <alternatives-file>`          |
| addendum_agent run                       | `15_Addendums/<slug>_plan.md`, `tracking_addendums.md`                  | `Wiki: ingest <slug>_plan.md` (if arch/infra relevant) |

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

**[v1.1]** Gaps logged to `identified_gaps.md` immediately. **[v1.7]** Manual steps logged to `12_Manual_Actions/actions.md` immediately (not the legacy `manual_action.md`).

**[v1.2]** `project_status.md` = READY before execution. Implementation prompts saved before running. M0 complete before M1.

**[v1.4]** All agent-generated files with tables must follow the Document Formatting Standard. Separator dashes match column width. Data cells padded. Consistent widths across files.

**[v1.8]** `git push` is a human-only action. Agents NEVER push to remote branches — not feature, not staging, not main. An agent may `git add`, `git commit`, and show the diff, but must stop there and wait for explicit human instruction to push.
