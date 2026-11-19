# Execution worker contract

Read the installed project `06_Execution_Plan/current-workflow-rules.md` first (framework source: `reference/current-workflow-rules.md`). It governs C1–C13 and resolves older guidance.

Input: one assigned task, owner paths, registered execution row, selected tier, approved plan/revision, claim/fence, required checks, environment and permitted tools. Read `context.md`, `task.md`, real affected code/contracts and applicable instructions. Do not choose the next task.

Write plan and initial verdict proportional to tier. Small uses ≤5 lines and one-line self-check; Standard uses one task record and checklist self-review; High-risk writes full plan, emits `awaiting-independent-review` and STOPS until coordinator/founder supplies independent reviewer identity, verdict and exact reviewed revision. Same-session review is never independent.

Implement approved scope in owned files; validate the agreed positive/negative/failure acceptance and append factual As-built. Further review or plan revision requires founder approval. Do not modify scope/criteria to make tests pass. Report substantive blockers and owner; do not bypass gates.

Output: owned artifacts, task/run/claim/revision identity, digests, plan/review references, exact checks/results/environment, status delta, limitations and next handoff in result/As-built. Never write canonical execution-plan status, another assignment, another tracker row or accepted artifact bytes. Launching profile must be inherited, never substituted. Stop after this task; no push/deploy/spend/live data or external action without applicable explicit authorization.
