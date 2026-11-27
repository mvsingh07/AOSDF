# Current workflow rules — single policy entry

Authority: explicit user direction, applicable workspace instructions, this entry (C1–C13 and C15–C17), dated directives, then older framework guidance. Later explicit project decisions govern their own scope; never import another project's authorizations. Historical examples do not grant permissions.

Coordination is opt-in. Strategy A is explicit legacy compatibility; coordinated Strategy B enters `05_AI_Agent_System/automation/coordination-threads/coordinator-definition.md`. Strategy and process Mode are separate choices. Exactly four process Modes exist: Manual, Semi-auto, Easy, Auto. A tooling rollout stage is not a process Mode.

| Rule | Required behavior                                                                                                                                                                                                                                                                                      |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| C1 | Every task has a bounded written plan sized to Small/Standard/High-risk. Small uses up to five lines; Standard/High-risk use one task record. Review timing and count follow C16; High-risk retains independent coordinator-arranged review and serialized implementation writers. |
| C2   | Exactly four Modes: Manual → Semi-auto → Easy → Auto. Founder handles SA in Manual/Semi-auto; Easy uses the founder's Discuss Thread relay; Auto adds SA-owned topology and a founder-approved bounded wave. Other modes keep founder topology/model choice. Tool rollout stage is not Mode.           |
| C3   | Captain creates/replans execution plan; only SA writes it thereafter. Coordinators write their own sprint/tracker row; workers send deltas in result/As-built. Validator records evidence, not canonical status.                                                                                       |
| C4   | Founder authors addendum request; addendum agent writes only addendum plan/tracking; SA registers executable rows and sprint mapping. Large replans use Captain. No unregistered implementation.                                                                                                       |
| C5   | One task record for Standard/High-risk; sprint document is an index/rollup, not its replacement. Small follows C1.                                                                                                                                                                                     |
| C6 | High-risk work has one clean-context independent review during implementation, arranged by the coordinator (founder in Manual). Record reviewer identity, findings and exact revision. No universal pre-implementation review stop; unresolved substantive defects block acceptance. |
| C7   | Coordinated development enters coordinator contract. Commander/execution Strategy A remains explicit legacy compatibility.                                                                                                                                                                             |
| C8 | At most one implementation review per task; an earlier review counts. No focused/post/re-review cycle without an explicit founder request. Address findings and validate the fix. Revise the plan only when it cannot meet acceptance, with one dated note and any separately required protected-scope approval. |
| C9 | Coordinator accepts identity/revision/digest/claim, owned paths, required deliverables and recorded environment/gate evidence once. Copy deferred items to the single hardening list; reject non-deliverable new_files. Do not replay passing checks, demand readbacks/probes or add an acceptance gate. |
| C10  | Launched worker/reviewer/architect uses launching Claude/Codex profile (`CLAUDE_CONFIG_DIR` / `CODEX_HOME`); hand launches obey the same rule.                                                                                                                                                         |
| C11  | Agent/context/rule files do not restate status or gap/action counts; read their authoritative trackers.                                                                                                                                                                                                |
| C12  | Sprint tracker shows current state only; superseded reconciliation goes to append-only archive.                                                                                                                                                                                                        |
| C13  | Every hashed-byte change, including formatting/comments, invalidates affected digest consumers; justify intentional pin updates and run affected checks. No new general dependency-analysis subsystem.                                                                                                 |
| C15 | Durable assignments and recipient-owned read ACKs; delivery, consumption and acceptance remain distinct. See Durable coordination and transport. |
| C16 | One review at most during implementation; prior reviews count. High-risk stays independent/coordinator-arranged; no automatic re-review. See Single implementation review. |
| C17 | STRICT outcome-first delivery in every Mode: required acceptance/checks once, defer optional work to one list, change blocked paths without bypassing gates, and keep only required deliverables. See Outcome-first delivery. |

## Initial planning and review

Establish actual baseline/reuse, objective and non-goals, one owner per surface, dependency order, affected contracts, permitted tools/principal, required positive/negative/failure acceptance, rollback and environment-specific evidence. Preserve security, tenant, secrets, authorization and immutable-migration boundaries.

Size the written plan to risk. Under C16 each task has at most one review during implementation; an earlier review counts. High-risk review remains independent, coordinator-arranged, with serialized implementation writers. Classify findings as acceptance-path blockers or deferred work. Address blockers and validate their fixes; do not launch a focused/post/re-review cycle. A failed required check with unknown cause permits a bounded diagnostic/fix, not speculative investigation. Further review needs an explicit founder request; a plan changes only when it cannot meet acceptance, with one dated note and any separate protected-scope approval.

## Status, ownership and continuity

Captain creates/replans `06_Execution_Plan/execution_plan.md`; Solution Architect (founder acting as SA in Manual/Semi-auto) is its sole ongoing writer. Coordinators write only their sprint and tracker row; workers/validators write owned source and task evidence/As-built and report deltas. Sprint rollup never replaces Standard/High-risk task records. Addendum requests originate with the founder; addendum agents own addendum planning/tracking only; SA registers executable rows and sprint mappings before dispatch.

On entry/resume/compaction reconcile latest numbered alignment round, machine status, sprint and accepted receipt. Consume a result once. Accepted artifacts are immutable; replacements are versioned. Every hashed-byte change, including comments/formatting, invalidates affected consumers; explain intentional pin changes and run affected checks. No general dependency-analysis subsystem is required.

