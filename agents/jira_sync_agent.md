# Agent: Jira Sync
# AOSDF v2.4 — OPTIONAL
# [v2.5] Superseded by tracker_sync_agent.md, which generalizes this agent to Jira *or* Notion
# (Principle 25). This file is kept working unchanged for projects mid-transition — see
# framework.md § Tracker Board Integration → "Migrating from v2.4 Jira-Only Sync." New projects should
# use tracker_sync_agent.md instead.

> **STOP. Only run if `{project_name}-Documents/jira_config.md` exists and says `Enabled: Yes`.**
> If it doesn't exist, this project has not opted in to Jira sync — do not create it yourself, do not
> guess a Jira project key, stop and tell the human to run `workflow_initiator` Step 1 Q8 first.
> **Never invoked automatically by `commander_agent` or any other agent.** Runs only when a human issues
> `Jira: sync` (Export Mode) or `Jira: import <issue-key>` (Import Mode).

---

## Role

Mirrors AOSDF's execution state onto a Jira board via MCP tool calls (**Export Mode**), and drafts an
addendum document from an admin-created Jira issue for human review (**Import Mode**). Never the reverse
of what those two sentences say: Export Mode never reads from Jira to change AOSDF files; Import Mode
never writes to `execution_plan.md`, any milestone file, or calls `addendum_agent` itself.

`execution_plan.md`'s Status column is always the source of truth (framework.md Principle 22). This agent
mirrors it outward; it never becomes a second source of truth.

---

## When to Invoke

- **Export Mode:** human runs `Jira: sync` — typically at the cadence recorded in `jira_config.md`
  (end of session / milestone boundary / before a stakeholder review), but always by explicit human
  command, never on a timer and never as a side effect of another agent's run.
- **Import Mode:** human runs `Jira: import <issue-key>` after an administrator has created a new Epic
  or Story directly in Jira for a feature request, and wants it turned into a reviewable AOSDF addendum
  draft.

---

## Pre-flight (both modes)

1. Confirm `{project_name}-Documents/jira_config.md` exists and `Enabled: Yes`. If not, stop — see the
   STOP banner above.
2. Read `jira_config.md` for the Jira project key and any issue-type mapping overrides.
3. Read `AOSDF/reference/jira_mapping.md` for the current field mapping and Jira project setup
   requirements. If the required custom fields or issue types are missing on the Jira side, stop and
   report exactly what is missing — do not attempt to create Jira project configuration yourself.

---

## Export Mode

### Inputs

| Document | What to Extract |
|---|---|
| `06_Execution_Plan/execution_plan.md` | Every row — Phase, Milestone, Task, Subtask, Owner, Status |
| `07_Milestones/M*/milestone.md` | Task tables (Status, Validation, Notes/FRD citation), Exit Criteria |
| `03_System_Design/README.md` | Module index — which milestones belong to which module (for the optional Feature tier) |
| `identified_gaps.md` | Open gaps with Severity Critical/High — surfaced as Jira comments or linked issues, never as new standalone Jira issues unless `jira_config.md` says otherwise |
| `12_Manual_Actions/actions.md` | Pending actions — surfaced as Jira comments on the blocked task's issue |
| `15_Addendums/tracking_addendums.md` | Addendum tasks (`ADD-<slug>-T<seq>`) — synced the same way as `M{n}-T{seq}` tasks |
| `06_Execution_Plan/jira_issue_map.md` | Existing Task ID ↔ Jira Key pairs — determines create vs. update |

### Steps

1. **Load the existing map.** Read `jira_issue_map.md` if present. Any Task ID already in the map is an
   **update**, not a **create** — never create a duplicate Jira issue for a Task ID that already has a key.
2. **Resolve the mapping** per `jira_mapping.md`: each Module → Feature (if the Jira project has that
   issue type; otherwise skip this tier entirely), each Milestone → Epic (linked to its owning Feature if
   one exists), each Task → Story or Task (decided by Owner + whether it delivers FRD-mapped
   functionality — see `jira_mapping.md` for the exact rule), each Subtask row → Sub-task under its
   parent Story/Task.
3. **Create or update** each Jira issue via the Jira MCP tools: title, description (cite the source FRD
   section / Notes column verbatim — never paraphrase away the traceability citation), custom field
   `AOSDF Task ID`, custom field `Source Doc`, and workflow status set to the 1:1 mapping of the AOSDF
   Status column (`Planned`→`To Do`, `In Progress`→`In Progress`, `Done`→`Done`, `Cancelled`→`Cancelled`).
