# Tracker Mapping
# AOSDF v2.5 — Quick Reference (OPTIONAL — only relevant if a project's `tracker_config.md` says `Enabled: Yes`)
# Read this before running tracker_sync_agent for the first time on a project.

---

## Why This Exists

AOSDF v2.4 shipped Jira-only sync (`jira_sync_agent`, `jira_config.md`, `jira_mapping.md`). Principle 25
generalizes that to any tracker provider, starting with Jira and Notion, without changing
`execution_plan.md`'s schema or forcing a rewrite of the v2.4 integration. This document is the shared
layer every provider adapter implements against — the provider-specific setup detail stays in its own
file: `jira_mapping.md` (Jira) and `notion_mapping.md` (Notion).

A v2.4 project with an existing `jira_config.md` is unaffected — see `framework.md` § Tracker Board
Integration → "Migrating from v2.4 Jira-Only Sync."

---

## 1. The `TrackerAdapter` Interface

`tracker_sync_agent` never calls a provider's API or MCP tools directly — it calls these four operations,
and exactly one adapter (Jira or Notion) implements them for the provider named in `tracker_config.md`'s
`Provider:` field. Adding a third provider later means writing a fifth adapter file, never touching
`tracker_sync_agent.md`'s own logic or `execution_plan.md`'s schema (Principle 25).

