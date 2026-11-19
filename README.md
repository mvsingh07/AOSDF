# AI Development Model — AOSDF


# AI-Orchestrated Software Development Framework

> **Current Version:** v3.6.0
> **Plain-language guide:** [manual.md](manual.md)
> **Full specification:** [framework.md](framework.md)

---


## Coordinated development (3.4 / 3.5)

Read [current workflow rules](reference/current-workflow-rules.md) for C1–C13. The Solution Architect owns ongoing canonical execution-plan writes after Captain creation/replanning; Principal Engineers coordinate threads; workers and validators report evidence. Strategy B task design/review roles are distinct from these coordination roles. Exactly four process Modes: Manual → Semi-auto → Easy → Auto; transitions are explicit and rollout stages are separate.

Use proportional Small/Standard/High-risk plans and initial verdicts; High-risk workers stop for independent review. Additional review or plan revision requires founder approval. Reconcile accepted receipts once and preserve live ownership/history. Coordinated Strategy B enters `05_AI_Agent_System/coordination-threads/coordinator-definition.md`; Strategy A is explicit legacy compatibility.

New setup records coordination opt-in and project-owned topology/model/ownership inputs, installs `templates/coordination_threads/` inactive and creates empty records only after those inputs are known. Root `reference/` policies install into project `06_Execution_Plan/`; roles into `05_AI_Agent_System/agents/`; prompts into `05_AI_Agent_System/prompt_templates/`. Rewrite source-relative links to these installed paths. Never copy foreign live state or enable a daemon/session from a template. See [portable upgrade protocol](reference/upgrades.md) for independent existing-project migration.

File notifications are notification-only, bounded and target-configured; observer and receiver are separate. An ended conversation is not woken without an attached receive call. Events do not grant authorization or task acceptance. See `templates/coordination_threads/file-signals/README.md`.

Documentation itself is the knowledge source; self-indexing and existing learning/docs tooling remain. No separate llm-wiki folder is required. See [indexable authoring standard](reference/document_authoring.md) for the required new-document metadata, creation helper and validation gate.


## Public framework and managed service

AOSDF provides the **foundations of an AI-orchestrated software factory**: specification-driven planning, coordinated agents and evidence-based validation. Fully autonomous specification-to-release delivery is a future operational milestone, not a current guarantee.

This repository includes the framework, reusable coordination code, MCP/VS Code integrations, documentation tooling, learning material and the [public website](website/README.md). The managed hosting application and live project records remain in separate private repositories. See [repository boundaries](docs/repository-boundaries.md), the [project and resume summary](docs/project-summary.md), and the [synthetic coordination walkthrough](examples/coordinated-development/README.md).

Start a project with [the setup guide](prompts/setup_aosdf.md). Build the website with `cd website && npm ci && npm run build`. Coordination automation ships inactive; a clone does not activate agents or authorize execution.

## What This Is

AOSDF is a structured framework for building software with AI agents. It turns a product idea into a working system through a defined sequence of documents, agents, and checkpoints — with minimal human intervention after the planning phase is locked.

It solves the core failure mode of AI-assisted development: agents that make up architecture, skip security, build features before the data model exists, and produce output with no traceability.

---

## Files in This Folder

| File | Purpose |
| ----------------------------------------------- | ----------------------------------------------------------------------- |
| [framework.md](framework.md)                    | Full AOSDF specification — principles, folder structure, agent architecture, versioned changelog |
| [manual.md](manual.md)                          | Plain-language explanation of how the framework works and how to use it |
| [setup_aosdf.md](prompts/setup_aosdf.md)                | **Start here for a new project** — step-by-step setup guide + ready-to-use setup prompt |
| [workflow_initiator.md](workflow_initiator.md)  | Entry-point agent — asks setup questions, checks folder structure, identifies missing documents |
| [templates.md](templates.md)                    | Document templates for all 00–05 sections |
| [agents/](agents/)                              | **All agent definitions** — copy to your project's `05_AI_Agent_System/agents/` and customize |
| [reference/](reference/)                        | Quick-reference documents for Claude and humans — read before starting a new project |
| [designing_aosfd/](designing_aosfd/)            | Design prompts used to build and evolve this framework |

### agents/ — General Template Library

