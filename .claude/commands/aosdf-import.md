---
description: Draft an addendum from an admin-created tracker item, for human review (tracker_sync_agent, Import Mode).
argument-hint: <tracker ref — Jira key or Notion page id>
---

Call the `tracker-sync-agent` subagent in **Import Mode** with ref `$ARGUMENTS` — the same as a
human typing `Tracker: import $ARGUMENTS` (`Jira: import <key>` / `Notion: import <page-id>` are
accepted aliases).

If `$ARGUMENTS` is empty, stop and ask for the tracker reference first.

Before calling: confirm `tracker_config.md` exists and says `Enabled: Yes` (or use `jira-sync-agent`
with `Jira: import $ARGUMENTS` for a pre-v2.5 project still on `jira_config.md`).

This drafts `15_Addendums/<slug>.md` for human review — it never writes directly to
`execution_plan.md`, any milestone file, or calls `addendum-agent` itself. Review the draft, then
run `/aosdf-addendum` on it if you want to proceed.
