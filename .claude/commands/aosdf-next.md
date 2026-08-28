---
description: Start (or resume) an execution session — find the next Planned task and delegate (commander_agent).
argument-hint: [optional: execution strategy override, e.g. "Strategy A" or "Strategy B"]
---

Call the `commander-agent` subagent.

$ARGUMENTS

Please:
1. Read project_status.md and execution_plan.md (or call `aosdf_read_status` / `aosdf_next_planned_task`)
2. Identify the next Planned task (the Status column — the only status record)
3. Verify no blocking manual actions for this milestone
4. Delegate to `execution-agent` (Strategy A) or `architect-agent` (Strategy B) with full context

This resumes exactly where the project left off — `execution_plan.md`'s Status column is the whole state, so no prior session context is needed. See `AOSDF/manual.md` § "How to Call the Commander Agent" for the full example, and `AOSDF/manual.md` § "Session Context Management" (Principle 27, enforced by the `session-context-gate` hook) for why this may refuse to start a task it can't finish.
