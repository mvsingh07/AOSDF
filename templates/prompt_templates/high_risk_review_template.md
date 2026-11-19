> Follow the project current-workflow-rules entry; initial review depth follows Small/Standard/High-risk. Further review or plan revision requires explicit founder approval.

# High-risk independent review: brief and verdict template

> **Current workflow rules (2026-11-06):** [single rules entry](../../reference/current-workflow-rules.md) — order of authority, the 2026-11-04/11-05 directives and clarifications C1–C12. Where this file conflicts, that entry wins.

Required for **High-risk** plans (proportional-rigor amendment §5a, D5 approved 2026-11-04). The reviewer must
not be the plan's author: a fresh Claude/Codex session, the other tool, or a reviewer subagent with clean
context. Same-session self-review does not satisfy this gate.

## Brief to give the reviewer (copy, fill paths)

```text
You are the independent reviewer for a High-risk task in the {project_name} / Comms Engine project.
Read the plan: <path to _prompt.md>
Verify it against the actual code and contracts: <paths>
Applicable ADRs/security docs: <paths>
Check: tenant isolation/RLS, authz, credential handling, webhook verification/replay, migration
immutability and grants for the target DB, failure/retry handling, Dev/Staging/Prod scoping,
testability of the validation criteria, rollback realism.
Do not edit code. Return: findings (severity, location, reason) and a verdict APPROVED or REDLINED.
```

## Verdict block (paste into the plan's Reviewer gate)

```markdown
**Independent review — YYYY-MM-DD**
Reviewer: <fresh Claude session | Codex session | reviewer subagent> (not the author)
Findings:
1. [High/Med/Low] … — location — reason — resolution
Verdict: APPROVED | REDLINED (reasons)
```

A redline needing plan revision or further independent review requires founder approval before that work; stop dependent implementation until the approved plan/verdict is available.

## Bounded review (founder directive 2026-11-05)

Apply [the bounded-review directive](../../reference/2026-11-05_bounded-planning-and-review-directive.md). Initial review covers the whole bounded plan; a correction review covers unresolved findings, material deltas and affected dependencies. List closed findings without reopening them absent new evidence. Each blocker needs a concrete failure scenario/violated requirement and binary resolution. Separate optional polish and unrelated follow-ups from blockers. A wording/hash change is not independently a material design change. After the initial plus one correction pass still leave substantive redlines, consolidate for owner resolution; do not automatically schedule repeated full review. Never approve an unresolved substantive defect to meet a review-count target.

## Initial Strategy B review: prevent downstream review churn

Cover the applicable initial-plan checks in the current directive: actual baseline/reuse; exact ownership and compatibility order; identities/null/canonicalization/clock/privileges/concurrency; execution and migration feasibility; objective-linked binary acceptance and bounded guarantees; rollback/handoff/tier boundaries. Keep non-applicable checks out of the task brief. Return substantive blockers with concrete failure and resolution evidence. If REDLINED, return the findings to the coordinator for a founder-approved amendment/review request; do not automatically run another pass. Approved plans are dispatched, not reassessed by coordinator or Solution Architect.


### Efficiency in the initial scope and review

Apply [the founder-approved workflow](../../reference/2026-11-05_strategy-b-role-boundaries-and-founder-review-control.md). Before initial approval, identify the bounded usable deliverable, compatible batched steps, existing reusable baseline/session/isolation, relevant checks versus the final required integration set, reusable revision-bound evidence, and a task-specific phase time budget. These can be brief fields in the existing plan, not extra documents. Review only whether the approach covers applicable real risks; don't add optional machinery. Approved active plans remain unchanged; later necessary amendments or extra reviews require founder approval.
