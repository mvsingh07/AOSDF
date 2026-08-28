---
description: Generate or re-run execution_plan.md, milestones, and the decisions log from the 00-05 docs (captain_agent).
argument-hint: [optional: reason for re-run, if scope changed after the first run]
---

Call the `captain-agent` subagent.

$ARGUMENTS

If no reason for a re-run is given above, this is a first run — please:
1. Read all 00-05 documents (FRD, PRD, BRD, security, architecture, infra)
2. Extract all services, security controls, and infra components
3. Map them to tasks grouped into milestones
4. Write execution_plan.md (flat Phase → Milestone → Task → Subtask table)
5. Write each milestone.md with task table, exit criteria, and dependencies
6. Write 08_Tracking_System/decisions_log.md if absent (decisions log only — not a task board)
7. Validate FRD coverage — every service must have at least one task
8. Log unmapped requirements via `aosdf_log_gap`
9. Set project_status.md to READY if coverage is complete

If a reason for a re-run is given above, instead:
1. Re-read FRD and architecture docs
2. Diff new requirements against current execution_plan.md (its Status column is the record)
3. Append new tasks, mark removed tasks as Cancelled
4. Re-validate FRD coverage
5. Update project_status.md

See `AOSDF/manual.md` § "How to Call the Captain Agent" for the full example.
