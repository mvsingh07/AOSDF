---
description: Turn a saved 15_Addendums/<slug>.md requirement into a scoped plan + tracking page (addendum_agent).
argument-hint: <path to 15_Addendums/<slug>.md>
---

Run `addendum-agent` on `$ARGUMENTS`.

Before calling: the addendum document must already be written and saved at that path — this command
never authors the addendum itself, only invokes the agent that plans from it. The agent reads
CLAUDE.md, project_status.md, and execution_plan.md (read-only — never modified), then produces:
1. An implementation plan (flat task table: owner, validation, status) in `15_Addendums/`
2. A tracking page mirroring that plan, updated as work progresses

Do not use this for a scope change that restructures milestones already in progress (re-run
`/aosdf-plan` instead) or for a single-task bug fix (update the execution_plan.md row directly).
