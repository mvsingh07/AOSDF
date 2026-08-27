# Notion Mapping
# AOSDF v2.5 — Quick Reference (OPTIONAL — only relevant if a project's `tracker_config.md` says
# `Provider: notion` and `Enabled: Yes`)
# Read this alongside `tracker_mapping.md` before running tracker_sync_agent against Notion for the
# first time on a project. `jira_mapping.md` is the equivalent document for `Provider: jira`.

---

## Why This Exists

`tracker_mapping.md` fixes the AOSDF-side vocabulary shared by every provider adapter. This document is
the Notion-specific half of the `TrackerAdapter` implementation: the databases, properties, and
provisioning steps `tracker_sync_agent`'s Notion adapter expects to exist before the first `Tracker: sync`
(or `Notion: sync`) run.

---

## 1. Required Notion Databases (Before First Sync)

| Database | Purpose | Required Properties |
| -------- | ------- | -------------------- |
| Modules *(optional — only if the project tracks `03_System_Design/NNN_<name>_module/` at the tracker level)* | One page per Module | `Name` (title) |
| Milestones | One page per `M{n}_<Name>` | `Name` (title), `AOSDF Task ID` (text — the Milestone's own ID if tracked, otherwise blank), `Module` (relation → Modules, if that database exists), `Status` (select: `Planned` / `In Progress` / `Done` / `Cancelled`) |
| Tasks | One page per Task ID (`M{n}-T{seq}` or `ADD-<slug>-T{seq}`) | `Name` (title), `AOSDF Task ID` (text, join key), `Milestone` (relation → Milestones), `Type` (select: `Story` / `Task`), `Owner` (select or person), `Source Doc` (URL or text), `Validation` (text), `Status` (select, same four values) |

Subtasks use Notion's native sub-item / checklist mechanism on the parent Task page — they do not need
their own database.

**One Notion workspace section (or a dedicated top-level page) per AOSDF project (`{project_name}`)**,
not one shared set of databases for everything — keeps the `AOSDF Task ID` join key unambiguous, mirroring
the "one Jira project per AOSDF project" rule in `jira_mapping.md` §3.

---

## 2. Property Mapping (Notion Side of `tracker_mapping.md` §4)

| AOSDF Field | Notion Property | Type | Notes |
| -------------------------------- | ---------------------- | ------ | ----- |
| Task ID | `AOSDF Task ID` | Text | The join key `tracker_sync_agent` uses (via `tracker_issue_map.md`) to decide create vs. update — never matched by page title, which can drift. |
| Notes column / FRD citation | `Source Doc` | URL or text | Copied verbatim — never paraphrased. |
| Owner | `Owner` | Select or Person | Use Person if the team maps AOSDF Owner values to real Notion workspace members; Select (`owner:backend`, etc.) otherwise — matches the Jira Component-or-Label choice in `jira_mapping.md` §2. |
| Validation criterion | `Validation` | Text | Stays a verifiable condition, never softened into prose. |
| Status | `Status` | Select | Exactly four options: `Planned`, `In Progress`, `Done`, `Cancelled` — 1:1 with `execution_plan.md`, no extra states and no collapsing two AOSDF states into one Notion option. |

---

## 3. Required Notion-Side Setup (Before First Sync)

| Requirement | Why |
| ----------- | --- |
| Integration token with access scoped to the project's Milestones/Tasks (and Modules, if used) databases only | Least-privilege — the same principle `jira_mapping.md` §4 applies to the Jira API credential. Stored in `tracker_config.env` (gitignored, never in `tracker_config.md`) — see `tracker_mapping.md` §2a (OD-2, resolved 2026-08-27). |
| `AOSDF Task ID` property present and set as a distinct, human-visible text property (not hidden) on the Tasks database, and on Milestones if Milestones are also directly addressable | Required join key — see §2. |
| `Status` select property present on both Milestones and Tasks with exactly the four values listed above | Per §2 — a richer workflow (e.g., an added "In Review" option) is fine as long as these four map onto it without collapsing two AOSDF states into one Notion option, same rule as Jira. |
| Relation properties wired: Tasks → Milestones, and Milestones → Modules if that database exists | Needed so `create_issue` can set the parent link described in `tracker_mapping.md` §3. |

If any of these are missing when `tracker_sync_agent` runs against `Provider: notion`, it stops and
reports exactly what's missing — it never attempts to provision Notion databases or properties itself
(same ADMIN-boundary rule as the Jira adapter in `jira_sync_agent.md` Rule 4).

---

## 4. What Administrators Need in Notion

- **To review progress:** nothing beyond normal Notion database views (a board view grouped by `Status`
  works well). No AOSDF-specific Notion integration UI is required beyond the shared integration token.
- **To assign or reprioritize existing work:** admins can freely change Notion-only properties not listed
  in §2 (e.g., a Priority select the team added on their own) — `tracker_sync_agent` never touches
  properties outside this document's field list.
- **To request new feature work:** an admin creates a normal page in the Tasks (or Milestones) database.
  A human then runs `Tracker: import <page-id>` (or the `Notion: import` alias) to draft a
  `15_Addendums/<slug>.md` for engineering review — same intake path as the Jira adapter, keeping new
  work subject to the same FRD/ADR traceability discipline instead of skipping straight into a backlog
  item with no design record behind it.
- **Permission model:** admins/PMs need normal edit rights on the relevant databases. Only the
  integration token used by the MCP connection needs standing write access — no engineer or agent needs
  a personal Notion credential for sync to work.
