# Folder Map
# AOSDF v2.5 — Quick Reference
# Canonical workspace layout. Every project using AOSDF follows this structure.

---

## Workspace Layout

```
{ProjectName}-Orchestrum/                          ← WORKSPACE ROOT (not a git repo itself)
│
├── .gitignore                                     ← excludes AOSDF/ and {ProjectName}-Documents/
│
├── AOSDF/                                         ← General AI Development Model (shared, not project-specific).
│   │                                                 No mkdocs.yml or site of its own — AOSDF/ is the product this
│   │                                                 framework produces, the analogue of {ProjectName}/ (application
│   │                                                 code) below, not of {ProjectName}-Documents/. A matching docs
│   │                                                 site for AOSDF/ itself (Track D) was built, then cancelled
│   │                                                 2026-08-19 — see execution_plan.md's D0 entry.
│   ├── framework.md                               Full specification
│   ├── manual.md                                  Plain-language guide
│   ├── setup_aosdf.md                             New project setup + upgrade guide
│   ├── workflow_initiator.md                      Entry-point agent
│   ├── templates.md                               Document templates (00–05)
│   ├── templates/
│   │   ├── reference_readme.md
│   │   └── module_template/                       [v2.3] Canonical NNN_<name>_module/ skeleton
│   │                                              → cloned into 03_System_Design/_template/ at project setup
│   ├── agents/                                    All agent definitions (general templates)
│   │   ├── identify_missing_documents.md          Structure auditor
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
│   │   ├── jira_sync_agent.md                     [v2.4] OPTIONAL — pre-v2.5 projects, superseded
│   │   ├── tracker_sync_agent.md                  [v2.5] OPTIONAL — human-invoked only, Jira or Notion
│   │   ├── concept_indexer_agent.md               [v2.5] OPTIONAL — human-invoked only, Learn: commands
│   │   └── docs_site_agent.md                     [v2.5, restructured 2026-08-19] OPTIONAL — human-invoked,
│   │                                                Project Docs: build/open only (no Docs: verb — Track D is cut)
│   ├── reference/                                 Quick-reference docs (YOU ARE HERE)
│   │   ├── agent_index.md                         Agent roles, call order, permissions
│   │   ├── folder_map.md                          This file
│   │   ├── formatting_standard.md                 Table formatting rules
│   │   ├── rules.md                                Non-negotiable framework rules
│   │   ├── jira_mapping.md                        [v2.4] OPTIONAL — Jira-specific setup/field mapping
│   │   ├── notion_mapping.md                      [v2.5] OPTIONAL — Notion-specific setup/field mapping
│   │   └── tracker_mapping.md                     [v2.5] OPTIONAL — TrackerAdapter interface + config schema
│   ├── renderer_core/                             [v2.5 D0] Track L only — custom app renderer
│   │   ├── core.js                                markdown→HTML, diagram panel, tables, nav, search
│   │   └── core.css                                shared design tokens + styles, light/dark aware
│   ├── designing_aosfd/                           Framework design history
│   ├── aosdf-mcp/                                 [v2.5 E2-T1] Six read/write MCP tools over a project's markdown
│   │   │                                            state (Principle 26) — stdio JSON-RPC, zero dependencies.
│   │   │                                            Registered by `.mcp.json` below; also spoken to directly by
│   │   │                                            `aosdf-vscode/`'s status bar chip.
│   ├── aosdf-vscode/                              [v2.5 E4-T1/T2] Editor extension MVP (read-only), VSCode first.
│   │   │                                            Status bar chip + Gaps/Manual Actions inbox, both thin clients
│   │   │                                            of `aosdf-mcp/` or direct markdown reads — never a second
│   │   │                                            source of truth. Not copied into `{ProjectName}/` — not yet
│   │   │                                            packaged for the Marketplace (`E4-T3`/OD-1 open); run via F5
│   │   │                                            from here against a `{ProjectName}/` workspace in the interim.
│   ├── .claude/                                   [v2.5 E3-T1] Master template — Claude Code subagents/
│   │   │                                            commands/hooks. `workflow_initiator` Step 8 copies this
│   │   │                                            whole tree into `{ProjectName}/.claude/`, never left here
│   │   │                                            in place (it's the only real git repo — see below).
│   │   ├── agents/                                 One `<role>.md` per `AOSDF/agents/*.md` (+ workflow-initiator),
│   │   │                                            translating each `## Permissions` block into a `tools:` allowlist
│   │   ├── commands/                                /aosdf-init, -plan, -next, -addendum, -research, -sync, -import
│   │   ├── settings.json                            `permissions.deny` for `git push` (WRITE_REMOTE, technical
│   │   │                                            control not just documented rule) + the session-context hook
│   │   └── hooks/session-context-gate.js            [E3-T2] Principle 27 — PreToolUse gate on Task/Agent
│   └── .mcp.json                                  [v2.5 E3-T1] Master template — registers `aosdf-mcp` (E2-T1) as
│                                                     an MCP server. Also copied to `{ProjectName}/`, not left here;
│                                                     paths inside are already written relative to that destination.
│
├── {ProjectName}/                                 ← Application Code only (git repo — the ONLY git repo in this
│   │                                                 workspace; see `.claude/`/`.mcp.json` note above)
│   ├── .claude/                                   [v2.5 E3-T1] Copied from `AOSDF/.claude/` at setup (Step 8) —
│   │   │                                            this is what actually ships to every teammate's `git clone`
│   │   ├── agents/
│   │   ├── commands/
│   │   ├── settings.json
│   │   └── hooks/session-context-gate.js
│   ├── .mcp.json                                  [v2.5 E3-T1] Copied from `AOSDF/.mcp.json` at setup (Step 8)
│   ├── .vscode/settings.json                      [v2.5 E4-T1/T2] Written (not copied) at setup (Step 8) —
│   │                                                points `aosdf-vscode/` at this workspace's docs root, MCP
│   │                                                server, and Project Docs Site
│   └── [backend/, frontend/, etc.]
│
└── {ProjectName}-Documents/                       ← Project Documentation (gitignored). The ONE project docs
    │                                                 folder — everything Track P needs, including its own built
    │                                                 site, lives inside it. Nothing else in the workspace holds
    │                                                 project-docs-site state.
    ├── mkdocs.yml                                  ← [v2.5 PJ1, restructured 2026-08-19] Project Docs Site config.
    │                                                  docs_dir: docs (a subfolder, not this folder's root) — that's
    │                                                  what lets both this file and the built site live here: MkDocs
    │                                                  forbids docs_dir from being the config file's own parent, and
    │                                                  forbids site_dir from nesting inside docs_dir. Neither rule
    │                                                  is triggered once docs_dir is a subfolder.
    ├── .venv/                                      ← [v2.5 PJ1] mkdocs + mkdocs-material, project-local, gitignored
    ├── {ProjectName}-Documents-site/                ← [v2.5 PJ1, restructured 2026-08-19] mkdocs build output,
    │                                                   gitignored, sibling of docs/ below (nested inside this
    │                                                   folder, not a workspace-root sibling). Regenerated on the
    │                                                   human-triggered `Project Docs: build` command — never
    │                                                   hand-edited, never a second source of truth (Principle 26).
    │                                                   Safe to delete any time; the next build recreates it.
    │                                                   Skip Track P entirely if a project docs site isn't wanted;
    │                                                   nothing else depends on this folder existing.
    └── docs/                                       ← [v2.5 PJ1, restructured 2026-08-19] docs_dir — every
        │                                              renderable file lives here
        ├── CLAUDE.md                              ← AI agent context (entry point — READ FIRST)
        ├── project_status.md                      ← Execution readiness gate
        ├── identified_gaps.md                     ← All identified gaps
        ├── research_results.md                    ← Output from research_and_refine_agent
        ├── jira_config.md                          ← [v2.4] OPTIONAL, pre-v2.5 — presence = Jira sync enabled
        ├── tracker_config.md                       ← [v2.5] OPTIONAL — presence = tracker sync enabled
        ├── tracker_config.env                      ← [v2.5] OPTIONAL, gitignored — credential-only (OD-2, resolved 2026-08-27)
        ├── docs_overrides/                         ← [v2.5 PJ1, populated 2026-09-12] aosdf.css (aosdf-diagram panel) + aosdf.js (collapsible nav/TOC, home link) — copied from AOSDF/templates/project_docs_site/ at PJ1-T1
        ├── reference/                              ← [v2.2] Raw product knowledge inputs
        │   ├── README.md                           ← Index of what's in this folder
        │   └── [human-provided raw docs]           ← briefs, research, vendor docs, stakeholder notes
        └── documents/
            ├── 00_Project_Context/
            │   └── project_context.md
            ├── 01_Project_Definition/
            │   ├── PRD.md
            │   ├── FRD.md
            │   └── BRD.md
            ├── 02_Security_Framework/
            │   ├── security_requirements.md
            │   ├── threat_model.md
            │   └── compliance_checklist.md
            ├── 03_System_Design/                   ← [v2.3] cross-cutting design + per-module design
            │   ├── README.md                       ← module index (number, name, status, milestone)
            │   ├── _template/                      ← skeleton cloned for every new module
            │   ├── system_architecture.md          ← cross-cutting
            │   ├── service_design.md
            │   ├── data_flow.md
            │   ├── ADR/                            ← cross-cutting ADRs
            │   ├── 001_<name>_module/              ← one folder per core module
            │   │   ├── README.md
            │   │   ├── 00_overview.md
            │   │   ├── 01_requirements.md
            │   │   ├── 02_domain_model.md
            │   │   ├── 03_architecture.md
            │   │   ├── 04_data_model.md
            │   │   ├── 05_interfaces.md
            │   │   ├── 06_operations.md
            │   │   ├── decisions/                  ← module-scoped ADRs
            │   │   ├── diagrams/                    [2026-09-12] OPTIONAL — archify .json/.html pair, only when the aosdf-diagram fence alone doesn't carry it (see framework.md → "Richer Diagrams: Archify")
            │   │   └── _archive/                   ← prior-art docs (where they exist)
            │   └── 002_<name>_module/
            │       └── …
            ├── 04_Infrastructure_Design/
            │   ├── infra_architecture.md
            │   ├── scaling_strategy.md
            │   ├── cost_estimation.md
            │   └── observability.md
            ├── 05_AI_Agent_System/
            │   ├── agents/                            ← Project-specific copies of AOSDF/agents/
            │   ├── prompt_templates/
            │   │   ├── task_prompt.md
            │   │   ├── review_prompt.md
            │   │   └── debug_prompt.md
            │   └── implementation_prompts/            ← Generated per task before execution
            ├── 06_Execution_Plan/
            │   ├── execution_plan.md                  ← [v2.2] Status source of truth — Status column is canonical
            │   │                                          Planned/In Progress/Done. Generated by captain_agent
            │   ├── jira_issue_map.md                  ← [v2.4] OPTIONAL, pre-v2.5 — Task ID ↔ Jira Key ↔
            │   │                                          Last Synced, written only by jira_sync_agent
            │   └── tracker_issue_map.md               ← [v2.5] OPTIONAL — Task ID ↔ tracker item ↔ Last
            │                                              Synced, written only by tracker_sync_agent
            ├── 07_Milestones/
            │   ├── M0_Project_Setup/
            │   │   └── milestone.md
            │   ├── M1_Foundation/
            │   │   └── milestone.md
            │   ├── M2_Core_Features/
            │   │   └── milestone.md
            │   └── M3_Hardening/
            │       └── milestone.md
            ├── 08_Tracking_System/
            │   └── decisions_log.md                   ← [v2.2] Lightweight decisions log only — NOT a task board.
            │                                              There is no tracking_board.md in AOSDF v2.2+.
            │                                              execution_plan.md's Status column is the only task-status
            │                                              record. Created by captain_agent if absent
            ├── 09_Testing_Validation/
            │   ├── test_plan.md
            │   ├── test_cases.md
            │   └── load_test_plan.md
            ├── 10_Deployment_Runbook/
            │   ├── deployment.md
            │   ├── rollback.md
            │   └── incident_response.md
            ├── 11_Future_Extensibility/
            │   └── future_scope.md
            ├── 12_Manual_Actions/                     ← [v1.7] Two-file manual action system
            │   ├── actions.md                         ← Tracker: all human steps, per-env status
            │   └── guides.md                          ← Step-by-step instructions per action ID
            ├── 13_Legal_Requirements/                 ← [v1.9] OPTIONAL — legal obligations
            │   └── concern_<n>.md
            ├── 14_Future_Migrations/                  ← [v2.0] RECOMMENDED — portability guide
            │   ├── research.md                        (optional — human-authored raw research)
            │   └── alternatives.md                    ← Authoritative; required reading for captain_agent
            ├── 15_Addendums/                          ← [v2.1] OPTIONAL — post-baseline changes
            │   ├── <slug>.md                          (human-authored)
            │   ├── <slug>_plan.md                     (addendum_agent-generated)
            │   └── tracking_addendums.md              (addendum_agent-generated; append-only)
            └── 16_Learning_Roadmap/                   ← [v2.5] OPTIONAL — created only if explicitly requested;
                │                                          derived-only, no original content
                ├── roadmap_index.md                   (concept_indexer_agent-generated, on Learn: rebuild)
                ├── roadmap_graph.json                  [v2.5 L2] (concept_indexer_agent-generated node/edge graph)
                └── render/index.html                   [v2.5 L2/L3] (concept_indexer_agent-generated, self-contained Build Order + Learn Order viewer with localStorage review tracking; inlines AOSDF/renderer_core/)

llm-wiki/                                          ← [v1.6] Persistent LLM knowledge base
    ├── WIKI.md
    ├── index.md
    ├── overview.md
    ├── log.md
    ├── sessions/
    ├── sources/
    ├── entities/
    ├── concepts/
    └── analyses/
```

---

## Naming Conventions

| Component | Pattern | Example |
| --------- | ------- | ------- |
| Workspace root | `{ProjectName}-Orchestrum` | `Comms-Engine-Orchestrum` |
| Application code | `{ProjectName}` | `Comms-Engine` |
| Project documentation | `{ProjectName}-Documents` | `Comms-Engine-Documents` |
| Project docs site | `{ProjectName}-Documents-site` (nested inside `{ProjectName}-Documents/`) | `Comms-Engine-Documents-site` |
| AI Development Model | `AOSDF` | `AOSDF` (same for all projects) |
| Persistent wiki | `llm-wiki` | `llm-wiki` (same for all projects) |
| Milestone folders | `M{N}_{Name}` | `M1_Foundation` |
| Task IDs | `M{N}-T{N}` | `M1-T3` |
| Module folders | `{NNN}_{name}_module` | `007_payments_module` |
| Module IDs | `{NNN}` — permanent, never renumbered | `007` |
| Module ADR files | `ADR-{NNN}-{NNN}-{slug}.md` | `ADR-007-001-idempotent-capture.md` |
| ADR files | `ADR-{NNN}-{slug}.md` | `ADR-001-event-sourcing.md` |
| Addendum task IDs | `ADD-{slug}-T{N}` | `ADD-security-patch-T1` |
| Implementation prompts | `{TASK-ID}_{short-name}_prompt.md` | `M1-T3-rate-limiting_prompt.md` |

---

## .gitignore at Workspace Root

```gitignore
# AOSDF — AI Development Model (not project-specific, not committed)
AOSDF/

# Project documentation — planning docs, agent definitions, gap trackers, never committed
{ProjectName}-Documents/
```