Coordinator acceptance checks task identity, approved revision/digest/claim, owned paths and required evidence/environment. Do not rerun worker suites routinely. Do not request extra probes or rerun accepted checks; fix an actual failed required check within the authorized acceptance path. Consult SA at sprint completion, ownership conflict or real ambiguity, not after every result.

Batch compatible scope before initial review, reuse owned isolation/session and unchanged-revision evidence, run targeted checks then required integration checks, budget initial effort and finish usable scope before optional machinery. Preserve manual-action guides and distinct Dev/Staging/Prod proof. CLI full-auto flags never replace authorization gates.

## References and portable upgrades

- [Proportional rigor](2026-11-04_proportional-rigor-amendment.md)
- [Bounded planning](2026-11-05_bounded-planning-and-review-directive.md)
- [Role boundaries and review control](2026-11-05_strategy-b-role-boundaries-and-founder-review-control.md)
- [Root and branch upgrade protocol](upgrades.md)

## New-document authoring requirement

Every new project document follows [document_authoring.md](document_authoring.md) and `aosdf-doc/v1`, including generated/task/evidence Markdown. Assign a new stable ID when instantiating templates. Preserve metadata on adopted files; run the installed metadata gate before handoff and docs builds. An explicit legacy path inventory preserves old immutable/legacy records, never exempts a whole folder or a future file. No document deletion/merge/supersession without the user's specific consent.

## Durable coordination and transport (C15)

Operating instructions live in maintained role/entry files, not only session context. A recommendation is not an assignment: record its registered task, owning thread, bounded deliverable, scope/model authority and durable assignment path before dispatch. A direct founder instruction may provide authority; its receiving coordinator records it. “Proceed” continues an identifiable authorized assignment; it creates no new scope. Coordinators administer ownership/evidence; workers author implementation and task evidence. Refused launch is a blocker, not permission for coordinator implementation.

At entry/resume, before task selection, after worker/result boundaries and before stopping, process the addressed peer inbox: read its immutable snapshot, ACK as the recipient, and answer each question with linked evidence or a concrete blocker. Use existing authorized internal transport for ordinary lane handoffs. Publication, queueing, native wake, read ACK, answer and acceptance are distinct.

Every Automation Mode round carries explicit `wave:` and `scope:` tags with its round identity and status. A verified exact read ACK closes that routing round even if the recipient subsequently updates its status; new instructions need a new round. Scan validated peer mail before mutable architect notifications. Do not fabricate ACKs for stale or unread input.

The [owner relay](../automation/README.md) delivers input to explicitly bound existing owners. It preserves pause, owner/profile checks, finite continuation/wake budgets and original wave deadlines. Existing-owner transport is communication-only and does not change dispatch. At an all-threads-drained checkpoint the architect assigns the next authorized work or returns a concrete HOLD/ESCALATE and consolidated founder-gate list.

C10 permits an explicitly founder-selected fresh-Claude profile override; defaults still inherit the launching profile. An override is path-only, directory-validated and refused for resumed sessions. No account is a framework default.

Four process Modes remain canonical. The Ultimate Auto delivery extension requires target opt-in. Product-specific environment rules are not generic defaults. The current single-review and outcome-first policy is defined by C16/C17 below; existing installations migrate independently.

## Single implementation review (C16)

At most one review per task, during implementation; a previous review already counts. Do not impose a separate pre-implementation review stop or a focused/post/re-review cycle. High-risk's single review stays independent and coordinator-arranged. Implementation writes stay serialized. Address findings and run the required validation; unresolved substantive defects block acceptance/activation. Keep written bounded plans, administrative acceptance and every separate protected-operation approval. Only an explicit founder instruction requests another review. This rule adds no scope, account, owner, runtime or deadline authority.

## Outcome-first delivery (C17) — STRICT in every Mode

Make the execution plan's goal rows work end to end in the selected project environment, then schedule refinement in testing/hardening. Done means the acceptance criterion passes once with targeted required tests. A wrong result, data loss, security/tenant/secret exposure or another unsafe acceptance path is a blocker and is fixed now, never deferred.

- Defer refactors, polish, hardening, optimisation, generalisation, extra proofs, diagnostics and document reconciliation as one line each in the single append-only `06_Execution_Plan/deferred-to-hardening.md`. The SA schedules these as registered hardening rows after the active goals work. Do not invent separate tasks, rounds or files for them now.
- Run each required check once. No reruns of passing checks, readbacks, inventories or count-only probes; diagnose only a required failure of unknown cause. These rules do not skip required security or acceptance checks.
- Add a migration only when acceptance requires a schema change, one forward migration per task. Revise a plan only when it cannot meet acceptance, with one dated note; optional wording/hash polish is not a reason.
- Workers report a gate, missing principal/credential or dependency once and stop that task. Coordinators record a founder request once and take the next authorized unblocked goal row. Do not loop on evidence packets about an unchanged gate.
- Keep only required deliverables: one task record where required and `result.json` with `deferred` and `new_files`. Coordinators check new files during existing C9 acceptance. Do not copy source trees, fixture trees or packets into runs; use temporary scratch. If an existing isolation tool requires a runs path, preserve it and defer its cleanup. Existing clutter is never deleted by this update.
- Peer messages are only actionable questions, answers or handoffs. Keep rounds about 15 lines with links; read channel tails, not full histories. Rotate large channels verbatim at an authorized quiet checkpoint/wave close and consult history only for older numbered rounds.

C16/C17 supersede older requests for repeated reviews, checks, revisions, diagnostics or documents. Security, tenant, secrets and authorization remain High-risk. Scope, founder consent, shared apply/send/deploy, runtime, credential and other protected gates remain unchanged.
