# Coordination threads

Reusable roles, coordination contracts, and inactive automation for developing a project across multiple AI threads. This folder is the public source bundle; each adopting project owns its actual thread assignments and runtime records.

## Bundle contents

| File or folder | Purpose |
| --- | --- |
| [coordinator-definition.md](coordinator-definition.md) | Development entry point and coordinator responsibilities. |
| [solution-architect.md](solution-architect.md) | Canonical plan ownership and cross-thread alignment. |
| [worker-definition.md](worker-definition.md) | Worker assignments, owned scope, and result reporting. |
| [init.md](init.md) | Thread initialization guidance. |
| [coordinator-architect/](coordinator-architect/README.md) | Alignment between coordinators and the architect. |
| [automation/](../) | Reusable dispatch, claim, recovery, and reconciliation implementation and tests. |
| [automation-proposal.md](automation-proposal.md) | Tooling scope, inactive defaults, and validation instructions. |
| [file-signals/](../file-signals/README.md) | Bounded file notifications and receiver contracts. |

For a practical introduction, read the [synthetic walkthrough](../../examples/coordinated-development/README.md).

## Install into a project

Read the installed project `06_Execution_Plan/current-workflow-rules.md` first (framework source: `reference/current-workflow-rules.md`). It governs C1–C13 and resolves older guidance.

Install this bundle at `{ProjectName}-Documents/docs/documents/05_AI_Agent_System/automation/coordination-threads/`. Root role files install into `05_AI_Agent_System/agents/`; root `reference/` policies install into `06_Execution_Plan/`. Set links relative to those destinations when installing.

Choose coordination opt-in, process Mode, thread count, identities, model policy, ownership, environment and budgets as explicit project inputs. Manual: founder performs SA and relays work. Semi-auto: founder remains SA with assisted dispatch. Easy: founder relays via Discuss Thread. Auto: SA owns topology inside a founder-approved bounded wave. Never infer a transition. Strategy A remains available explicitly.

After inputs are known, create EMPTY project-owned records:

- `SPRINT-TRACKER.md`: one current row per thread; superseded reconciliation in append-only archive.
- `thread<N>/{README.md,coordinator-context.md,sprint.json}`: scope, ownership, selected model policy and no active assignment initially.
- `thread<N>/agent<N>-<A>/{context.md,task.md,track.md,state.json,runs/}`: identity and owned scope, task initially unassigned, empty run directory and state conforming to automation schema.
- `coordinator-architect/thread<N>.md` and matching numbered machine round records, initially no pending round.

No product topology, claims, sprints, active config, credentials, authorization, accepted digests or runtime history ships in this template. Automation and file-signals are inactive: there is no live config or enabled daemon. Copying templates does not authorize launch.

Entry: [coordinator](coordinator-definition.md), [worker](worker-definition.md), [SA](solution-architect.md), [alignment channel](coordinator-architect/README.md), [automation](automation-proposal.md), [notifications](../file-signals/README.md). On resume reconcile rounds/machine status/sprint/accepted receipt before acting; never redispatch consumed work.
