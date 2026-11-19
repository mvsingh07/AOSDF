# Current workflow rules — single policy entry

Authority: explicit user direction, applicable workspace instructions, this entry (C1–C13), dated directives, then older framework guidance. Later explicit project decisions govern their own scope; never import another project's authorizations. Historical examples do not grant permissions.

Coordination is opt-in. Strategy A is explicit legacy compatibility; coordinated Strategy B enters `05_AI_Agent_System/coordination-threads/coordinator-definition.md`. Strategy and process Mode are separate choices. Exactly four process Modes exist: Manual, Semi-auto, Easy, Auto. A tooling rollout stage is not a process Mode.

| Rule | Required behavior                                                                                                                                                                                                                                                                                      |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| C1   | Every task has a written plan and initial verdict. Small: up to five lines in assignment/result/As-built/commit and a one-line self-check; Standard: short plan and checklist self-review; High-risk: full plan and independent review. Same-session review is never independent.                      |
| C2   | Exactly four Modes: Manual → Semi-auto → Easy → Auto. Founder handles SA in Manual/Semi-auto; Easy uses the founder's Discuss Thread relay; Auto adds SA-owned topology and a founder-approved bounded wave. Other modes keep founder topology/model choice. Tool rollout stage is not Mode.           |
| C3   | Captain creates/replans execution plan; only SA writes it thereafter. Coordinators write their own sprint/tracker row; workers send deltas in result/As-built. Validator records evidence, not canonical status.                                                                                       |
| C4   | Founder authors addendum request; addendum agent writes only addendum plan/tracking; SA registers executable rows and sprint mapping. Large replans use Captain. No unregistered implementation.                                                                                                       |
| C5   | One task record for Standard/High-risk; sprint document is an index/rollup, not its replacement. Small follows C1.                                                                                                                                                                                     |
| C6   | High-risk worker writes plan, emits `awaiting-independent-review` and stops. Coordinator launches a clean-context reviewer; Manual founder launches it. Identity and verdict recorded before implementation.                                                                                           |
| C7   | Coordinated development enters coordinator contract. Commander/execution Strategy A remains explicit legacy compatibility.                                                                                                                                                                             |
| C8   | After initial review, further review or plan revision needs explicit founder approval; one authorized correction and focused recheck, then consolidate substantive unresolved blockers with owner. No automatic third full review. Ordinary implementation fixes within approved scope remain allowed. |
| C9   | Coordinator acceptance checks identity, revision/digest/claim, owned paths and recorded gates/environment. No routine suite rerun; one named spot check only for missing/inconsistent evidence, recorded as such and subject to review-control policy.                                                 |
| C10  | Launched worker/reviewer/architect uses launching Claude/Codex profile (`CLAUDE_CONFIG_DIR` / `CODEX_HOME`); hand launches obey the same rule.                                                                                                                                                         |
| C11  | Agent/context/rule files do not restate status or gap/action counts; read their authoritative trackers.                                                                                                                                                                                                |
| C12  | Sprint tracker shows current state only; superseded reconciliation goes to append-only archive.                                                                                                                                                                                                        |
| C13  | Every hashed-byte change, including formatting/comments, invalidates affected digest consumers; justify intentional pin updates and run affected checks. No new general dependency-analysis subsystem.                                                                                                 |

## Initial planning and review

Establish actual baseline/reuse, concrete objective/non-goals, one owner per surface, dependency order, identity/data/security/concurrency/failure contracts, permitted tools/principal, immutable migration requirements, positive/negative/failure acceptance, compatibility, rollback and environment-specific evidence. Classify credential values, locators, hashes and public material separately; use synthetic representative output shapes.

Small has at most five written plan lines and a one-line initial self-check. Standard uses one task record and checklist self-review. High-risk needs a full plan and clean-context independent reviewer: the worker writes `awaiting-independent-review` and stops; the coordinator (founder in Manual) launches the reviewer. Record reviewer identity and exact reviewed revision before implementation. Same-session review is not independent.

Initial authorized scope includes initial review. Further review or plan revision requires explicit founder approval. One approved correction/focused recheck is bounded by that approval; unresolved substantive blockers go to their owner. Ordinary implementation fixes within approved scope remain allowed. Do not invent additional review gates.

## Status, ownership and continuity

Captain creates/replans `06_Execution_Plan/execution_plan.md`; Solution Architect (founder acting as SA in Manual/Semi-auto) is its sole ongoing writer. Coordinators write only their sprint and tracker row; workers/validators write owned source and task evidence/As-built and report deltas. Sprint rollup never replaces Standard/High-risk task records. Addendum requests originate with the founder; addendum agents own addendum planning/tracking only; SA registers executable rows and sprint mappings before dispatch.

On entry/resume/compaction reconcile latest numbered alignment round, machine status, sprint and accepted receipt. Consume a result once. Accepted artifacts are immutable; replacements are versioned. Every hashed-byte change, including comments/formatting, invalidates affected consumers; explain intentional pin changes and run affected checks. No general dependency-analysis subsystem is required.

Coordinator acceptance checks task identity, approved revision/digest/claim, owned paths and required evidence/environment. Do not rerun worker suites routinely. A named spot check is only for missing/inconsistent evidence and remains subject to review control. Consult SA at sprint completion, ownership conflict or real ambiguity, not after every result.

Batch compatible scope before initial review, reuse owned isolation/session and unchanged-revision evidence, run targeted checks then required integration checks, budget initial effort and finish usable scope before optional machinery. Preserve manual-action guides and distinct Dev/Staging/Prod proof. CLI full-auto flags never replace authorization gates.

## References and portable upgrades

- [Proportional rigor](2026-11-04_proportional-rigor-amendment.md)
- [Bounded planning](2026-11-05_bounded-planning-and-review-directive.md)
- [Role boundaries and review control](2026-11-05_strategy-b-role-boundaries-and-founder-review-control.md)
- [Root and branch upgrade protocol](upgrades.md)

## New-document authoring requirement

Every new project document follows [document_authoring.md](document_authoring.md) and `aosdf-doc/v1`, including generated/task/evidence Markdown. Assign a new stable ID when instantiating templates. Preserve metadata on adopted files; run the installed metadata gate before handoff and docs builds. An explicit legacy path inventory preserves old immutable/legacy records, never exempts a whole folder or a future file. No document deletion/merge/supersession without the user's specific consent.
