# Jira Mapping
# AOSDF v2.4 — Quick Reference (OPTIONAL — only relevant if a project's `jira_config.md` says `Enabled: Yes`)
# Read this before running jira_sync_agent for the first time on a project.
# [v2.5] This is now the Jira-specific half of the generalized tracker integration — see
# AOSDF/reference/tracker_mapping.md for the provider-agnostic TrackerAdapter interface and
# tracker_config.md schema, and notion_mapping.md for the Notion equivalent of this document.

---

## Why This Exists

AOSDF's own hierarchy (Phase → Milestone → Task → Subtask, plus numbered `03_System_Design` Modules) has
no native concept of "Epic" or "Story" — those are Jira vocabulary. This document is the one place that
translation is defined, so every project that opts in to Jira sync (framework.md § Jira Board Integration,
Principle 24) uses the same mapping instead of each project inventing its own.

---

## 1. The Issue-Type Mapping

| AOSDF Unit | Source File | Jira Issue Type | Parent Link | Notes |
| ---------- | ------------------------------------- | ---------------- | ------------------- | ----- |
| Module (`NNN_<name>_module/`) | `03_System_Design/README.md` (module index) | **Feature** *(optional)* | none (top-level) | Only created if the Jira project has a Feature issue type (Jira Premium/Advanced Roadmaps, or a custom scheme). On a stock Jira project without one, **skip this tier** — Epics simply have no parent. Groups the milestones that implement this module, per the Module Design Contract's "every milestone must name its owning module(s)" rule. |
| Milestone (`M{n}_<Name>`) | `07_Milestones/M{n}_<Name>/milestone.md` | **Epic** | Feature (if it exists) for the module the milestone is primarily implementing | Matches AOSDF's own definition: "each milestone = a working, testable system slice." If a milestone spans multiple modules, link to the primary module's Feature and add "relates to" links to the others. |
| Task (`M{n}-T{seq}` or `ADD-<slug>-T{seq}`) | `execution_plan.md` row / milestone task table row | **Story** or **Task** | Epic (the owning Milestone) | **Story** if the task delivers FRD-mapped, user/system-facing functionality (typically Owner = Backend, Frontend, or a service capability). **Task** if it's infra/ops/non-functional (typically Owner = Infra or QA, e.g. "provision VPC," "run load test"). When ambiguous, default to Jira **Task** — it's the safer default for anything not clearly a product-facing Story. |
| Subtask (a row nested under a Task) | milestone task table's Subtask cell | **Sub-task** | Story/Task (the owning Task) | Native Jira sub-task, not a separate top-level issue. |

**Addendum tasks** (`ADD-<slug>-T{seq}` from `15_Addendums/<slug>_plan.md`) follow the same Task→Story/Task
rule, parented under a single Epic per addendum (create one Epic named after the addendum's slug — this is
the one case where an Epic does not correspond to a `07_Milestones/` folder, since Addendums are
deliberately kept outside the main milestone structure per Principle 21).

---

## 2. Field Mapping

| AOSDF Field | Jira Field | Notes |
| -------------------------------- | -------------------------------------- | ----- |
| Task ID (`M{n}-T{seq}`) | Custom field: `AOSDF Task ID` (text) | The join key. `jira_sync_agent` uses this (via `jira_issue_map.md`) to decide create vs. update — never matched by title text, which can drift. |
| Notes column / FRD citation | Custom field: `Source Doc` (text or URL) | Copied verbatim — never paraphrased. This is what lets a Jira reader trace a Story back to the exact requirement that justifies it. |
| Owner (Backend / Infra / QA / Frontend / Human) | Component or Label | Use a Jira Component per owner if the project has them configured; otherwise a label (`owner:backend`, etc.). |
| Validation criterion | Acceptance Criteria field (or description section if no dedicated field) | Must stay a verifiable condition, same as in AOSDF — not softened into prose. |
| Status (`Planned` / `In Progress` / `Done` / `Cancelled`) | Jira workflow status (`To Do` / `In Progress` / `Done` / `Cancelled`) | 1:1. If a project's Jira workflow uses different status names, `jira_config.md` may record an override table — but the four AOSDF states must always map to exactly one Jira status each, no many-to-one collapsing. |

