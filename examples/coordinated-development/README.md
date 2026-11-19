# Synthetic coordination walkthrough

This fictional inventory application illustrates the protocol without copying a real product's topology, private requirements or live run records. It is a worked example, not an enabled runner.

## Scenario and ownership

The approved requirement is: display inventory items from a read-only API with a documented empty state. The Solution Architect owns the canonical execution plan and shared API contract. A backend thread owns `api/`; a web thread owns `web/`. Shared contract changes return to the architect; neither worker silently expands its owned paths. These names are example project inputs, not framework defaults.

1. Run setup using [the public guide](../../prompts/setup_aosdf.md). Explicitly choose coordinated Strategy B and Manual Mode. The founder performs the Solution Architect role in this Mode.
2. Install [coordination templates](../../templates/coordination_threads/README.md) at `docs/documents/05_AI_Agent_System/coordination-threads/`, keeping automation inactive. Install role and policy files at their documented destinations and rewrite links. Create empty project-owned records only after identities and ownership are known.
3. Captain creates the initial execution plan. The architect records the API contract, dependency and acceptance criteria. The backend task returns a fixed-schema item list; the web task consumes that schema and handles the empty list. Changes to authorization or tenant boundaries would be High-risk and need independent review.
4. Each coordinator issues a bounded task to its worker. The worker follows plan → review → implement → validate at the assigned risk tier. A worker returns changed files, test evidence, deviations and blockers in the documented result format. Events signal available work; they do not accept results or grant permission.
5. The coordinator reconciles the result against its task and records the thread outcome. The architect alone reconciles accepted completion into the canonical execution plan. The web thread starts integration after the contract dependency is satisfied.
6. On interruption, read the latest task, claim/fence, sprint and accepted receipt before resuming. A live writer retains ownership; already-consumed results are not dispatched again. Missing authority or a failed acceptance criterion blocks completion.
7. Close the example only after API and UI acceptance checks pass. Build evidence does not establish live deployment. Deploy and verify a project only under that project's release authorization.

## Exercise the implementation without launching agents

From the framework root:

```sh
(cd templates/coordination_threads/automation && python3 -m unittest discover -s tests -v)
(cd templates/coordination_threads/file-signals && python3 -m unittest discover -s tests -v)
```

The fixtures cover concurrent claims, stale results, fencing, reconciliation and bounded notifications using temporary directories and mocks. They do not activate a daemon, call a model, or prove unattended production delivery. For project-owned records, follow the template README and machine schemas rather than copying mock test state.
