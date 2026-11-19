> Follow the project current-workflow-rules entry; initial review depth follows Small/Standard/High-risk. Further review or plan revision requires explicit founder approval.

# Standard-tier plan template

> **Current workflow rules (2026-11-06):** [single rules entry](../../reference/current-workflow-rules.md) — order of authority, the 2026-11-04/11-05 directives and clarifications C1–C12. Where this file conflicts, that entry wins.

Use for **Standard** tasks (proportional-rigor amendment, 2026-11-04). Target is about 40–60 lines. Save as
`implementation_prompts/M{m}-T{t}_{slug}_prompt.md`. Small tasks need no plan file; High-risk tasks use the
full 9-section plan plus `high_risk_review_template.md`.

```markdown
# M{m}-T{t} — {title}
**Tier:** Standard · **Row:** M{m}-T{t}{/subtask} · **Env:** Dev

## Context
What and why, in 2–4 lines. Link the ADR/contract if one applies.

## Approach
1. …
2. …

## Files
- path — change

## Risks
- risk → mitigation

## Validation (binary)
- [ ] `npm run build` / lint / type-check green
- [ ] tests for new behavior: …

## Rollback
Revert this change. (Note anything that a revert doesn't undo.)

## Reviewer gate
Tier: Standard — no High-risk triggers (amendment §2)  [ ]
Matches current code/contracts it touches               [ ]
Tenant scoping unchanged or not involved                [ ]
Failure paths handled / tested                          [ ]
Validation checks are binary and runnable               [ ]
Rollback is a revert of this change                     [ ]
Verdict: APPROVED / REDLINED (reason) — YYYY-MM-DD

## As-built
Files changed · checks run with results · limitations (3–6 lines)
```

### Efficiency in the initial scope and review

Apply [the founder-approved workflow](../../reference/2026-11-05_strategy-b-role-boundaries-and-founder-review-control.md). Before initial approval, identify the bounded usable deliverable, compatible batched steps, existing reusable baseline/session/isolation, relevant checks versus the final required integration set, reusable revision-bound evidence, and a task-specific phase time budget. These can be brief fields in the existing plan, not extra documents. Review only whether the approach covers applicable real risks; don't add optional machinery. Approved active plans remain unchanged; later necessary amendments or extra reviews require founder approval.