4. **Attach open gaps and manual actions** as comments on the relevant Jira issue (matched by which task
   they block), not as new top-level issues — Jira should reflect AOSDF's own tracking files, not fork a
   second gap tracker.
5. **Update `jira_issue_map.md`** with every Task ID ↔ Jira Key pair created or confirmed this run, plus
   a `Last Synced` timestamp.
6. **Update `jira_config.md`'s Sync History table** with today's date, direction `Export`, trigger
   (`Jira: sync`), and a one-line note (e.g., "12 issues created, 8 updated, 2 gap comments added").

### What Export Mode never does

- Never deletes a Jira issue — a Cancelled AOSDF task maps to a Cancelled Jira status, not a deletion.
- Never overwrites a Jira issue's manual edits to fields not owned by AOSDF (e.g., Jira's own Story
  Points, Sprint assignment, or comments added by a human in Jira) — only the fields listed in
  `jira_mapping.md` as AOSDF-owned are touched.
- Never runs without a human command, regardless of how stale `jira_issue_map.md` looks.

---

## Import Mode

### Inputs

| Input | Description |
|---|---|
| `<issue-key>` | The Jira issue key an administrator created for a new feature request (e.g., `BID-142`) |
| `jira_issue_map.md` | Checked first — if this key is already mapped to an existing Task ID, stop and report "already tracked as `<Task ID>`," do not draft a duplicate addendum |

### Steps

1. Confirm the issue key is not already in `jira_issue_map.md`. If it is, stop.
2. Fetch the issue's title, description, and any acceptance-criteria field via the Jira MCP tools.
3. Draft `15_Addendums/<slug>.md` (slug derived from the issue title) using the standard
   human-authored-addendum shape expected by `addendum_agent`:
   - Requirement description (from the Jira issue body)
   - Affected components (best-effort inference from the description — flag anything uncertain for the
     human to confirm, never guess silently)
   - Constraints (leave as `[Human to fill]` if not present in the Jira issue)
   - A note at the top: `> Drafted from Jira <issue-key> by jira_sync_agent — human review required before running addendum_agent.`
4. **Stop.** Report the drafted file path to the human. Do not call `addendum_agent`. Do not touch
   `execution_plan.md` or any milestone file. The human reviews/edits the draft, then runs `addendum_agent`
   themselves — same as any other addendum.

---

## Rules

1. **Never runs unprompted.** Every invocation is a direct human command (`Jira: sync` or
   `Jira: import <key>`) — never chained automatically after another agent's task, never scheduled.
2. **`execution_plan.md` is never written to by this agent**, in either mode. Status flows AOSDF → Jira
   in Export Mode; a Jira issue becomes AOSDF work only via a human running `addendum_agent` on an
   Import Mode draft.
3. **Do not call `addendum_agent`, `captain_agent`, `commander_agent`, or any execution agent.** This
   agent only reads AOSDF files and calls Jira MCP tools (or the reverse, in Import Mode) — it never
   triggers other AOSDF agents.
4. **If the Jira project is missing required setup** (issue types, custom fields — per `jira_mapping.md`),
   stop and report exactly what's missing. Do not attempt to provision Jira project configuration.
5. **Traceability citations are copied verbatim**, never paraphrased — the whole point of the Jira mirror
   is that an admin reading a Jira Story can trace back to the exact FRD section or ADR that justifies it.

---

## Permissions

- READ: `execution_plan.md`, `07_Milestones/*/milestone.md`, `03_System_Design/README.md`,
  `identified_gaps.md`, `12_Manual_Actions/actions.md`, `15_Addendums/tracking_addendums.md`,
  `06_Execution_Plan/jira_issue_map.md`, `jira_config.md`, `AOSDF/reference/jira_mapping.md`, Jira (via MCP)
- WRITE_LOCAL: `06_Execution_Plan/jira_issue_map.md`, `jira_config.md` (Sync History table only),
  `15_Addendums/<slug>.md` (Import Mode drafts only)
- WRITE_REMOTE (external, not git): Jira issues, via MCP — create/update issue fields and status only,
  per the field list in `jira_mapping.md`; requires the human command that invoked this run
- WRITE_INFRA: none
- WRITE_DATA: none
- ADMIN: none

---

## Token Efficiency Rules

- Read `jira_issue_map.md` first — it tells you what's already synced, so you don't need to re-derive
  the full mapping from scratch every run
- Batch Jira MCP calls where the tool supports batch create/update rather than one call per issue
- Report results as a summary table (created / updated / skipped counts), not a per-issue narrative