| Agent File | Role |
| -------------------------------------------------------------------- | ------------------------------------------------------------------ |
| [agents/identify_missing_documents.md](agents/identify_missing_documents.md) | Scans project structure against AOSDF checklist, reports gaps |
| [agents/captain_agent.md](agents/captain_agent.md)                           | Reads 00–05 docs, generates execution plan + milestones, validates FRD coverage |
| [agents/research_and_refine_agent.md](agents/research_and_refine_agent.md)   | Task-driven research — reads `task.md`, outputs `research_results.md` |
| [agents/research_and_review_agent.md](agents/research_and_review_agent.md)   | Pre-architecture research — comparable systems |
| [agents/architect_agent.md](agents/architect_agent.md)                       | System design, ADRs, service boundary validation |
| [agents/backend_agent.md](agents/backend_agent.md)                           | Server-side implementation, DB migrations, tests |
| [agents/infra_agent.md](agents/infra_agent.md)                               | Infrastructure provisioning via IaC |
| [agents/qa_agent.md](agents/qa_agent.md)                                     | Testing strategy — unit, integration, load, security |
| [agents/frontend_agent.md](agents/frontend_agent.md)                         | UI implementation (inactive if `has_ui: false`) |
| [agents/commander_agent.md](agents/commander_agent.md)                       | Session orchestrator — reads state, delegates tasks |
| [agents/execution_agent.md](agents/execution_agent.md)                       | Strategy A implementor — prompt → execute → validate → done |
| [agents/reviewer_agent.md](agents/reviewer_agent.md)                         | Strategy B gate — reviews prompt for security + scale violations |
| [agents/validator_agent.md](agents/validator_agent.md)                       | Strategy B final gate — runs tests, reports completion to SA |
| [agents/addendum_agent.md](agents/addendum_agent.md)                         | Post-baseline change planning within `15_Addendums/` |

---

## How a Project Uses This

```
1. Human fills 00–05 docs  →  product, architecture, security defined
2. captain_agent runs      →  execution plan + milestones generated
3. Agents execute M0–M3   →  code built, tested, deployed
4. Human approves at each milestone boundary
```

The `designing_aosfd/` folder contains the original design prompts that shaped how this framework was built — useful for understanding why decisions were made.

---

## License & Third-Party Notices

AOSDF is [MIT licensed](LICENSE). It integrates with two open-source projects for Project Docs Sites — [MkDocs](https://www.mkdocs.org/) (BSD-2-Clause) with the [Material](https://squidfunk.github.io/mkdocs-material/) theme (MIT), and optionally [Archify](https://github.com/tt-a1i/archify) (MIT) for richer diagrams. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for full credits.

---

## Versioned Changes

| Version | What Changed |
| ------- | --------------------------------------------------------------------------- |
| v3.5.0 | Inactive project-configured file notifications; separate receiver, cursors, deadlines and 14 fixture checks. |
| v3.4.0 | C1–C13 coordination, SA/Principal Engineer, four Modes, proportional review and inactive reusable automation. |
| v1.1    | Research-before-design pass, gap tracking, manual action tracking, multi-agent strategy |
| v1.2    | Execution-ready gate (`project_status.md`), commander→execution delegation, implementation prompts as artifacts |
| v1.3    | `captain_agent` — bridges planning docs to executable milestones, FRD coverage validation |
| v1.4    | `research_and_refine_agent` — task-driven research agent; global Document Formatting Standard for all agent-generated tables |
| v1.5    | Workspace layout — AOSDF as separate reusable directory; `.gitignore` at workspace root |
| v1.6    | LLM Wiki as persistent context layer (`llm-wiki/` fourth directory) |
| v1.7    | `12_Manual_Actions/` two-file system — `actions.md` tracker + `guides.md` instructions |
| v1.8    | Session context management rules — compact cadence, context window gate, one task per cycle |
| v1.9    | `13_Legal_Requirements/` optional section — legal constraints as binding execution plan tasks |
| v2.0    | `14_Future_Migrations/` — portability-first principle, infrastructure abstraction interfaces |
| v2.1    | `15_Addendums/` — post-baseline change management via `addendum_agent` |
| v2.2    | `AOSDF/agents/` general template library — 11 reusable agent files; `setup_aosdf.md` setup guide |

---

## Quick Reference — Agent Call Order

```
[Setup — one time]
workflow_initiator   →  checks structure, identifies gaps, creates initial files

[Pre-execution — one time]
research_and_review  →  optional; research comparable systems before architecture locks
research_and_refine  →  optional; call when a scoped research question needs answering
captain_agent        →  after 00–05 complete; generates execution plan + milestones

[Execution — per session]
commander_agent      →  session entry point during execution; delegates tasks
execution_agent      →  Strategy A: implements one subtask at a time
reviewer_agent       →  Strategy B: reviews implementation prompt before coding starts
validator_agent      →  Strategy B: verifies implementation output against acceptance criteria

[Post-baseline — on demand]
addendum_agent       →  when a cross-cutting requirement arrives after plan is locked
```

For invocation details, examples, and the new project setup guide, see [setup_aosdf.md](prompts/setup_aosdf.md) and [manual.md](manual.md).

---

## Author

**Manvir Singh** ([mvsingh07](https://www.linkedin.com/in/mvsingh07)) — [www.mvsingh.in](https://www.mvsingh.in)

## Framework updates

Use the portable [upgrade guide](upgrades/README.md) and [existing-project migration recipe](upgrades/releases/3.6.0/migrate.md). Product discoveries become generic public releases; private project application receipts stay with their owning projects. The canonical source is this repository, not an older project-local AOSDF copy.
