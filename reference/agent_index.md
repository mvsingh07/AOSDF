# Agent Index
# AOSDF v3.2 — Quick Reference
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

[ON DEMAND — Deep external review, human-paced — v3.2]
principal_architect_agent ← human calls at a milestone/module/ADR boundary they choose; researches
                          current external best practice and writes a dated redline findings doc;
                          never auto-called, never edits existing design docs directly

[ON DEMAND — Tracker sync, OPTIONAL, only if tracker_config.md exists — v2.5]
tracker_sync_agent     ← human runs "Tracker: sync" (export) or "Tracker: import <ref>" (import); never
                          automatic; Jira or Notion per tracker_config.md's Provider field

[ON DEMAND — Jira sync, OPTIONAL, pre-v2.5 projects only, only if jira_config.md exists — v2.4]
jira_sync_agent        ← superseded by tracker_sync_agent; kept working for projects mid-transition;
                          human runs "Jira: sync" (export) or "Jira: import <key>" (import); never automatic

[ON DEMAND — Learning Roadmap, OPTIONAL, human-invoked only — v2.5]
concept_indexer_agent  ← human runs "Learn: rebuild" (regenerates roadmap_index.md, roadmap_graph.json,
                          and render/index.html), "Learn: open" (opens render/index.html), or
                          "Learn: check coverage" (frontmatter-coverage report only); never automatic

[ON DEMAND — MkDocs Project Docs Site, OPTIONAL, human-invoked only — v2.5, restructured 2026-08-19]
docs_site_agent        ← human runs "Project Docs: build"/"Project Docs: open"
                          ({project_name}-Documents/mkdocs.yml → {project_name}-Documents/
                          {project_name}-Documents-site/); thin wrapper around `mkdocs build`, never
                          authors mkdocs.yml itself, never automatic. No "Docs:" verb — a matching
                          site for AOSDF/ itself (Track D) was built, then cancelled
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
| `tracker_sync_agent` | `agents/tracker_sync_agent.md` | Human (`Tracker: sync` / `Tracker: import`) | Jira or Notion (via MCP, per `tracker_config.md` Provider); never another AOSDF agent | Export: `06_Execution_Plan/tracker_issue_map.md`, `tracker_config.md` (Sync History), tracker items. Import: `15_Addendums/<slug>.md` (draft only) |
| `jira_sync_agent` | `agents/jira_sync_agent.md` | Human (`Jira: sync` / `Jira: import`) — pre-v2.5 projects only | Jira (via MCP); never another AOSDF agent | Export: `06_Execution_Plan/jira_issue_map.md`, `jira_config.md` (Sync History), Jira issues. Import: `15_Addendums/<slug>.md` (draft only) |
| `concept_indexer_agent` | `agents/concept_indexer_agent.md` | Human (`Learn: rebuild` / `Learn: open` / `Learn: check coverage`) | Nothing — reads frontmatter, calls no other agent | `16_Learning_Roadmap/roadmap_index.md`, `roadmap_graph.json`, `render/index.html`, `identified_gaps.md` (append, `Category: Learning`) |
| `docs_site_agent` | `agents/docs_site_agent.md` | Human (`Project Docs: build`/`open`) | `mkdocs build` (external command); never another AOSDF agent | `{project_name}-Documents/{project_name}-Documents-site/` (via `mkdocs build`'s own output — never writes source files or `mkdocs.yml` itself) |
| `principal_architect_agent` | `agents/principal_architect_agent.md` | Human, at a milestone/module/ADR boundary | Nothing — web search/fetch only, no other agent | `principal_architect_review_<date>.md` in the reviewed scope's own directory only |

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
| `tracker_sync_agent` | On `Tracker: sync` or `Tracker: import <ref>` — only if `tracker_config.md` exists (v2.5) |
| `jira_sync_agent` | On `Jira: sync` or `Jira: import <key>` — pre-v2.5 projects only if `jira_config.md` exists (v2.4) |
| `concept_indexer_agent` | On `Learn: rebuild`, `Learn: open`, or `Learn: check coverage` (v2.5) |
| `docs_site_agent` | On `Project Docs: build` or `Project Docs: open` (v2.5, restructured 2026-08-19) |
| `principal_architect_agent` | At a milestone/module/ADR boundary the human chooses, for an external-informed re-review (v3.2) |

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
| WRITE_LOCAL | Create/edit project files | `execution_agent`, `validator_agent`, `architect_agent`, `infra_agent`, `qa_agent`, `captain_agent`, `addendum_agent`, `tracker_sync_agent` (scoped to `tracker_issue_map.md`, `tracker_config.md` Sync History, and Import Mode addendum drafts only), `jira_sync_agent` (pre-v2.5 projects, same scope on the `jira_*` equivalents), `concept_indexer_agent` (scoped to `16_Learning_Roadmap/roadmap_index.md`, `roadmap_graph.json`, `render/index.html`, and `identified_gaps.md` append only), `docs_site_agent` (scoped to `{project_name}-Documents/{project_name}-Documents-site/` via `mkdocs build`'s own output only — never `mkdocs.yml`) |
| WRITE_INFRA | Provision/modify cloud resources | `infra_agent` only (requires human approval before apply) |
| WRITE_DATA | Mutate production data | None — human only |
| WRITE_REMOTE | Push to remote git | **None — git push is always a human action** |
| WRITE_REMOTE (external, v2.5) | Create/update tracker items via MCP | `tracker_sync_agent` (Jira or Notion, per `tracker_config.md`) or `jira_sync_agent` (pre-v2.5 projects) only, and only on an explicit human command each time |
| ADMIN | Cross-cutting (secrets, IAM, DNS) | Human only |
