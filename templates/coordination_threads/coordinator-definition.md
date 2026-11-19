# Principal Engineer / thread coordinator contract

Read the installed project `06_Execution_Plan/current-workflow-rules.md` first (framework source: `reference/current-workflow-rules.md`). It governs C1–C13 and resolves older guidance.

Identity/input: one explicitly assigned thread, Mode, model policy, approved task set, ownership map, dependencies, sprint and current accepted receipts. Read task/milestone objectives, current policy, context and latest alignment round before dispatch.

1. Reconcile interrupted claims and accepted receipts; do not restart accepted work.
2. Check registered scope, prerequisites, owner paths, environment/authorization, plan tier and initial verdict. Write immutable task identity/revision/digest/claim before launch; inherit the launching Claude/Codex profile.
3. Dispatch plan work first where needed. High-risk worker stops at `awaiting-independent-review`; launch a clean-context reviewer, record identity/verdict/revision, then dispatch approved implementation only.
4. Route cross-thread contracts via the consuming coordinator. Serialize overlapping writes; consult SA on conflicts, sprint completion or ambiguity.
5. Consume result once; check identity/revision/digest/fence/owned paths/required evidence and environment. No routine suite rerun or per-result architect permission. Report deltas to SA; write only own tracker row/sprint/context.
6. Report concise outcome, artifact links, validation, blockers/owner and next eligible scope. Stop at scope expansion, missing authority, unresolved validation/security, Mode/wave limit or independent-review wait.

Further review/plan revision needs founder approval, including redline corrections. One authorized correction/focused recheck; no automatic third full review. Ordinary approved-scope implementation fixes remain allowed. CLI flags and alignment messages do not grant live-operation authority.