| Operation | Called During | Input | Output | Must Never |
| --- | --- | --- | --- | --- |
| `create_issue` | Export Mode, Task ID not yet in `tracker_issue_map.md` | AOSDF unit type (Module/Milestone/Task/Subtask), title, description/FRD citation, Owner, Status | Provider-native item reference (Jira key, Notion page ID) | Create a duplicate for a Task ID already mapped |
| `update_status` | Export Mode, Task ID already in `tracker_issue_map.md` | Provider-native item reference, new AOSDF Status | Confirmation | Overwrite provider-only fields (Jira Story Points/Sprint, Notion properties AOSDF doesn't own) |
| `get_issue` | Import Mode | Provider-native item reference (`<ref>` in `Tracker: import <ref>`) | Title, description, acceptance-criteria text | Fabricate content the provider item doesn't have |
| `import_issue` | Import Mode, after `get_issue` | Fetched title/description/acceptance criteria | A drafted `15_Addendums/<slug>.md` (human review required before `addendum_agent` runs) | Call `addendum_agent` itself, or write to `execution_plan.md` |

Every operation reads or writes only the same markdown files AOSDF already uses, plus one external
tracker call per operation — no operation introduces a second local state store (Principle 26).

---

## 2. `tracker_config.md` Schema

Created by `workflow_initiator` Step 5c, or hand-migrated from `jira_config.md` per the framework.md
migration note. One file, one provider:

```markdown
# Tracker Sync Configuration
# {project_name}
# AOSDF v2.5 — OPTIONAL

**Enabled:** Yes
**Provider:** jira | notion
**Sync cadence recommendation:** {end of session | milestone boundaries | before stakeholder reviews}

<!-- Jira-only fields (see jira_mapping.md) -->
**Jira project key:** {key}

<!-- Notion-only fields (see notion_mapping.md) -->
**Notion Modules database ID:** {id}
**Notion Milestones database ID:** {id}
**Notion Tasks database ID:** {id}

**Credentials:** see `tracker_config.env` (same directory) — never stored inline in this file.

> Sync is always human-triggered — `Tracker: sync` (export) or `Tracker: import <ref>` (import).
> `Jira: sync` / `Notion: sync` and `Jira: import` / `Notion: import` remain accepted aliases.
> No agent calls the tracker on its own initiative (framework.md Principle 24).
> See AOSDF/reference/tracker_mapping.md (this file) plus jira_mapping.md or notion_mapping.md
> for the full issue-type mapping and required provider-side setup.

## Sync History
| Date | Direction | Trigger | Notes |
| ---- | --------- | ------- | ----- |
|      |           |         |       |
```

A project fills in only the fields for its chosen `Provider:` — the fields for the other provider are
left in the template as a comment/reminder in case the team ever migrates, but are never read by
`tracker_sync_agent` unless `Provider:` changes.

**A project configures exactly one provider at a time.** Changing providers mid-project is a human-run
edit to `Provider:` (plus filling in the new provider's fields) — never a live dual-write mode
(Principle 25).

---

## 2a. Credential Storage (OD-2, resolved 2026-08-27)

The actual token/secret never lives in `tracker_config.md` — that file sits inside
`{project_name}-Documents/`, which every agent reads freely as project context, so a token stored there
would end up pulled into any agent's context the moment it reads the file, not just at sync time. Instead,
`workflow_initiator` Step 5c creates a sibling file, `tracker_config.env`, in the same directory:

```
# tracker_config.env — gitignored, never committed, never read except by tracker_sync_agent
# Fill in only the fields for the Provider chosen in tracker_config.md

# Jira (only if Provider: jira)
JIRA_API_TOKEN=
JIRA_EMAIL=
JIRA_BASE_URL=

# Notion (only if Provider: notion)
NOTION_API_TOKEN=
```

Rules:
- `tracker_config.env` is read by exactly one agent — `tracker_sync_agent` — and only at the moment it
  runs an Export or Import. No other agent ever opens this file, and it is never quoted or echoed into
  `execution_plan.md`, `identified_gaps.md`, or any other document.
- Gitignored the same way the rest of `{project_name}-Documents/` already is (`setup_aosdf.md` Step 7);
  kept as its own file rather than folded into `tracker_config.md` specifically so the secret stays out
  of every other agent's read path, not just out of git.
- This is a local-file convention, not a new mechanism — it's the same pattern AOSDF already uses for any
  gitignored, human-managed local file. No VSCode `SecretStorage` or OS keychain dependency is introduced;
  those remain options a project can layer on later (e.g. inside a Pillar A VSCode extension), but are not
  required for `tracker_sync_agent` to work today.

---

## 3. The Generalized Issue-Type Mapping

| AOSDF Unit | Source File | Jira Issue Type | Notion Equivalent | Parent Link |
| ---------- | ------------------------------------- | ---------------- | -------------------------------------------------- | ------------------- |
| Module (`NNN_<name>_module/`) | `03_System_Design/README.md` | **Feature** *(optional)* | A page in a "Modules" database | none (top-level) |
| Milestone (`M{n}_<Name>`) | `07_Milestones/M{n}_<Name>/milestone.md` | **Epic** | A page in a "Milestones" database, related to its Module page | Feature/Module page, if one exists |
| Task (`M{n}-T{seq}` or `ADD-<slug>-T{seq}`) | `execution_plan.md` row / milestone task table row | **Story** or **Task** | A page in a "Tasks" database, related to its Milestone page, with a `Type` select property | Epic/Milestone page |
| Subtask (a row nested under a Task) | milestone task table's Subtask cell | **Sub-task** | Notion sub-items (or a checklist block) under the Task page | Story/Task item |

Full provider-specific setup requirements (issue types, custom fields, database schemas, permission
model) live in `jira_mapping.md` and `notion_mapping.md` — this table only fixes the AOSDF-side
vocabulary both adapters share, which is why Jira's Epic → Story → Sub-task chronology is kept as the
*conceptual* model even for Notion (per `aosdf_expansion_scope.md` § 4.3): it's what most stakeholders
already understand, and it keeps the two adapters interchangeable without renaming anything in
`execution_plan.md`.

---

## 4. Field Mapping (Provider-Agnostic Layer)

| AOSDF Field | Purpose | Jira Field | Notion Field |
| -------------------------------- | --- | -------------------------------------- | ----------------------------- |
| Task ID (`M{n}-T{seq}`) | Join key — `tracker_sync_agent` uses this (via `tracker_issue_map.md`) to decide create vs. update, never matched by title text | Custom field: `AOSDF Task ID` (text) | Property: `AOSDF Task ID` (text) |
| Notes column / FRD citation | Traceability — copied verbatim, never paraphrased | Custom field: `Source Doc` (text or URL) | Property: `Source Doc` (URL or text) |
| Owner | Who/what owns the task | Component or Label | Property: `Owner` (select or person) |
| Validation criterion | Verifiable done-condition, not softened prose | Acceptance Criteria field (or description) | Property or block: `Validation` |
| Status (`Planned` / `In Progress` / `Done` / `Cancelled`) | 1:1, no many-to-one collapsing | Jira workflow status | Notion `Status` select property, same four values |

---

## 5. Recommended Sync Cadence

Sync is **always** human-triggered (framework.md Principle 24) — this is a recommendation for *when* a
human should bother to run the command, recorded per-project in `tracker_config.md`. Same three options
as v2.4, provider-independent:

| Cadence | Best for | Trade-off |
| ------- | -------- | --------- |
| **End of each work session** *(recommended default)* | Small/solo teams already following the compact → invoke Commander → task runs to completion → compact loop | One more command at the natural session boundary; keeps the tracker close to real-time without any automation |
| **At milestone boundaries** | Teams where admins only care about milestone-level (Epic-level) visibility | Tracker can look stale mid-milestone; less noise |
| **Before stakeholder reviews** | Teams where the tracker is purely a reporting surface | Can be significantly stale between reviews; lowest effort |
