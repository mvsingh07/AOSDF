---
description: Export AOSDF's execution state to the configured tracker — Jira or Notion (tracker_sync_agent, Export Mode).
---

Call the `tracker-sync-agent` subagent in **Export Mode** — the same as a human typing `Tracker: sync`
(`Jira: sync` / `Notion: sync` are accepted aliases).

Before calling: confirm `tracker_config.md` exists and says `Enabled: Yes`. If it doesn't, stop and
tell the human to run `workflow_initiator` Step 1 Q8 first — do not create the config or guess a
provider. If only `jira_config.md` exists (pre-v2.5, not yet migrated), call `jira-sync-agent`
instead, the same way, with `Jira: sync`.

This mirrors `execution_plan.md`, milestone exit criteria, the module index, open gaps, and pending
manual actions onto the tracker via the provider's adapter. It never reads from the tracker to
change any AOSDF file — that's Import Mode (`/aosdf-import`), a separate, explicit command.
