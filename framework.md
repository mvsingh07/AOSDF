# AI-Orchestrated Software Development Framework (AOSDF)
# Version 3.2

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
> Changes in v2.2 are marked `[v2.2]`
> Changes in v2.3 are marked `[v2.3]`
> Changes in v2.4 are marked `[v2.4]`
> Changes in v2.5 are marked `[v2.5]`
> Changes in v3.0 are marked `[v3.0]`
> Changes in v3.1 are marked `[v3.1]`

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
- **[v2.4]** Introduces optional Jira board integration — a project may opt in, at setup time only, to having its `execution_plan.md` / milestone / gap / manual-action state mirrored onto a Jira board via MCP. Off by default. When on, sync is **human-triggered only** (`Jira: sync`, mirroring the existing `Wiki:` command pattern) — no agent calls Jira automatically. See the **Jira Board Integration** section below and `AOSDF/reference/jira_mapping.md`.
- **[v2.5]** Introduces the Concept Frontmatter Standard — a small YAML metadata block, required on every ADR, module `02_domain_model.md`/`03_architecture.md`, `02_Security_Framework/threat_model.md`, `04_Infrastructure_Design/*.md`, and `13_Legal_Requirements/concern_*.md` (when present). The agent (or human) writing the document fills it in as part of writing it — no separately-scheduled "write learning content" task. This is the raw material a later, independently-tracked capability (`16_Learning_Roadmap/`) derives a personal, zero-setup interview-prep roadmap from — see the **Concept Frontmatter Standard** section below and Principles 28-30. Also formalizes the `aosdf-diagram` fenced-block convention already used by this file's own diagrams.
- **[v2.5]** Generalizes Jira-only sync to a provider-agnostic `tracker_sync_agent` — Jira *or* Notion, one provider per project, selected via `tracker_config.md`'s `Provider:` field and implemented against a shared `TrackerAdapter` interface. `jira_config.md` / `jira_sync_agent` keep working unchanged for existing projects. See the **Tracker Board Integration** section below, `AOSDF/reference/tracker_mapping.md`, and Principles 25-26.
- **[v2.5]** Introduces `concept_indexer_agent` and `16_Learning_Roadmap/` — read-only over the documentation tree, write-only to `16_Learning_Roadmap/`, deriving `roadmap_index.md`, `roadmap_graph.json`, and a self-contained `render/index.html` from every `concepts:` entry in Concept Frontmatter, never duplicating source content (Principle 28). Human-triggered only, via `Learn: rebuild` / `Learn: open` / `Learn: check coverage`. See the **Learning Roadmap** section below.
- **[v2.5 D0]** Introduces `AOSDF/renderer_core/` for Track L (`render/index.html`'s diagram panel + shared tokens). **[v2.5, restructured 2026-08-19]** Track P (Project Docs Site) renders with MkDocs + Material instead of a hand-rolled renderer — a single `mkdocs.yml` per project, a tiny CSS override for `aosdf-diagram`, and `docs_site_agent` as the thin human-triggered build/open wrapper. Track D (a matching site for `AOSDF/` itself) was built the same way, then cancelled — `AOSDF/` is the product, not project documentation. See **Track L Renderer Core** and **MkDocs-Based Project Docs Site** below.
- **[v3.0, E6]** GA hardening: `aosdf-lint` formatting linter (Rules 1-2, reusing the write tools' own table renderer as the compliance definition), multi-workspace support in the editor extension, and internal-only packaging (`OD-1`). See **GA Hardening** below.
- **[v3.1]** Codifies Principle 31 — denormalized status displays (`milestone.md` vs `execution_plan.md`) and MA-xxx cross-references must be reconciled whenever an agent reads a milestone.md, not left to silently drift; adds the **Reusable Architecture Patterns (Reference)** section, starting with Tenant Reputation Gating for shared outbound dispatch infrastructure.
- **[v3.2]** Introduces `principal_architect_agent` — a human-invoked, on-demand agent that re-reviews an existing architecture or plan against current external best practice (official docs, established engineering references, recent community discussion) at a milestone or task boundary the human chooses, producing trackable redline findings rather than silent rewrites. Gives `superman_agent` a `mode` input (`discipline` forces the full Strategy B review pipeline for every task; `normal` is its pre-existing behavior). Introduces the Scope Expansion Protocol (`06_Execution_Plan/scope_expansion_log.md`) for work discovered mid-task that is genuinely outside the current plan. Formalizes auto-compaction triggers against context-window percentage, and adds advisory-only model-tier suggestions and a context-caching read-ordering discipline. See Principles 32-37 below.

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

**[v2.4] 24. Jira board sync is optional, decided once at setup, and always human-triggered**
A project may opt in to Jira board sync only during `workflow_initiator` setup (Step 1, Q8) — never mid-project without a human explicitly re-running that decision. When opted in, the human also fixes a sync cadence recommendation (see `jira_mapping.md`), but no agent is ever permitted to call the Jira MCP tools on its own initiative — sync only happens when a human issues the `Jira: sync` command, exactly as wiki updates only happen via `Wiki:` commands. `execution_plan.md`'s Status column remains the sole source of truth at all times; Jira is a mirror of it, never the reverse, except through the explicit Import Mode described in `jira_sync_agent.md`.

**[v2.5] 25. Tracker sync is provider-agnostic and swappable**
`tracker_sync_agent` (generalizing `jira_sync_agent` — see **Tracker Board Integration** below) never imports a provider SDK outside its adapter implementation. Adding a third provider in the future requires only a new adapter file, never a change to `execution_plan.md`'s schema or to any other agent. A project configures exactly one tracker provider at a time — dual-sync is out of scope, since two live mirrors could independently drift, the exact failure mode Principle 22 exists to prevent.

**[v2.5] 26. Tooling is a client of the files, never a second source of truth**
The editor extension (VSCode first — see `aosdf_expansion_scope.md` §4.1, IDE-agnostic by design), `aosdf-mcp`, and any Claude Code hook (when built) read and write the existing markdown files in `{project_name}-Documents/`. None of them may introduce a parallel database, cache, or state store that could diverge from `execution_plan.md`'s Status column (Principle 22) or `project_status.md`. If a view needs to be fast, it may cache for rendering, but a cache is invalidated by file changes, never treated as authoritative. This is the same discipline Principle 30 later extends to the learning renderer.

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

**[v2.5] 28. Learning content is derived, never duplicated**
`16_Learning_Roadmap/` (when a project builds it) contains no original prose. Every fact in it traces to Concept Frontmatter on a document that exists for its own, non-learning reason. If regenerating it would produce different content than the last run, the source documents are authoritative — the roadmap is stale, never wrong, and re-running its rebuild command fixes it. No agent or human ever writes directly into `16_Learning_Roadmap/`.

**[v2.5] 29. Concept capture happens at the moment of decision, by the agent (or human) making it**
`architect_agent`, and any human authoring `02_Security_Framework/threat_model.md`, `04_Infrastructure_Design/*.md`, or `13_Legal_Requirements/concern_*.md`, add Concept Frontmatter (see the **Concept Frontmatter Standard** section below) as part of the document they were already producing. No one schedules a separate "write learning content" task. A required document missing the frontmatter is logged as a Low-severity Learning gap — never a blocker to execution.

**[v2.5] 30. The learning renderer is a read-only, zero-dependency artifact**
`16_Learning_Roadmap/render/index.html` has no build step, no external network calls, no accounts, and no server requirement — it reads only from data inlined at generation time, the same "tooling is a client of the files, never a second source of truth" discipline this framework already applies to the Wiki (Principle 18) and Jira sync (Principle 24). `{project_name}-Documents/{project_name}-Documents-site/` (MkDocs-based, see **MkDocs-Based Project Docs Site** below) is read-only, self-contained static HTML once built — a real build step exists there (`mkdocs build`), but the *output* is still an artifact anyone can open with no server, no accounts, and no runtime dependency, and stays local-only by default the same way (never publishes by default — see **Learning Roadmap** and `evolution.md` Sec 14).

**[v3.1] 31. Denormalized status displays and cross-references must be reconciled on read, never left to drift**
`07_Milestones/*/milestone.md`'s own Status column is a human-readable display copy of `execution_plan.md`'s Status column (Principle 22) — it is not a second source of truth, but nothing keeps it automatically in sync either. Similarly, `12_Manual_Actions/actions.md` Action IDs (MA-xxx) can be reassigned or repurposed as the tracker evolves; any citation of a specific MA-xxx ID in a milestone.md, execution_plan.md, or implementation prompt is a point-in-time reference, not a permanent binding. **Discovered concretely in a live project:** a milestone.md showed every subtask as `Planned` while `execution_plan.md` showed nearly all of them `Done`, and the same file cited `MA-024`/`MA-025` for a task whose actions had since been renumbered to `MA-021`/`MA-022` after `actions.md` reassigned the ID `MA-024` to unrelated work. **Rule:** whenever any agent reads a milestone.md file for any reason, it MUST cross-check its Status column against `execution_plan.md` and its MA-xxx citations against `actions.md`'s current numbering, and correct any mismatch found in the same session — logged as a Documentation gap in `identified_gaps.md` if the fix is non-trivial. This is a targeted reconciliation triggered by the read, never a standing background sync job.

**[v3.2] 32. Principal Architect review is human-invoked, periodic, and produces trackable redlines — never silent rewrites**
`principal_architect_agent` re-reviews an existing architecture or plan against current external practice (official docs, established engineering references, recent community discussion) only when a human explicitly invokes it for a milestone or task boundary they choose — never automatically, and never as a substitute for `architect_agent`'s day-to-day design ownership or `reviewer_agent`'s implementation-prompt gate. Findings go into a dated review document under the affected module's directory, separated into must-fix-before-proceeding / worth-tracking / no-change-needed, and any proposed change is written as a redline against the existing design docs — never an in-place rewrite. See **principal_architect_agent** under Agent Architecture below.

**[v3.2] 33. Superman's Discipline Mode forces the reviewed pipeline; Normal Mode is unchanged**
`superman_agent` accepts a `mode` of `discipline` or `normal` (default `normal`). Normal mode is Superman's pre-existing behavior — Strategy A or B, as read from `execution_plan.md` or an explicit `strategy_override`. Discipline mode forces the full Strategy B pipeline (architect → reviewer → implementor → validator) for every task in the run, regardless of what the execution plan's strategy line says — no implementation prompt reaches execution without `reviewer_agent` approval first. Both modes keep Superman's defining trait: no per-task human approval gate. See **Superman Modes** under Execution Strategies below.

**[v3.2] 34. Out-of-scope work discovered mid-task is logged and stops the loop — never silently absorbed or silently dropped**
When implementing a task reveals a genuine need for work outside the current milestone/execution-plan scope, the agent logs it to `06_Execution_Plan/scope_expansion_log.md` (discovering task, proposed task, why it's required, suggested milestone) and stops — the same shape as a Manual Action Required stop. A human resolves it by re-running `captain_agent` to fold the proposed task into the plan, or by recording an explicit deferral in the log. No agent adds an unplanned task to `execution_plan.md` on its own initiative. See **Scope Expansion Protocol** below.

**[v3.2] 35. Every agent loads only what the current task needs — never a whole reference directory speculatively**
Each agent's Token Efficiency Rules section already names the specific files it reads per task; this principle makes explicit and binding what those sections individually imply: reading an entire folder (`llm-wiki/`, `03_System_Design/`, `reference/`) "just in case" is a violation, not a convenience. If a task's scope is ambiguous enough that an agent cannot tell which file it needs, that ambiguity itself is reported as a blocker (per each agent's existing stopping conditions) rather than resolved by reading broadly.

**[v3.2] 36. Auto-compaction is triggered by context-window percentage, not just task count**
Every agent with a Compact Protocol section treats visible context usage at roughly **70% of the active model's context window as COMPACT RECOMMENDED and roughly 85% as COMPACT REQUIRED**. Where exact usage isn't visible to the agent, the pre-existing qualitative heuristics (task count completed this session, size of outputs already generated) remain the fallback signal — they are secondary, not the primary trigger, wherever a percentage estimate is available.

**[v3.2] 37. Model-tier and context-cache discipline are advisory, not runtime automation**
AOSDF agents are instructions consumed by whatever LLM/harness executes them — they cannot themselves switch models or control an API-level prompt cache. Two advisory disciplines apply instead: (a) the session-orchestrating agents (`commander_agent`, `superman_agent`) print a `Suggested model tier` line inferred from the task's shape (mechanical/single-file/Strategy A → fast/low-cost tier; architecture/ADR/Strategy B/principal-review work → frontier tier) for a human or supervising harness to act on — no agent switches models itself; (b) every agent reads stable, rarely-changing documents (`CLAUDE.md`, `framework.md`, architecture docs) first, in the same order, without re-reading them verbatim mid-session, so the underlying LLM API's prompt cache is actually reused — task-specific/volatile reads (execution-plan rows, FRD sections) come after that stable prefix, never interleaved before it.

---

## Reusable Architecture Patterns (Reference)

Patterns below are not framework principles (they are not mandatory for every project) — they are documented,
named precedents any `architect_agent` or human should consider and either apply or explicitly decline (with a
one-line reason) when a project matches the "Applies to" criterion. Declining without a stated reason is a
Documentation gap.

### Tenant Reputation Gating (Shared Outbound Dispatch Infrastructure)

**Applies to:** any product where multiple tenants dispatch outbound communications (email, SMS, push,
webhooks) through infrastructure the platform itself operates and is accountable for — a shared IP pool, a
shared sending domain, a shared provider account. The risk this pattern addresses: one tenant's bad list or
bad behavior degrades or suspends sending reputation for every other tenant sharing that infrastructure.

**Pattern:**
- A **gatekeeper** sits in the dispatch path and can block or throttle a send before it reaches the provider,
  independent of the provider's own reputation logic.
- A **per-tenant reputation score**, maintained as an exponentially-weighted moving average (EMA) over the
  tenant's own complaint/bounce rate (a smoothing factor of α≈0.05 dampens single-incident noise while still
  reacting within a handful of sends) — not a raw rolling-window rate, which a short burst can distort.
- A **graduated enforcement ladder**, never a binary allow/block — e.g. `HEALTHY → WATCHLIST → THROTTLED →
  SUSPENDED → BANNED`, with each transition automatic on score thresholds.
- **Calibration check (a specific, recurring miscalibration to test for):** the platform's own account-level
  provider alarms (e.g. a cloud provider's bounce/complaint CloudWatch-equivalent alarms) must be set *tighter*
  than any individual tenant's per-tenant gatekeeper threshold. If the account-level alarm is looser than the
  per-tenant threshold, the gatekeeper can never actually protect the shared account — by the time the
  account-level alarm fires, the gatekeeper's per-tenant threshold has already been breached and it is too
  late to prevent the shared-account consequence.
- This is a **`02_Security_Framework`/`03_System_Design` concern from M0** for any product matching the
  "Applies to" criterion — do not defer it to a later phase as a placeholder "basic rules" implementation, and
  do not let a fully-built engine go undocumented: log a Documentation gap in `identified_gaps.md` immediately
  if the engine is built before its own architecture doc exists — this pattern is named from exactly that
  failure mode occurring in a live project.

**Origin:** Comms-Service's Send Gatekeeper Service + Tenant Reputation Engine. See
`Comms-Engine-Documents/identified_gaps.md` GAP-061–063 for the concrete miscalibration and documentation-gap
instances this pattern was extracted from.

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
│   │   ├── addendum_agent.md
│   │   ├── jira_sync_agent.md                  [v2.4] ← OPTIONAL, superseded by tracker_sync_agent.md
│   │   ├── tracker_sync_agent.md               [v2.5] ← OPTIONAL, human-invoked only; Jira or Notion
│   │   ├── concept_indexer_agent.md            [v2.5] ← OPTIONAL, human-invoked only; Learn: rebuild / check coverage
│   │   └── docs_site_agent.md                  [v2.5, restructured 2026-08-19] ← OPTIONAL, human-invoked only; Project Docs: build/open only
│   ├── reference/                              ← Quick-reference docs for Claude + humans
│   │   ├── agent_index.md
│   │   ├── folder_map.md
│   │   ├── formatting_standard.md
│   │   ├── rules.md
│   │   ├── jira_mapping.md                     [v2.4] ← OPTIONAL — read if tracker_config.md Provider: jira
│   │   ├── notion_mapping.md                   [v2.5] ← OPTIONAL — read if tracker_config.md Provider: notion
│   │   └── tracker_mapping.md                  [v2.5] ← OPTIONAL — TrackerAdapter interface + config schema
│   ├── renderer_core/                          [v2.5 D0] ← Track L only — see Track L Renderer Core
│   │   ├── core.js                             ← markdown→HTML, diagram panel, tables, nav, search
│   │   └── core.css                            ← shared design tokens + styles, light/dark aware
│   ├── aosdf-mcp/                              [v2.5 E2-T1] ← MCP server, six read/write tools (Principle 26);
│   │   │                                            bundled inside AOSDF/, not a standalone package (OD-3)
│   │   ├── package.json                        ← zero runtime dependencies, hand-rolled stdio JSON-RPC
│   │   └── src/                                ← config.js, markdown-table.js, tools/*.js — see its own README.md
│   ├── designing_aosfd/                        ← AOSDF/ has no mkdocs.yml or site of its own — Track D
│   │                                              (a docs site for the framework itself) was built, then
│   │                                              cancelled 2026-08-19; see MkDocs-Based Project Docs Site
│   ├── .claude/                                [v2.5 E3-T1] ← Master template, copied into {project_name}/
│   │   │                                            (the only git repo) at setup — see Claude Code Native
│   │   │                                            Integration section below and folder_map.md
│   │   ├── agents/                             ← 20 subagent defs, one per AOSDF agent role
│   │   ├── commands/                            ← /aosdf-init, -plan, -next, -addendum, -research, -sync, -import
│   │   ├── settings.json                        ← git-push deny rule + session-context-gate hook wiring
│   │   └── hooks/session-context-gate.js        [E3-T2] ← Principle 27 PreToolUse gate
│   └── .mcp.json                               [v2.5 E3-T1] ← registers aosdf-mcp as an MCP server; also
│                                                    copied to {project_name}/, paths pre-adjusted for there
│
├── {project_name}/                             ← Application Code only
│   ├── nest-microservice/                      (backend — NestJS / Fastify / etc.)
│   └── {ui_component}/                         (optional UI — e.g. react-email-editor, Phase 2+)
│
├── {project_name}-Documents/                   ← Project Documentation (gitignored) — the ONE project docs folder;
│   ├── mkdocs.yml                              [v2.5, restructured 2026-08-19] ← Project Docs Site config, docs_dir: docs
│   ├── .venv/                                  [v2.5] ← mkdocs + mkdocs-material, project-local, gitignored
│   ├── {project_name}-Documents-site/          [v2.5, restructured 2026-08-19] ← mkdocs build output, gitignored,
│   │                                                sibling of docs/ (nested inside this folder, not a workspace-root
│   │                                                sibling), local-only by default
    └── docs/                                   [v2.5, restructured 2026-08-19] ← docs_dir; every renderable file lives here
        ├── CLAUDE.md                           ← AI agent context file (entry point)
        ├── project_status.md                   [v1.2] execution readiness gate
        ├── identified_gaps.md                  [v1.1]
        ├── research_results.md                 [v1.4] output from research_and_refine_agent
        ├── jira_config.md                      [v2.4] ← OPTIONAL, pre-v2.5 projects only (kept working)
        ├── tracker_config.md                   [v2.5] ← OPTIONAL, created only if tracker sync opted in at setup
        ├── tracker_config.env                  [v2.5] ← OPTIONAL, gitignored, credential-only (OD-2, resolved 2026-08-27)
        ├── docs_overrides/                     [v2.5, populated 2026-09-12] ← aosdf.css (aosdf-diagram panel) + aosdf.js (collapsible nav/TOC, home link) — copied from AOSDF/templates/project_docs_site/ at PJ1-T1
        ├── reference/                          [v2.2] ← Raw product knowledge inputs (read by agents, never modified)
        │   ├── README.md                       ← What goes here and how agents use it
        │   └── [human-provided raw docs]       ← briefs, research, vendor docs, stakeholder notes
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
            │   ├── execution_plan.md               [v2.2] ← Status source of truth — Status column is canonical
            │   ├── jira_issue_map.md               [v2.4] ← OPTIONAL, pre-v2.5 projects only — Task ID ↔
            │   │                                        Jira Key ↔ Last Synced; written only by jira_sync_agent
            │   └── tracker_issue_map.md            [v2.5] ← OPTIONAL — Task ID ↔ tracker item ↔ Last Synced;
            │                                            written only by tracker_sync_agent, never edited by hand
            ├── 07_Milestones/                      ← one folder per milestone, each a stage/checkpoint grouping
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
            ├── 15_Addendums/                       [v2.1] ← OPTIONAL: post-baseline change management; one doc per addendum
            │   ├── <slug>.md                       ← human-authored addendum document (requirement, scope, constraints)
            │   ├── <slug>_plan.md                  ← generated by addendum_agent: scoped implementation plan
            │   └── tracking_addendums.md           ← generated by addendum_agent: append-only tracking board for all addendums
            └── 16_Learning_Roadmap/                [v2.5] ← OPTIONAL, created only if explicitly requested: derived-only,
                                                          no original content (Principle 28)
                ├── roadmap_index.md                ← generated by concept_indexer_agent on Learn: rebuild — human-readable table
                ├── roadmap_graph.json               [v2.5 L2] ← generated by concept_indexer_agent — machine-readable node/edge graph
                └── render/index.html                [v2.5 L2/L3] ← generated by concept_indexer_agent — self-contained Build Order + Learn Order viewer, localStorage review tracking
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
**[v2.5]** `threat_model.md` requires Concept Frontmatter — see **Concept Frontmatter Standard**.

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

**[v2.5]** Every ADR and every module's `02_domain_model.md`/`03_architecture.md` requires Concept Frontmatter — see **Concept Frontmatter Standard**.

### 04_Infrastructure_Design
**Files:** `infra_architecture.md`, `scaling_strategy.md`, `cost_estimation.md`, `observability.md`
**[v2.5]** All four files require Concept Frontmatter — see **Concept Frontmatter Standard**.

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

**[v3.1]** Every `milestone.md`'s Status column is a denormalized display copy of `execution_plan.md` (Principle
22) — it can drift and is not auto-synced. Any agent reading a milestone.md must reconcile it against
`execution_plan.md` and against `12_Manual_Actions/actions.md`'s current MA-xxx numbering before relying on it.
See Principle 31.

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
**[v2.5]** Every `concern_*.md` requires Concept Frontmatter — see **Concept Frontmatter Standard**.

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
- **[v3.1]** When an Action ID's meaning changes — e.g. a placeholder or completed ID gets reassigned to unrelated work — audit `07_Milestones/*/milestone.md` for any stale citation of that ID's old meaning and correct it in the same session. See Principle 31.

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

### [v3.2] principal_architect_agent — On-Demand External Architecture Review

- **Role:** Re-reviews an existing architecture, module design, or plan against current external best practice — official documentation, established engineering references, recent community discussion — at a milestone or task boundary a human chooses. Not a periodic automatic gate: it runs only when invoked.
- **Called by:** Human only, never by `captain_agent`, `commander_agent`, or `superman_agent`.
- **Calls:** Nothing — it is a terminal, findings-producing agent. Uses web search/fetch to gather external comparison material.
- **Reads:** the design set in scope (`03_System_Design/`, relevant ADRs), `CLAUDE.md`, and whatever milestone/task the human names.
- **Writes:** a dated findings document under the affected module's directory (`principal_architect_review_<date>.md`), separating must-fix-before-proceeding / worth-tracking / no-change-needed. Any proposed design change is a redline against the existing docs — it never rewrites `03_architecture.md` or an ADR in place.
- **Relationship to existing agents:** distinct from `architect_agent` (owns day-to-day design, never does broad external research) and `reviewer_agent` (reviews implementation prompts against static internal docs, no external research). Closest in spirit to `research_and_review_agent` but scoped to re-reviewing the project's *own* already-built architecture rather than studying named external systems pre-lock.
- A human acts on its findings by tasking `architect_agent` with the accepted changes, or by re-running `captain_agent` if a finding implies new execution-plan tasks.

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
| `tracker_sync_agent` | On `Tracker: sync` (Export Mode) or `Tracker: import <ref>` (Import Mode) — only if `tracker_config.md` exists | **[v2.5]** Generalizes `jira_sync_agent` to Jira *or* Notion (Principle 25); never runs on its own initiative (Principle 24), needs a human-issued command every time |
| `jira_sync_agent` | **[v2.5] Superseded** — kept working unchanged for projects mid-transition; new projects get `tracker_config.md` (`Provider: jira`) and use `tracker_sync_agent` instead | See **Tracker Board Integration** below |
| `concept_indexer_agent` | On `Learn: rebuild`, `Learn: open`, or `Learn: check coverage` | **[v2.5]** Read-only over the whole documentation tree, write-only to `16_Learning_Roadmap/`; never runs on its own initiative (Principle 24 discipline extended a third time). Generates `render/index.html` by inlining `AOSDF/renderer_core/` (see **Track L Renderer Core** below). See **Learning Roadmap** below |
| `docs_site_agent` | On `Project Docs: build`/`Project Docs: open` | **[v2.5, restructured 2026-08-19]** Thin wrapper — runs `mkdocs build` against `{project_name}-Documents/mkdocs.yml`, or opens the already-built site; never authors config, never runs on its own initiative. Renders your project's own docs only — `AOSDF/` has no site of its own. See **MkDocs-Based Project Docs Site** below |
| `principal_architect_agent` | At a milestone or task boundary the human chooses, for a deep external-informed re-review | **[v3.2]** Never auto-called; produces a dated findings doc, never a silent rewrite. See **principal_architect_agent** above and Principle 32 |

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

### [v3.2] Superman Modes: Discipline vs Normal

`superman_agent` combines Commander's orchestration with an implementor's execution, running a whole milestone without per-task human approval. It now takes a `mode` input:

```
mode: normal (default)
  → Superman's pre-existing behavior: reads execution_plan.md's strategy line
    (or an explicit strategy_override) and runs Strategy A or Strategy B per task,
    exactly as before this version.

mode: discipline
  → Every task in the queue runs the full Strategy B pipeline regardless of what
    execution_plan.md's strategy line says:
      architect_agent → reviewer_agent → implementor → validator_agent
  → No task's implementation prompt reaches execution without reviewer_agent's
    sign-off first — this is what "discipline" adds over normal mode.
  → The no-per-task-human-approval gate Superman removes stays removed in both
    modes; discipline mode adds an automated review gate, not a human one.
```

Superman's session header (see `agents/superman_agent.md`) prints the active mode, and every stop/resume message carries it forward so a resumed run doesn't silently fall back to `normal`.

### [v3.2] Scope Expansion Protocol — Out-of-Scope Work Discovered Mid-Task

Applies inside `commander_agent`'s per-task delegation, `execution_agent`'s implementation step, and `superman_agent`'s per-task loop (both modes). If completing the current task genuinely requires a task that does not exist in `execution_plan.md` or the current milestone's scope:

1. **Log it** to `06_Execution_Plan/scope_expansion_log.md`: discovering task ID, a clear description of the proposed new task, why it's required (blocking vs. merely improving), and a suggested milestone placement.
2. **Stop the loop** — do not implement the out-of-scope work, and do not skip past it to a later task in the queue:
   ```
   === SCOPE EXPANSION DISCOVERED ===
   Stopped after/before: <TASK-ID>
   Discovered need: <proposed task description>
   Why required: <blocking | improves current task, not strictly required>
   Logged to: 06_Execution_Plan/scope_expansion_log.md

   Resolve by: re-running captain_agent to fold this into the plan, or recording
   an explicit deferral in the log.
   Resume command: <same form as a Manual Action Required stop>
   ```
3. A human resolves it — via `captain_agent` (adds the task to `execution_plan.md`/a milestone) or by writing an explicit deferral into the log — before the paused agent resumes.

No agent ever adds an unplanned task to `execution_plan.md` on its own initiative; this mirrors Principle 2 (contract-first) and the existing "no scope additions" rule each Strategy A/B implementor already follows for the *current* task.

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

## [v2.5] Concept Frontmatter Standard

A second metadata standard, parallel to the Document Formatting Standard above — that one governs table layout, this one governs a small YAML block at the top of a file that carries a real design decision. It is the raw material an independently-tracked capability (`16_Learning_Roadmap/`, not part of this framework's own execution — see that folder's own documentation when it exists in a project) derives a personal interview-prep roadmap from, without asking anyone to write a second copy of anything.

### Required on

Every ADR (`03_System_Design/ADR/*.md`, `03_System_Design/NNN_<name>_module/decisions/*.md`), every module `02_domain_model.md` and `03_architecture.md`, `02_Security_Framework/threat_model.md`, `04_Infrastructure_Design/*.md`, and `13_Legal_Requirements/concern_*.md` (when present). Optional on any other document that happens to carry a teachable decision.

### The block

```yaml
---
concepts: [caching-strategies, cache-invalidation, redis-internals]
concept_category: Distributed Systems
difficulty: intermediate
prerequisites: [http-caching-basics]
interview_angle: >
  Be ready to explain why write-through was chosen over write-back here,
  and what happens to an in-flight write if the cache node fails mid-request.
built_at: M2-T4
diagram: true
---
```

| Field | Purpose |
| --- | --- |
| `concepts` | Short, reusable topic IDs. The same ID can appear on multiple docs — they merge into one concept with multiple source links. |
| `concept_category` | A coarse bucket (Distributed Systems, Data Modeling, Security, Networking, API Design, DevOps/Infra, Concurrency) for filtering. |
| `difficulty` | `fundamental` \| `intermediate` \| `advanced` — a coarse hint, refined by the prerequisite graph. |
| `prerequisites` | Other concept IDs this one assumes — the edge list a pedagogical ordering would sort from. |
| `interview_angle` | One or two sentences, written by whoever made the decision, framing it as something you'd say out loud in an interview. |
| `built_at` | The task ID (`M2-T4`) this was written under — already known by whichever agent is executing that task. |
| `diagram` | `true` if the doc includes an `aosdf-diagram` fenced block (below) worth surfacing separately. |

### Who fills it in

`architect_agent` fills this in as part of authoring an ADR or a module's `02_domain_model.md`/`03_architecture.md` — the same way it already writes the document's title and status (see its `## Output` section). For the three Phase-0, human-authored document types (`threat_model.md`, `04_Infrastructure_Design/*.md`, `13_Legal_Requirements/concern_*.md`), the human fills it in while writing the document, the same glance they already give the rest of it — never a separate task, checklist item, or session (Principle 29).

### Coverage

A required document missing this block is a `Category: Learning, Severity: Low` gap in `identified_gaps.md` — the same table an unmapped FRD requirement uses at `Severity: Critical`, just a weight that reflects "nice to have," never a blocker to execution (Principle 29).

### The `aosdf-diagram` fenced-block convention

This file's own "Full Lifecycle Flow" diagram and the Workspace Layout tree below are already hand-drawn, monospace box diagrams — this formalizes that existing house style into a fenced block rather than adopting a diagramming library that would add an external dependency:

````markdown
```aosdf-diagram
┌─────────────────────┐        ┌──────────────────────┐
│   Client Request     │──────▶ │   Rate Limiter (L1)   │
└─────────────────────┘        └──────────┬───────────┘
```
````

Any document with `diagram: true` is expected to contain at least one such block. It changes nothing about how the diagram is drawn — plain box-and-arrow ASCII, git-diffable, no tooling required — only that it is fenced so a renderer can detect and present it as a distinct panel later. Wrapping an existing diagram in this fence never counts as rewriting it.

---

## [v2.5] Learning Roadmap

### What This Is

`16_Learning_Roadmap/` is an index derived entirely from Concept Frontmatter (above) — it contains no original prose (Principle 28). It exists so a project's real design decisions, already captured as five extra YAML lines on documents an agent or human was writing anyway, become a single readable "what I've learned building this" record, without a separate authoring task ever being scheduled (Principle 29).

### Current Scope (L3) — Table, Graph, and Two Views on One Viewer

`concept_indexer_agent` produces three outputs on `Learn: rebuild`: `16_Learning_Roadmap/roadmap_index.md` (the flat human-readable table — concept ID, category, difficulty, source document(s), `built_at`), `roadmap_graph.json` (the same nodes as a machine-readable object, plus each node's `aosdf-diagram` text verbatim when its source document has `diagram: true`), and `render/index.html` — a single self-contained file with the graph JSON inlined as a `<script type="application/json">` block, so opening it via `file://` never hits a CORS failure trying to `fetch()` a sibling JSON file. Deduplication merges the same concept ID across multiple source documents into one row/node with multiple source links.

The renderer shows two views over the same dataset, switched by a tab, both with category/difficulty filters and Prev/Next navigation:
- **Build Order** — sorted by `built_at`, the order things actually got decided.
- **Learn Order** — a topological sort over `prerequisites`, computed client-side at render time (never precomputed into `roadmap_graph.json` — ordering is the renderer's job, not the index's). Fundamentals-first, "if I were studying this cold" order.

A `localStorage` "mark reviewed" checkbox on each card (page-scoped, never synced anywhere) drives a "Reviewed: N / total" count in the header — purely the developer's own personal tracking. A node whose prerequisites form a cycle, or reference an ID that doesn't resolve to any known concept, is never silently dropped from Learn Order: it falls back to its Build Order position, visibly badged — computed independently by the renderer itself, not merely trusted from what `concept_indexer_agent` already logged (see **Cycle / Orphan Detection** below).

### Sync Is Always Human-Triggered

```
Learn: rebuild         → concept_indexer_agent scans the doc tree, regenerates roadmap_index.md,
                          roadmap_graph.json, and render/index.html
Learn: open             → opens render/index.html in the default browser, or reports its path
Learn: check coverage  → identify_missing_documents' Concept Frontmatter check only, no rebuild —
                          reports which required documents are missing the block
```

Exactly the same discipline as `Wiki:` and `Tracker:`/`Jira:` commands (Principle 24, extended a third time): no agent calls `concept_indexer_agent` on its own initiative.

### Coverage Gaps Are Low Severity, Never a Blocker

`identify_missing_documents` logs a required document missing Concept Frontmatter as `Category: Learning, Severity: Low` in `identified_gaps.md` — the same table, a different weight than an unmapped FRD requirement (`Category: Coverage, Severity: Critical`). It never blocks execution (Principle 29).

### Cycle / Orphan Detection

Two independent layers, deliberately redundant, never allowed to disagree in substance:
- **`concept_indexer_agent` (the logged record).** On `Learn: rebuild`, a `prerequisites` entry that doesn't resolve to any known `concepts` ID, or a prerequisite cycle, is annotated in `roadmap_index.md`'s Notes column and appended to `identified_gaps.md` (`Category: Learning, Severity: Low`) — never dropped, never escalated.
- **The renderer (the display guarantee, L3).** `render/index.html`'s Learn Order view runs its own cycle/orphan check over the same `prerequisites` edges, independently of whatever this agent already logged. A node it can't place topologically falls back to its Build Order position, badged — this is what makes "the renderer never silently drops a concept" true even if the index-generation step were somehow stale or wrong, not just a restatement of what was already logged.

---

## [v2.5] Track L Renderer Core (Learning Roadmap Only)

### What This Is

`AOSDF/renderer_core/` (`core.js` + `core.css`) is the rendering logic behind `16_Learning_Roadmap/render/index.html` — `markdownToHtml`, the `aosdf-diagram` panel, table rendering, a nav builder, and a search-index builder, plus the shared design tokens. It was originally built (D0-T1) with the intent of also backing the Docs Browser and Project Docs Site; that plan changed — see **MkDocs-Based Documentation Sites** below for why and what replaced it. `renderer_core/` now serves **Track L only** (L2/L3's Build Order / Learn Order viewer). It is source, not a generated artifact — a human or `frontend_agent` maintains it directly, the same way any other file under `AOSDF/` is maintained.

`render/index.html` inlines `core.js` and `core.css`'s full text verbatim into its single-file HTML output — never a `<script src="…">` reference to a shared external file, which would reintroduce the exact `file://` CORS failure the inlining approach (Principle 30) exists to avoid.

Only the diagram panel and shared design tokens are actually exercised today — `render/index.html` renders structured JSON as cards, not raw markdown pages, so `markdownToHtml`, `buildNav`, and the search index builder sit unused. That's fine; they're not being removed on the chance a future Track L feature needs them, but they're not scope for anything beyond Track L either.

---

## [v2.5, E0] Project Setup — Sequenced Initial Questions

`workflow_initiator` Step 1 is now a fixed, ordered, 14-question sequence — asked one at a time, with two explicit branch points — rather than an unordered list with no stated rationale for its order. Full detail lives in `workflow_initiator.md` Step 1 and `aosdf_expansion_scope.md` §4.4; this is the pointer, not a third copy.

**The two branches that can end the sequence early or redirect it:**
- **Q1 — new vs. existing.** "Expand or improve an existing product/project" stops `workflow_initiator` entirely and points at `expand_existing_products/00_README.md` (Track X) instead — running the full setup sequence on a project that already has structure would re-propose things it doesn't need.
- **Q4 — reference documents.** If none exist yet, the agent does not proceed to Q5 until a fixed, blocking minimum-context interview is complete (target users, core features, business goal, known constraints), written to a new `reference/founder_interview.md` — a raw input for Phase 1 to start from, not a finished FRD/BRD. `workflow_initiator` explicitly does not attempt to synthesize a full FRD/BRD from this interview itself; that overstates what a setup agent should own.

**Four setup-time toggles, each recorded once in `project_status.md` § Project Configuration and never re-asked automatically** (the same one-time-decision discipline Principle 24 already applies to the tracker sync cadence):

| Question | Default | What it gates |
| --- | --- | --- |
| Q9 — Adopt IDE tooling? | No | `workflow_initiator` Step 8 (copies `.claude/` + `.mcp.json` into `{project_name}/`, `E3-T1`) |
| Q10 — Enable Learning Roadmap (Track L)? | Yes | `identify_missing_documents`'s Concept Frontmatter Coverage Checklist — disabling skips the check, not the standard itself |
| Q11 — Enable Project Docs Site (Track P)? | Depends on stakeholder count | Whether `PJ1-T1` (`mkdocs.yml` authoring) is ever run — `docs_site_agent`'s existing precondition already refuses to act without it, so disabling needs no other enforcement |
| Q14 — Milestone generation mode? | Auto | Whether `captain_agent` derives milestone boundaries itself from the FRD (Auto, today's existing behavior, now named) or formalizes a human-supplied outline (Manual) |

Q9 is worth calling out specifically: `aosdf_expansion_scope.md` Sec 6 item 4 committed to this exact question years before it was implemented — this section closes that gap rather than introducing a new one. Its default stays **No** even though `E3-T1` shows the feature itself carries no real risk (no credentials, nothing runs until a subagent or slash command is actually invoked) — the honest move was to implement the commitment as originally scoped, not to quietly change the default while finally building it.

**One cosmetic-only toggle:** Q12 lets a human rename the *display* label of the main agents (Commander, Captain, Architect, etc.) shown in the copied `{project_name}-Documents/documents/05_AI_Agent_System/agents/*.md` files. It never touches the technical identifier `.claude/agents/<role>.md` (`E3-T1`) uses — those stay e.g. `execution-agent` regardless, because slash commands and `Agent(...)` delegation restrictions reference those exact names. Stated plainly rather than implied otherwise, matching how every other scope limit in this framework is documented.

**`Step 1 Q8` (tracker sync opt-in, `E1`) keeps its exact position** — six files already cite it by that name (`jira_sync_agent.md`, `tracker_sync_agent.md`, `.claude/commands/aosdf-sync.md`, plus this meta-project's own tracking docs). The four new/reframed questions before it (Q1, Q2, Q4, and the Q1/Q2 merge) were sized so they net to zero position change; the new questions after tracker sync (Q9-Q14) don't affect it at all.

---

## [v2.5, E2-T1] `aosdf-mcp` Server

### What This Is

`AOSDF/aosdf-mcp/` is the MCP server `aosdf_expansion_scope.md` §4.2 scoped: exactly six read/write tools over a project's own markdown files, so the editor extension (Pillar A) and every Claude Code agent (Pillar B) go through one audited interface instead of ad hoc file edits (Principle 26). Bundled inside `AOSDF/` rather than a standalone package, per OD-3 (resolved 2026-08-27). It holds no state of its own — every call re-reads the file it needs and re-derives its answer, so restarting the process loses nothing and two tool calls in a row never see stale data relative to a file changed in between.

Built with zero runtime dependencies — the stdio JSON-RPC framing MCP's transport uses is a handful of lines of newline-delimited JSON, so hand-rolling it keeps this package consistent with the zero-dependency discipline Principle 30 already holds the Learning Roadmap renderer to, and means it never blocks on an `npm install` reaching a registry from an offline or sandboxed agent session.

### The Six Tools

| Tool | Reads / Writes | Notes |
| --- | --- | --- |
| `aosdf_read_status` | `project_status.md` | Extracts `Current State` and the `## Next Action` section only — not the whole file's prose |
| `aosdf_next_planned_task` | `execution_plan.md` | First row, in document order, whose ID matches a task pattern (`*-T<n>`) and whose `Status` is exactly `Planned` — a phase-level Master Sequence row (e.g. `E2`) is never returned by this tool, only an actual task (e.g. `E2-T1`) |
| `aosdf_update_task_status` | `execution_plan.md` | The only tool allowed to write this file. Locates the row by matching a given ID against whichever column is actually named an ID column (`Task ID`, `Phase ID`, or `ID` — not always column 0, e.g. the Master Sequence table's ID column is its *second* column), then rewrites just that row's `Status` cell and re-pads the whole table per the Document Formatting Standard |
| `aosdf_log_gap` | `identified_gaps.md` | Appends a row; auto-generates the next `GAP-NNN` ID and today's `Identified` date |
| `aosdf_log_manual_action` | `12_Manual_Actions/actions.md` (or a documented single-file deviation, via `AOSDF_MANUAL_ACTIONS_PATH`) | Appends to the *Pending* table specifically, never *Completed*; auto-generates the next `MA-N` ID |
| `aosdf_read_module_index` | `03_System_Design/README.md` | Returns the module registry as structured rows |

Every writer goes through the same `markdown-table.js` helper, so a write is never a hand-edited single cell — it recomputes column widths across the whole table and re-renders every row, which is what keeps a written file automatically compliant with the Document Formatting Standard (manual.md §Document Formatting Standard) rather than relying on the caller to have padded correctly.

### Configuration

One required environment variable, `AOSDF_DOCS_ROOT`, pointing at a project's `{project_name}-Documents/docs/` folder. Each of the six files above resolves to a sane default path under that root, and each can be overridden individually (`AOSDF_PROJECT_STATUS_PATH`, `AOSDF_EXECUTION_PLAN_PATH`, `AOSDF_IDENTIFIED_GAPS_PATH`, `AOSDF_MANUAL_ACTIONS_PATH`, `AOSDF_MODULE_INDEX_PATH`) — this is how a project that documents a layout deviation (e.g. this meta-project's own `manual_actions.md` living at its docs root instead of under `documents/12_Manual_Actions/`) stays servable without forking the tool.

### Known Scope Limits

Column matching is by header name, not a fixed schema, so a project's exact column set doesn't need to match `templates.md`'s example verbatim — but a table with no recognizable ID or Status column is silently skipped by the tools that need one. `aosdf_log_gap` and `aosdf_log_manual_action` each operate on one table (the first table found, or — for manual actions — the one under a heading matching "Pending"); a file with more than one candidate table beyond that convention needs its own path override or isn't yet handled generically. `id`/`status` column-name matching accepts a bare `"ID"`/`"Status"` header as well as the templated `"Gap ID"`/`"Action ID"`/`"Task ID"`/`"Phase ID"` forms, across all six tools.

### `E2-T3` Principle 26 Compliance Audit — Passed 2026-08-28

`validator_agent` read every file in `src/`: no tool caches, holds, or duplicates file content across calls — each reads its source file fresh per call and, for a write, writes straight back immediately (`index.js`'s `paths` object is just resolved file *locations* from env vars at startup, not cached content). Recorded in `{project_name}-Documents/docs/documents/02_Security_Framework/compliance_checklist.md` row 5, superseding a prior "by design" claim made before this package existed.

Auditing against this meta-project's own real files — not just the checked-in test fixtures, which had all used the canonical `"Gap ID"`/`"Action ID"` headers — surfaced two real, unrelated defects, both fixed same-day: `aosdf_log_gap`/`aosdf_log_manual_action`'s ID-column regex didn't recognize this project's own bare `"ID"` header in `identified_gaps.md`, so a real call would have silently written a row with a blank ID cell; and the package's own `npm test` script (`node --test test/`) threw `MODULE_NOT_FOUND` on Node 24 — fixed to `node --test` (default discovery). Both logged and resolved as `identified_gaps.md` GAP-001/GAP-002, written by the newly-fixed tool itself as the first two rows ever added to that file. A regression test (bare-`"ID"`-header fixture) now covers the fix; suite is 14/14.

---

## [v2.5, E3-T1/E3-T2] Claude Code Native Integration

### What This Is

`aosdf_expansion_scope.md` §4.2 (Pillar B) scoped four artifacts so an AOSDF agent stops being "a prompt template a human hand-copies into chat" and becomes a real Claude Code feature. Item 4 (`aosdf-mcp`) shipped as `E2-T1`. This section covers the other three: subagent definitions + slash commands (`E3-T1`) and the session-context hook (`E3-T2`).

All of it lives as a master template at `AOSDF/.claude/` and `AOSDF/.mcp.json` — `workflow_initiator` Step 8 copies the whole thing into **`{project_name}/`**, not the workspace root and not `{project_name}-Documents/`. This isn't a style choice: `folder_map.md` marks `{project_name}/` as the only real git repo in the workspace. Placing `.claude/` anywhere else would mean it never reaches a teammate's `git clone`, silently breaking the "ships automatically to anyone using Claude Code in that repo" goal `aosdf_expansion_scope.md` §4.2 item 1 states directly. `AOSDF/.mcp.json`'s paths (`../AOSDF/...`, `../{project_name}-Documents/...`) are pre-written relative to that destination, one level below the workspace root — they're not meant to resolve correctly left in place inside `AOSDF/` itself.

### Subagent Definitions (`E3-T1`) — 20 Files, One Per Agent Role

Every AOSDF agent role — the 19 files under `AOSDF/agents/` plus `workflow_initiator` — gets a `.claude/agents/<role>.md` Claude Code subagent definition. Each one is deliberately thin: its `tools:` frontmatter translates that agent's `## Permissions` section into Claude Code's tool-allowlist, and its body is a pointer ("your complete operating instructions live in `AOSDF/agents/<file>.md` — read it and follow it exactly"), never a restatement. This mirrors the same pointer-not-copy discipline `reference/README.md` already applies to raw product-knowledge inputs (Principle 26/28's shared spirit): one file stays the source of truth, everything else references it.

Five agent roles (`architect_agent`, `backend_agent`, `frontend_agent`, `infra_agent`, `qa_agent`) have no formal `## Permissions` block in their source file — only prose Constraints/Output sections. Their `tools:` lists were derived from that prose plus `reference/agent_index.md`'s authoritative Permission Summary table, not guessed independently.

Where an agent's Permissions already name one of `aosdf-mcp`'s six files (`execution_plan.md`, `identified_gaps.md`, `12_Manual_Actions/actions.md`), its subagent definition is granted the matching `mcp__aosdf-mcp__*` tool and told to use it instead of `Edit`-ing that file directly — `aosdf_update_task_status`'s own description already states it's "the only tool allowed to write execution_plan.md." **This is a prompt instruction, not a technical wall**: Claude Code's `tools:` frontmatter is coarse (whole-tool grants only), with no documented way to deny `Edit` on one specific path while allowing it on every other file. Stated plainly rather than implied otherwise — the honest scope limit here is the same kind already called out for `aosdf-mcp` itself.

`commander_agent` and `architect_agent` are the only two subagents that delegate to others (to `execution-agent`/`architect-agent`, and to `reviewer-agent`, respectively) — both use the `Agent(name1, name2)` restriction syntax so they can't spawn anything outside the pipeline stage they're actually in.

### `git push` — WRITE_REMOTE Becomes a Technical Control (`E3-T1`)

Every AOSDF agent's Permissions already say "WRITE_REMOTE: none — git push is always a human action." Claude Code's subagent frontmatter has no per-command restriction (confirmed against current docs: `tools: Bash` is all-or-nothing at the whole-tool level), so this can't be enforced per-agent in the `tools:` list. Instead, `.claude/settings.json` (copied to every project alongside the subagents) carries a project-wide `permissions.deny: ["Bash(git push:*)"]` rule — this is exactly where `aosdf_expansion_scope.md` §4.2 item 1 said "this is where the human-only git-push rule becomes a technical control instead of just a documented one," achieved at the project level rather than per-subagent, which is the only level Claude Code actually exposes for this.

### Slash Commands (`E3-T1`)

Seven thin `.claude/commands/*.md` wrappers around the exact invocation shapes `manual.md` and each agent's own "When to Invoke" section already document — no new decision logic, per §4.2 item 2:

| Command | Wraps |
| --- | --- |
| `/aosdf-init` | `workflow-initiator` |
| `/aosdf-plan` | `captain-agent` |
| `/aosdf-next` | `commander-agent` (session start) |
| `/aosdf-addendum <path>` | `addendum-agent` |
| `/aosdf-research <task.md>` | `research-and-refine-agent` |
| `/aosdf-sync` | `tracker-sync-agent`, Export Mode ("Tracker: sync") |
| `/aosdf-import <ref>` | `tracker-sync-agent`, Import Mode ("Tracker: import \<ref\>") |

Current Claude Code docs confirm `.claude/commands/<name>.md` still works exactly as before ("custom commands have been merged into skills... your existing `.claude/commands/` files keep working") — this package uses that format rather than migrating to `.claude/skills/<name>/SKILL.md`, since the simpler single-file form is sufficient here and matches the naming `aosdf_expansion_scope.md` already used.

### Session-Context Hook (`E3-T2`) — Principle 27

`manual.md`'s Session Context Management Rule 2 ("do not start a task you cannot finish," target "never exceed 60% context usage before starting a new task") was, until now, an honor-system instruction the Commander was trusted to self-police. `AOSDF/.claude/hooks/session-context-gate.js` turns it into a real `PreToolUse` gate, wired in `.claude/settings.json` against the `Task|Agent` matcher — the closest real approximation to "before a task is delegated" that Claude Code's hook events actually expose (there is no documented "before delegation decision is made" event; `PreToolUse` on the tool that spawns a subagent is the nearest honest equivalent).

**Stated plainly, the same way `aosdf-mcp`'s scope limits are stated:** Claude Code's hook input carries no direct token-count or context-percentage field (confirmed against current hook docs). The hook estimates usage itself by reading the transcript JSONL at `transcript_path` and taking the most recent turn's `usage.{input_tokens, cache_creation_input_tokens, cache_read_input_tokens}` — the same numbers the Anthropic API returns for that turn. It compares the sum against `AOSDF_CONTEXT_WINDOW` (default 200,000 — a placeholder, not a claim about any specific model's real window; set it per-project) at a threshold of `AOSDF_CONTEXT_THRESHOLD` (default 0.6, matching Rule 1's stated target exactly). On any parse failure, missing transcript, or absent usage data, it **fails open** — allows the call — rather than blocking on a guess. 12/12 tests pass (`AOSDF/.claude/hooks/test/`), covering the parsing, threshold math, env-var overrides, and the real hook process's stdin/stdout contract end to end.

### Known Scope Limits

- No fine-grained per-path tool restriction exists in Claude Code's subagent frontmatter — the `mcp__aosdf-mcp__*`-instead-of-`Edit` guidance above is enforced by instruction, not by the platform.
- `git push` denial is project-wide (`.claude/settings.json`), not per-subagent — Claude Code has no subagent-scoped equivalent today.
- The context-usage estimate depends on `transcript_path`, which the docs state is written asynchronously and "may lag" the current turn, and on an assumed context-window size that varies by model and isn't reliably present in the hook's own input.
- `tracker-sync-agent`/`jira-sync-agent`'s subagent definitions don't list a specific Jira/Notion MCP tool name — those are registered per-project, per whichever provider `tracker_config.md` names, not something this template can hardcode generically.

---

## [v2.5, E4-T1/E4-T2] Editor Integration MVP (Read-Only, VSCode First)

### What This Is

`aosdf_expansion_scope.md` §4.1 (Pillar A) scoped an editor extension as a thin shell over `aosdf-mcp` (`E2-T1`) — the extension holds no logic or state of its own, only chrome. `execution_plan.md`'s `E4` phase narrowed the original draft scope: the Documentation Tree, Execution Plan Table, Milestone Board, and Module Index views moved to Track P's rendered site (`PJ1`) instead of being built twice. What remains for `E4` is the two genuinely editor-native affordances plus a link-out command:

- **Status bar chip** (`E4-T1`) — current project state and next `Planned` task, sourced from `aosdf_read_status`/`aosdf_next_planned_task` over `aosdf-mcp`'s stdio JSON-RPC protocol, not a re-implementation of either tool's parsing.
- **Gaps & Manual Actions inbox** (`E4-T1`) — a tree view listing every open row in `identified_gaps.md` and `manual_actions.md`. `aosdf-mcp` exposes only *append* tools for these two files (`aosdf_log_gap`, `aosdf_log_manual_action`) — no list tool — so the extension reads and parses both files directly, reusing `aosdf-mcp`'s own `markdown-table.js`/`config.js` modules rather than a second parser. This is still Principle-26-safe: nothing is cached across refreshes, and every refresh re-reads from disk.
- **`AOSDF: Open Project Docs`** command (`E4-T2`) — a thin wrapper opening Track P's built site (`docs_site_agent.md`'s `Project Docs: build` output). Unblocked once `PJ1` shipped.

Built at `AOSDF/aosdf-vscode/`, plain JS (no build step), zero runtime dependencies — the extension talks to `aosdf-mcp` by spawning it as a child process and speaking the same newline-delimited JSON-RPC 2.0 protocol `AOSDF/aosdf-mcp/src/index.js` implements (`src/mcpClient.js`), consistent with Principle 30's zero-dependency discipline already holding the Learning Roadmap renderer and `aosdf-mcp` itself.

### Where It Lives — Not Copied Into `{project_name}/`

Unlike `.claude/`/`.mcp.json` (`E3-T1`), `aosdf-vscode/` stays at `AOSDF/aosdf-vscode/` and is **not** copied anywhere: it isn't packaged for the VS Code Marketplace yet (`E4-T3`, tracked as `OD-1` in `execution_plan.md` Sec 4, remains an open human decision — public vs. internal distribution). Packaging is `E6`'s job, not `E4`'s. In the interim, `workflow_initiator` Step 8 (gated the same as `E3-T1`, on Step 1 Q9) writes `{project_name}/.vscode/settings.json` with the extension's three settings (`aosdf.documentsRoot`, `aosdf.mcpServerPath`, `aosdf.projectDocsSitePath`), so a developer only has to press F5 in `AOSDF/aosdf-vscode/` and open `{project_name}/` in the resulting Extension Development Host window — the settings take effect automatically, no manual configuration required.

### Known Scope Limits

- No list tool exists in `aosdf-mcp` for gaps/manual actions, so the inbox view reads those two files directly rather than exclusively through the MCP surface — stated here rather than left implicit, matching how `aosdf-mcp`'s own scope limits are documented.
- Not packaged for any marketplace or extension gallery — `E4-T3`/`OD-1` is open, and `E6` is where that gets resolved.
- Read-only by design (`E4`'s explicit scope): no command in this MVP writes to any AOSDF file. Write actions (invoking agents, approving prompts, triggering tracker sync from the command surface) are `E5` — see § Editor Integration Write Actions below.
- VSCode only for now — the underlying logic (`aosdf-mcp`, Claude Code subagents/commands) is already editor-independent, so a later port to another IDE is additive, not a rearchitecture.

---

## [v2.5, E5-T1] Editor Integration Write Actions

### What This Is

`execution_plan.md`'s `E5` phase adds the three write-capable affordances `aosdf_expansion_scope.md` §4.1/§4.2 scoped: invoking an agent from the command surface, approving an implementation prompt inline, and triggering tracker sync — all from inside `AOSDF/aosdf-vscode/` (`E4`), without ever letting the extension become a second writer of any AOSDF file.

**The mechanism is a terminal, not an MCP tool call.** Every one of these three actions is, mechanically, the same primitive: reveal a named integrated terminal ("AOSDF") and type text into it (`src/terminalRunner.js`). `AOSDF: Run Agent Command...` offers a `QuickPick` over the 7 slash commands `.claude/commands/*.md` (`E3-T1`) already wires, prompting for an argument where the command needs one (`/aosdf-addendum`, `/aosdf-research`, `/aosdf-import`); `AOSDF: Trigger Tracker Sync` is a one-click shortcut for `/aosdf-sync`; `AOSDF: Approve & Send` opens the pending prompt file for review, then sends the literal text `Approve to execute`. In every case, whatever actually changes on disk happens inside the Claude Code session already running in that terminal, through that session's own agents and their own Permissions — exactly as if the human had typed the same text by hand. This is deliberately not a second, extension-side execution path: the extension performs **zero** direct file writes for any of the three actions, which is what the task's Principle 26 audit confirmed rather than assumed.

This mechanism was chosen over trying to call a hypothetical Claude Code extension API from `aosdf-vscode` (unverified, and would couple a generic VS Code extension to Anthropic's own extension internals) and over inventing a new MCP tool that "invokes an agent" (aosdf-mcp's whole design is narrow, auditable file read/write tools per Principle 26 — spawning an agent session isn't a file operation, so it doesn't belong there either).

### Implementation Prompts Inbox — Closing a Real, Pre-Existing Gap

`templates.md` has specified `implementation_prompts/README.md`'s Log table (`Prompt File | Task | Created | Executed | Status`) since v1.2, but no agent's operating steps ever actually wrote to it — the table existed only as an unfulfilled template promise, the same category of gap `E0` found in `aosdf_expansion_scope.md`'s Q9 commitment. `E5-T1` closes it for the two paths that could be fixed without redesigning Strategy B's pipeline:

- `execution_agent.md` (Strategy A) — Step 2 now appends a `Pending Approval` row when the prompt is saved; Step 6 flips it to `Executed` once validation passes and `execution_plan.md` is updated.
- `superman_agent.md` — Step 1.7 appends the row directly as `Executed (Superman — no approval gate)`, since Superman's whole design removes the pause between generating and executing a prompt (Step 1.4's own text: "Do NOT pause for human approval — this is the gate Superman removes"). Labeling it this way keeps the log honest about which prompts skipped the human gate, rather than making them look indistinguishable from an approved one.
- Strategy B (`architect_agent` → `reviewer_agent` → implementor) is **not** wired — neither file currently specifies the mechanics of saving/logging a prompt concretely enough to extend safely without a larger pass over that pipeline. Logged as `identified_gaps.md` GAP-003 rather than silently left unfixed.

`aosdf-mcp/src/config.js` gained an `implementationPromptsIndex` path (`documents/05_AI_Agent_System/implementation_prompts/README.md`, env-overridable like every other path) so `aosdf-vscode`'s `src/promptsData.js` resolves it the same canonical way as every other tracked file — no aosdf-mcp tool reads or writes it; there was no read need until this extension existed, and the two agents above write it directly as part of their own existing WRITE_LOCAL permissions.

### Known Scope Limits

- Depends on the human already running (or being willing to run) `claude` in the same "AOSDF" integrated terminal the extension sends text into — the extension does not start a Claude Code session itself.
- Strategy B's implementation-prompt lifecycle isn't logged to `implementation_prompts/README.md` yet (`identified_gaps.md` GAP-003) — the Implementation Prompts inbox will under-report for Strategy B projects until that's addressed.
- `AOSDF: Approve & Send` sends a fixed approval string; it has no way to know whether the terminal it's typing into is actually the one running the session awaiting that specific prompt's approval — the human is trusted to have the right terminal focused, same as if they'd typed it themselves.

---

## [v3.0, E6] GA Hardening

`OD-1` (editor extension distribution model) resolved internal-only on 2026-08-29 — no public VS Code Marketplace listing, scoped to the VSCode release specifically. That unblocked `E6`'s three build tasks (`E6-T4`, the `manual.md` walkthrough update, lives in `manual.md` itself rather than being duplicated here).

### E6-T1 — Formatting Linter (`aosdf-lint`)

`AOSDF/aosdf-mcp/src/lint.js` + `src/lint-cli.js` (`npm run lint -- <path> [--fix]`, or `aosdf-mcp`'s `bin.aosdf-lint`). Deliberately reuses `markdown-table.js`'s own `renderTable()` as the sole definition of "compliant" — a table passes if and only if re-rendering it reproduces its current lines verbatim. This is not a second, parallel implementation of the Document Formatting Standard that could drift from what the write tools already enforce (Principle 26): it's the exact same function every write tool already goes through, run in the other direction (check instead of write).

Scope is deliberately Rules 1–2 only (separator-dash width, cell padding) — the two rules a table can be mechanically judged against in isolation. Rules 3 (consistent widths for the same schema *across files*) and 4 (blank rows between logical groups) both require recognizing "the same schema" or "a logical group," a semantic judgment the tool doesn't attempt. `--fix` uses the same `replaceManyTables` primitive every write tool already uses, so a fixed file is indistinguishable from one an agent wrote correctly the first time.

**Dogfooding finding:** running `aosdf-lint` over this entire workspace turned up 182 Rule 1/2 violations across 72 files — almost entirely hand-authored prose/reference tables (BRD.md, FRD.md, `execution_plan.md`'s own Sec 1 reference table, `evolution.md`, `aosdf_expansion_scope.md`, `expand_existing_products/`) that were never run through the write tools and so were never actually held to the standard, despite `manual.md` Rule 5 stating "no exceptions for quick or small tables." Not auto-fixed: a workspace-wide `--fix` pass is a large, mostly-cosmetic diff across many files and products, well outside the scope of "build the linter" — that's a separate human decision, tracked as `identified_gaps.md` GAP-004 rather than either silently ignored or unilaterally executed. The three tables this session's own `E6` edits touched (`execution_plan.md`'s Open Decisions Log, `E4` phase table, Decision & Sign-Off Record) were re-canonicalized as part of making those specific edits, since that's normal write-tool hygiene, not a workspace sweep.

### E6-T2 — Multi-Workspace Support

Resolves `OD-4`'s deferral (`execution_plan.md` Sec 6): `aosdf-vscode` now manages every open workspace folder, not just `folders[0]`. The three `aosdf.*` settings are now `"scope": "resource"` (`package.json`), so a multi-root workspace can point each folder at a different `{project_name}-Documents/docs`. One `McpClient` per folder (`Map` keyed by `folder.uri.toString()` in `extension.js`), restarted individually on that folder's own config change or removal (`onDidChangeConfiguration`'s per-resource `affectsConfiguration(section, uri)` check; `onDidChangeWorkspaceFolders`). The status bar chip stays a single item — it shows whichever folder contains the active editor's document (falling back to the first folder), prefixed `[folderName]` only when more than one folder is open. `InboxProvider` (`inboxProvider.js`) iterates every folder and prefixes each folder's three sections the same way — still a flat list, not a new tree level, consistent with `E4-T1`'s original design. Every write action (`E5-T1`) now takes a `folder` argument end to end: `terminalRunner.js` names/`cwd`s a terminal per folder (`AOSDF: <folderName>`) instead of the single fixed `AOSDF` terminal, and `runAgentCommand`/`triggerTrackerSync` prompt with a folder-picking `QuickPick` first; `approvePromptItem` already knows its folder from the Inbox item that triggered it (`item.aosdfFolder`, stamped by `InboxProvider`).

**With exactly one workspace folder open — the common case — every one of these reduces to `E4`/`E5`'s original behavior exactly:** no `[folderName]` prefix anywhere, no folder-picker prompt, the one plain `AOSDF` terminal with no explicit `cwd`. Verified with a hand-rolled `vscode` API stub (this environment can't launch a real Extension Development Host) exercising both the single- and two-folder paths end to end — confirmed terminal naming/`cwd`, Inbox prefixing, and folder-scoped dispatch all behave as designed, and confirmed the single-folder path is byte-for-byte unchanged.

### E6-T3 — Internal Packaging

`OD-1` resolved internal-only, so this is `.vsix` packaging, never a Marketplace submission — no `vsce publish` step, no publisher-account signup. `aosdf-vscode/package.json` gained a `package` script (`npx --yes @vscode/vsce package --allow-missing-repository --no-dependencies -o aosdf-vscode.vsix`) — `@vscode/vsce` is fetched on demand via `npx`, never added as a project dependency, so the zero-runtime-dependency discipline (Principle 30) this extension otherwise holds to is unaffected; nothing about running or testing the extension requires an `npm install` to pull in anything. `--allow-missing-repository` is passed because `aosdf-vscode` isn't a standalone repo (`OD-3`: bundled inside `AOSDF/`), so a `repository` field would be fictitious. Verified end to end this session: `npm run package` produces a working 11-file, ~14KB `.vsix` containing exactly the runtime `src/*.js` files plus `package.json`/`readme.md` (`.vscodeignore` already excluded `test/**`). The output is gitignored (`aosdf-vscode/.gitignore`) — a regenerable build artifact, not source, the same treatment Track D's `AOSDF-site/` got before its cancellation.

### Known Scope Limits

- The linter checks Rules 1–2 only; Rules 3–4 remain unaudited by tooling (see E6-T1 above).
- Multi-workspace's "active folder" heuristic (whichever folder owns the active editor) has no meaning with zero open editors — it falls back to the first folder, same as the original single-workspace assumption.
- The `.vsix` was verified to package and install-list correctly; it was not verified to *run* correctly once installed from a `.vsix` inside a real Extension Development Host, since this environment can't launch VS Code's GUI — human verification (opening `aosdf-vscode.vsix` via "Install from VSIX...") is the recommended final check before relying on it.

---

## [v2.5, restructured 2026-08-19] MkDocs-Based Project Docs Site

### What This Is

Track P (Project Docs Site) renders a product's own `{project_name}-Documents/` — execution plan, milestones, every `03_System_Design/NNN_<name>_module/`, ADRs — for every project stakeholder, not just the developer who built it. That's a different problem from Track L's curated, derived dataset (above), so it doesn't share Track L's hand-rolled renderer: it uses **[MkDocs](https://www.mkdocs.org/) with the Material theme**, configured via `mkdocs.yml`, not custom JavaScript.

An earlier draft (Track D) pointed this same tooling at `AOSDF/` itself, to give the framework a browsable front door. It was built and worked, then cancelled: `AOSDF/` is the product this framework produces — the analogue of `{project_name}/` (application code) in any product built with AOSDF, not of `{project_name}-Documents/`. No AOSDF-adopting product renders its own application code as a website, so AOSDF didn't need one either. See `evolution.md` Sec 13's cut note and `execution_plan.md`'s D0 entry.

### Why It Fits With Near-Zero Rework

- AOSDF's markdown is already standard: headings, GFM pipe tables (the Document Formatting Standard is a superset, not a conflicting convention), and folder names already numerically prefixed (`00_…` through `16_…`), which MkDocs' nav ordering picks up with zero configuration.
- The `aosdf-diagram` fence (§ Concept Frontmatter Standard, `aosdf-diagram` convention) needs no custom plugin — any fenced-code renderer, including MkDocs' default Python-Markdown `fenced_code` extension, already tags that block `language-aosdf-diagram` in its output HTML class. `AOSDF/templates/project_docs_site/docs_overrides/aosdf.css` (below) is the few lines of CSS that turn it into a distinct monospace panel — copied verbatim, not re-authored per project.
- Nav, search, and table-of-contents generation are the tool's job, not AOSDF's — "generic by construction, no hardcoded file list" is a property of `mkdocs.yml`'s config, not hand-written JS.
- The one piece of hand-written JS this site does ship, `docs_overrides/aosdf.js` (below), is additive to the tool's own nav/TOC/search — it doesn't replace or duplicate any of it.

### Richer Diagrams: Archify (optional, `R3`/`OD-H11`)

The `aosdf-diagram` fence (plain box-drawing text) stays the default for every diagram — zero tooling,
zero setup, opens as plain text if all else fails. For a real architecture/workflow/sequence/dataflow/
lifecycle diagram where that's not enough, [Archify](https://github.com/tt-a1i/archify) (MIT) is the
recommended alternative for **Project Docs Site pages only** — never Track L's `render/index.html`
(see below for why). An agent authors a small typed JSON spec, Archify's CLI validates it and
compiles it into one self-contained interactive HTML file (pan/zoom, search, theme toggle, PNG/SVG/
WebM export), which is committed under the module's `diagrams/` subfolder and linked from the relevant
markdown page — it is never generated as part of `mkdocs build` itself, so it adds nothing to that
build's dependency surface. See `007_hosting_pipeline_module/03_architecture.md` for a real, delivered
example (`hosting-pipeline.architecture.json`/`.html`) and `execution_plan.md`'s `R3` phase for the
pilot record.

**Why not Track L:** a generated Archify diagram links to Google Fonts — confirmed by inspecting a
delivered artifact directly, not assumed from its docs — which breaks the offline-first, zero-external-
call guarantee `render/index.html` holds itself to (Principle 30). Track L's diagram panel stays
`aosdf-diagram`-only; this was a deliberate simplification (`OD-H11`), not an oversight.

### One Site, Nested Inside `{project_name}-Documents/`

```
{project_name}-Documents/
├── mkdocs.yml                       → docs_dir: docs, site_dir: {project_name}-Documents-site
├── .venv/                           → mkdocs + mkdocs-material, project-local, gitignored
├── {project_name}-Documents-site/   → build output, gitignored, sibling of docs/
└── docs/                            → docs_dir — every renderable file lives under here:
    ├── CLAUDE.md, project_status.md, identified_gaps.md, reference/
    ├── docs_overrides/aosdf.css, aosdf.js   → PJ1-T1 default theme, see below
    └── documents/00_Project_Context/ … 16_Learning_Roadmap/
```

`docs_dir: docs` is MkDocs' own idiomatic default, not an AOSDF invention — narrowing `docs_dir` to a subfolder (rather than the whole project root) is what lets both the config file and the built site live legally inside `{project_name}-Documents/`: MkDocs only forbids `docs_dir` from being the *parent of the config file*, and forbids `site_dir` from being *inside* `docs_dir`. Neither restriction applies once `docs_dir` is a subfolder — `mkdocs.yml`'s own parent isn't `docs_dir`, and `{project_name}-Documents-site/` sits beside `docs/`, not inside it. `docs_overrides/` must live *inside* `docs_dir` for the same reason `extra_css`/`extra_javascript` paths resolve correctly — MkDocs resolves both relative to `docs_dir`, not the repo root (a real bug caught in `AOSDF-Hosting` — see `execution_plan.md`, 2026-09-12 — from a project whose `docs_overrides/` sat at the repo root instead).

`docs_site_agent` (`AOSDF/agents/docs_site_agent.md`) is the thin, human-triggered wrapper that runs `mkdocs build` against `{project_name}-Documents/mkdocs.yml` on a `Project Docs:` command, or opens the already-built static output — it never authors or edits `mkdocs.yml` itself (that's `frontend_agent`'s one-time setup task, PJ1-T1, below).

### Setup Procedure (PJ1-T1)

The one-time task that actually creates this site, owned by `frontend_agent`, run once Track P is reached (per the `Enabled`/`Disabled` flag `workflow_initiator` recorded at Q11 — that question only records the flag, it does not scaffold anything itself):

1. Copy `AOSDF/templates/project_docs_site/mkdocs.yml.template` to `{project_name}-Documents/mkdocs.yml`, replacing every `{project_name}` placeholder.
2. Copy `AOSDF/templates/project_docs_site/docs_overrides/` (both `aosdf.css` and `aosdf.js`) to `{project_name}-Documents/docs/docs_overrides/` verbatim — this is the default theme every project starts from: a distinct panel for `aosdf-diagram` blocks, collapsible left-nav and right-TOC sidebars, and a back-to-home link in the header. Customize further from here if a project needs it; don't start from scratch.
3. Create the project-local `.venv/` and install `mkdocs`/`mkdocs-material` into it (gitignored, per-project — never a framework-level dependency).
4. Confirm `mkdocs build` runs clean before marking `PJ1-T1` `Done` in `execution_plan.md`.

This is a reviewed, one-time setup task, same as every other `PJ1-T1`-class task — later hand customization of `mkdocs.yml` or `docs_overrides/` is expected and fine; this procedure only fixes the *starting point* so every project's docs site begins from the same baseline instead of being re-invented per project.

### Command Surface

```
Project Docs: build      → docs_site_agent runs `mkdocs build` against {project_name}-Documents/mkdocs.yml
Project Docs: open       → docs_site_agent opens {project_name}-Documents/{project_name}-Documents-site/index.html
```

Same human-triggered pattern as `Wiki:`, `Tracker:`/`Jira:`, and `Learn:` (Principle 24) — no agent rebuilds this site on its own initiative. There is no `Docs:` verb — Track D is cancelled, so `Project Docs:` is the only site-build command surface this framework has.

### Sensitivity Profile

`{project_name}-Documents/` is a specific company's real product documentation — the site stays local-only by default, same spirit as Track L (Principle 30), no default publishing path. MkDocs makes this an explicit, deliberate step either way (`mkdocs build` alone is fully local; `mkdocs gh-deploy` is an extra step) rather than something the tooling defaults into.

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

## [v2.5] Tracker Board Integration

**[v2.5]** Generalizes the v2.4 Jira-only integration to Jira *or* Notion, per Principle 25. A v2.4
project with an existing `jira_config.md` is unaffected — see **Migrating from v2.4 Jira-Only Sync**
below.

### What This Is

An **optional** mirror of a project's AOSDF state onto a tracker board (Jira or Notion), via MCP tool
calls. It exists so that people who work from a tracker (PMs, admins, stakeholders who never open
`execution_plan.md`) can see milestone and task progress without learning AOSDF's file layout, and so
they have a normal tracker entry point for requesting new work. It changes **nothing** about how AOSDF
itself plans or executes work — `execution_plan.md`'s Status column remains the only task-status record
(Principle 22), full stop. The tracker is a read-and-occasionally-write mirror of that record, never a
replacement for it, and never more than one provider at a time (Principle 25).

Full field-level mapping, the `TrackerAdapter` interface, and the `tracker_config.md` schema live in
`AOSDF/reference/tracker_mapping.md` — required reading before running `tracker_sync_agent` for the
first time on a project. Provider-specific setup requirements live in `AOSDF/reference/jira_mapping.md`
(Jira) and `AOSDF/reference/notion_mapping.md` (Notion). This section only covers the integration points
into the core framework.

### Opt-in Is a One-Time Setup Decision

`workflow_initiator` asks whether to enable tracker sync **once**, during initial project setup (Step 1,
Q8), including which provider — never silently enabled later, and never asked again mid-project without
a human deliberately revisiting the decision. If enabled:
- `workflow_initiator` creates `{project_name}-Documents/tracker_config.md` (`Provider: jira | notion`,
  provider-specific settings, issue-type mapping overrides if any, and the human's chosen sync-cadence
  recommendation from `tracker_mapping.md`), and — in the same step, since the credential is collected
  at the same time as the provider choice — a sibling `tracker_config.env` holding the actual API
  token(s). Neither the token nor the choice of Jira vs. Notion is defaulted: Provider has no suggested
  option (the human must pick), and the credential is never written into `tracker_config.md` itself
  (OD-2/OD-5, resolved 2026-08-27 — see `tracker_mapping.md` §2a).
- If declined (the default), no tracker-related file is created and `tracker_sync_agent` is never
  invoked — the project runs exactly as it did pre-v2.4.

### The Mapping (Summary — full detail in `tracker_mapping.md`)

| AOSDF Unit | Jira Issue Type | Notion Equivalent | Notes |
|---|---|---|---|
| `03_System_Design/NNN_<name>_module/` (a Module) | **Feature** *(optional)* | A "Modules" database, one page per module | Groups the milestones that implement this module. Skipped entirely on a Jira project with no Feature type — Milestones then have no parent. |
| Milestone (`M{n}_<Name>`) | **Epic** | A page in a "Milestones" database, related to its Module page | Matches AOSDF's own definition — "each milestone = a working, testable system slice." |
| Task (`M{n}-T{seq}` or `ADD-<slug>-T{seq}`) | **Story** (FRD-mapped, user/system-facing) or **Task** (infra/ops/non-functional) | A page in a "Tasks" database, related to its Milestone page, with a `Type` select property | The Owner column and the Notes/FRD citation decide which. |
| Subtask (a row within a Task) | **Sub-task** | Notion sub-items (or a checklist block) under the Task page | Native to each provider. |
| `execution_plan.md` Status (`Planned` / `In Progress` / `Done` / `Cancelled`) | Jira workflow status (`To Do` / `In Progress` / `Done` / `Cancelled`) | Notion `Status` select property, same four values | 1:1, no reinterpretation, and never many-to-one collapsing. |

### Sync Is Always Human-Triggered

No agent calls a tracker MCP tool on its own initiative — ever. A human runs:

```
Tracker: sync
```

(`Jira: sync` / `Notion: sync` remain accepted aliases, so v2.4 muscle memory and docs don't break)
exactly mirroring the existing `Wiki: re-ingest` / `Wiki: full-sync` command pattern (§ LLM Wiki
Integration above). This command invokes `tracker_sync_agent` in **Export Mode**, dispatched to the
provider named in `tracker_config.md`'s `Provider:` field (reads `execution_plan.md`, milestone files,
`identified_gaps.md`, `12_Manual_Actions/actions.md`, and `15_Addendums/tracking_addendums.md`;
creates/updates the corresponding tracker items; records the Task-ID↔tracker-item mapping in
`06_Execution_Plan/tracker_issue_map.md`). See `tracker_mapping.md` for the recommended cadence at
which a human should run this command — AOSDF does not enforce a cadence, only recommends one, because
enforcing it would require an agent to act unprompted, which Principle 24 forbids.

### The Reverse Direction — Admin-Initiated Work

Administrators are not limited to reading the mirror — they can originate new work directly in the
tracker (a new Epic/Story, or Notion Milestone/Task page, for a feature request). That does **not**
automatically become AOSDF work. A human runs:

```
Tracker: import <ref>
```

which invokes `tracker_sync_agent` in **Import Mode**: it drafts a `15_Addendums/<slug>.md` addendum
document from the tracker item's title/description/acceptance criteria, for a human to review and
refine. `tracker_sync_agent` never calls `addendum_agent` itself and never touches `execution_plan.md`
or any milestone file — the human runs `addendum_agent` afterward, exactly as the existing post-baseline
change process (Principle 21) already requires. This keeps tracker-originated work subject to the same
traceability discipline as everything else in AOSDF, instead of creating a side channel that bypasses it.

### Wiki Sync Trigger Table Addition

| Agent Action | Files Changed | Command |
|---|---|---|
| `tracker_sync_agent` Export Mode run | `06_Execution_Plan/tracker_issue_map.md` (created/updated); tracker items (external) | Human already ran `Tracker: sync` to trigger this — no further wiki action needed unless the human also wants `llm-wiki/` to note the sync happened |
| `tracker_sync_agent` Import Mode run | `15_Addendums/<slug>.md` (drafted) | None yet — run `addendum_agent` next, which triggers its own normal wiki-sync guidance |

### Migrating from v2.4 Jira-Only Sync

A project with an existing `jira_config.md` keeps working completely unchanged — `jira_sync_agent` is
untouched and still runs on `Jira: sync` / `Jira: import <key>`. To move to the generalized agent (not
required):
1. `jira_config.md` is read as `Provider: jira` and its contents copied forward into a new
   `tracker_config.md` — no data is re-entered.
2. `tracker_sync_agent` takes over `Tracker: sync` / `Tracker: import` (and the `Jira: sync` /
   `Jira: import` aliases) from that point forward.
3. `jira_config.md` and `jira_sync_agent.md` may be left in place or removed once the team is confident
   in the new file — AOSDF never deletes either automatically.

---

## Critical Rules

**No code without:** API contract + schema definition + security review (02 complete)

**No agent freedom:** Agents follow prompts exactly. Blocked tasks escalated, not improvised.

**Everything must be:** Versioned | Testable | Traceable

**[v1.1]** Gaps logged to `identified_gaps.md` immediately. **[v1.7]** Manual steps logged to `12_Manual_Actions/actions.md` immediately (not the legacy `manual_action.md`).

**[v1.2]** `project_status.md` = READY before execution. Implementation prompts saved before running. M0 complete before M1.

**[v1.4]** All agent-generated files with tables must follow the Document Formatting Standard. Separator dashes match column width. Data cells padded. Consistent widths across files.

**[v1.8]** `git push` is a human-only action. Agents NEVER push to remote branches — not feature, not staging, not main. An agent may `git add`, `git commit`, and show the diff, but must stop there and wait for explicit human instruction to push.