---

## 3. Required Jira Project Setup (Before First Sync)

| Requirement | Why |
| ----------- | --- |
| One Jira project per AOSDF project (`{project_name}`), not one shared project for everything | Keeps the Task-ID join key unambiguous and keeps permission scoping simple (§4). |
| Short project key recorded in `jira_config.md` (e.g., `BID`, `CE`, `SD`, `WEP`, `PWB`) | Used to construct issue keys; also doubles as the short code used in the company-wide project tracking table in `Vusic/infrastructure.md`. |
| Issue types: Epic, Story, Task, Sub-task at minimum; Feature only if available | Per §1. Do not force-enable a Feature issue type just for this — skipping the tier is a supported, expected configuration. |
| Custom fields: `AOSDF Task ID` (text), `Source Doc` (text/URL) | Per §2 — required on Story and Task issue types at minimum. |
| Workflow statuses covering `To Do` / `In Progress` / `Done` / `Cancelled` | Per §2 — a project using a richer workflow (e.g., "In Review") is fine as long as these four map onto it without collapsing two AOSDF states into one Jira status. |

If any of these are missing when `jira_sync_agent` runs, it stops and reports exactly what's missing —
it never attempts to configure the Jira project itself (that's an ADMIN-level action, outside this
agent's permission model).

---

## 4. What Administrators Need in Jira

This answers "how much Jira setup does an admin need to review AOSDF-driven work and assign new feature
work" directly:

- **To review progress:** nothing beyond normal Jira board/backlog views. Every Epic (Milestone) and its
  child Stories/Tasks (AOSDF Tasks) show real status, kept current at whatever cadence the team recorded
  in `jira_config.md` (§5). No AOSDF-specific Jira plugin or view is required.
- **To assign or reprioritize existing work:** admins can freely change Jira-only fields (Assignee, Sprint,
  Story Points, Priority) — `jira_sync_agent` never overwrites these, only the AOSDF-owned fields listed
  in §2.
- **To request new feature work:** an admin creates a normal Epic or Story in the project. A human then
  runs `Jira: import <issue-key>` to draft a `15_Addendums/<slug>.md` for engineering review (see
  `jira_sync_agent.md` § Import Mode) — this is the intended intake path, keeping new work subject to the
  same FRD/ADR traceability discipline as everything else, rather than skipping straight to a backlog
  item with no design record behind it.
- **Permission model:** admins/PMs should have normal Create/Edit/Transition rights on the project. Only
  the person running `jira_sync_agent` needs the Jira API credential used by the MCP connection — no
  engineer or agent needs standing Jira write access outside of that. **[v2.5]** A project running the
  generalized `tracker_sync_agent` instead stores this credential in `tracker_config.env`, not
  `jira_config.md` — see `tracker_mapping.md` §2a (OD-2, resolved 2026-08-27). Pre-v2.5 projects on
  `jira_config.md`/`jira_sync_agent` are unaffected and keep working as documented above.

---

## 5. Recommended Sync Cadence

Sync is **always** human-triggered (framework.md Principle 24) — this section is a recommendation for
*when a human should bother to run the command*, not an enforcement mechanism. Recorded per-project in
`jira_config.md`. Three reasonable defaults:

| Cadence | Best for | Trade-off |
| ------- | -------- | --------- |
| **End of each work session** *(recommended default)* | Small/solo teams already following the `compact → invoke Commander → task runs to completion → compact` loop (framework.md § Session Context Management) | One more command at the natural session boundary; keeps Jira close to real-time without any automation |
| **At milestone boundaries** | Teams where admins only care about milestone-level (Epic-level) visibility, not per-task churn | Jira can look stale mid-milestone; less noise |
| **Before stakeholder reviews** | Teams where Jira is purely a reporting surface for periodic reviews, not a working board | Jira can be significantly stale between reviews; lowest effort |

Whichever is chosen, it is a convention the team agrees to follow — nothing in AOSDF reminds or forces a
human to run `Jira: sync`. If the board looks stale, that means someone hasn't run the command, not that
something is broken.
