# Coordination contracts — inactive installation template

Read the installed project `06_Execution_Plan/current-workflow-rules.md` first (framework source: `reference/current-workflow-rules.md`). It governs C1–C13 and resolves older guidance.

Install this bundle at `{ProjectName}-Documents/docs/documents/05_AI_Agent_System/coordination-threads/`. Root role files install into its sibling `agents/`; root `reference/` policies install into `06_Execution_Plan/`. Set links relative to those destinations when installing.

Choose coordination opt-in, process Mode, thread count, identities, model policy, ownership, environment and budgets as explicit project inputs. Manual: founder performs SA and relays work. Semi-auto: founder remains SA with assisted dispatch. Easy: founder relays via Discuss Thread. Auto: SA owns topology inside a founder-approved bounded wave. Never infer a transition. Strategy A remains available explicitly.

After inputs are known, create EMPTY project-owned records:

- `SPRINT-TRACKER.md`: one current row per thread; superseded reconciliation in append-only archive.
- `thread<N>/{README.md,coordinator-context.md,sprint.json}`: scope, ownership, selected model policy and no active assignment initially.
- `thread<N>/agent<N>-<A>/{context.md,task.md,track.md,state.json,runs/}`: identity and owned scope, task initially unassigned, empty run directory and state conforming to automation schema.
- `coordinator-architect/thread<N>.md` and matching numbered machine round records, initially no pending round.

No product topology, claims, sprints, active config, credentials, authorization, accepted digests or runtime history ships in this template. Automation and file-signals are inactive: there is no live config or enabled daemon. Copying templates does not authorize launch.

Entry: [coordinator](coordinator-definition.md), [worker](worker-definition.md), [SA](solution-architect.md), [alignment channel](coordinator-architect/README.md), [automation](automation-proposal.md), [notifications](file-signals/README.md). On resume reconcile rounds/machine status/sprint/accepted receipt before acting; never redispatch consumed work.
