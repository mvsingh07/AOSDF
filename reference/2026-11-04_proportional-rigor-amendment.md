# Proportional rigor — reusable directive (2026-11-04)

Read [current rules](current-workflow-rules.md), which resolve the original product-specific amendment.

Small: reversible, bounded changes without identity/security/schema/concurrency impact; ≤5 plan lines and initial one-line self-check. Standard: short task plan with files, risks, binary validation, rollback, reviewer gate and As-built; checklist self-review. High-risk: identity, tenant isolation, authorization, secrets, migrations, concurrency or destructive effects; full plan and independent initial review. When uncertain use the higher tier.

Canonical status belongs to the execution plan; task plans are evidence, not a second status board. Standard/High-risk each have one task record. Initial review precedes implementation. Existing accepted work is preserved; no retrospective review or dispatch. Install coordination only with project-owned topology and inactive tooling.
