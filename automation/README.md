# AOSDF automation

One parent for process Modes, coordination threads and their shared engine. This is reusable, inactive source: no daemon, actor, existing-session wake, profile or active wave is enabled by installing it.

```text
automation/
├── modes/                     # Manual → Semi-auto → Easy → Auto
│   └── ultimate-auto/         # Optional existing-owner wake extension
├── coordination-threads/     # SA, coordinator and worker contracts
│   └── coordinator-architect/# Round protocol and alignment channels
├── file-signals/             # Separate bounded observer/receiver
├── config/                   # Inactive *.example.json only
├── schema/                   # Worker state/result contracts
├── tests/                    # Temporary fixtures and mocked transports
├── automode.py               # Controller and live console
├── owner_wake.py             # Existing-session wake adapters
├── owner_sessions.py         # Explicit binding and owner liveness
├── channel_delivery.py       # Delivery, source snapshots and read ACKs
├── coordinator_continuation.py
├── supervisor.py             # Assignment, fake pilot and gated dispatch
└── ...                       # Shared bridge, monitor and recovery helpers
```

## Read the flow

The [framework](../framework.md) defines requirements, architecture, planning and acceptance. [Coordination contracts](coordination-threads/README.md) allocate that work to explicit owners. The engine carries bounded assignments, channel rounds, peer mail and worker results. Delivery is not a read ACK; a read ACK is not an answer; accepted evidence is not live deployment proof.

[Explore the interactive flow](../assets/diagrams/aosdf-flow.html) or read the [synthetic walkthrough](../examples/coordinated-development/README.md).

## Inspect without activation

From the framework root:

```sh
python3 automation/automode.py status
python3 automation/initiate_automation.py --status
MODE_DRY_RUN=1 python3 automation/modes/ultimate-auto/ultimate_auto.py status
python3 -m unittest discover -s automation/tests -q
python3 -m unittest discover -s automation/file-signals/tests -q
```

`automode.py watch` provides a read-only live console for a configured installation. It shows process state, the shared Mode word, wave countdown, owner wake budgets, channel rounds and workers. It is an operational view, not an independent status authority.

## Adopt deliberately

Copy this whole folder into the adopting project's `05_AI_Agent_System/automation/`. Set `AOSDF_PROJECT_ROOT` explicitly to the project workspace; copy root `agents/` to `05_AI_Agent_System/agents/` and policies to `06_Execution_Plan/`. Rewrite documentation links to the installed destinations. Create project-owned thread records only after topology, ownership and model policy are known. The source folder now uses `coordination-threads` consistently.

Existing installations do not move automatically. Use the [3.7.0 migration recipe](../upgrades/releases/3.7.0/migrate.md); preserve claims, accepted receipts, channel rounds and worker evidence. Reconcile old process/script paths at an idle checkpoint before any authorized restart. Never run two engines over the same writers.

Only example configurations ship. A project separately authorizes live configuration, owner binding, each first wake, fresh actor launch and any protected operation. Keep launching-profile inheritance; a fresh-session override must be explicit, directory-validated and must not carry credentials. CLI availability varies; check the actual installed tools before selecting an adapter.

The added delivery/wake transport is currently qualified against a three-thread reference topology (`thread1`–`thread3`); the framework contracts and worker engine are broader. Adapt and test the transport's thread selectors for other topologies rather than silently assuming support. The deprecated separate sprint-loop controller and product pilot permissions are deliberately excluded.

Four process Modes remain the default. [Ultimate Auto](modes/ultimate-auto/README.md) is an opt-in delivery extension for existing bound owners, not a new default review policy or permission to execute more work. C16/C17 define the current single-review and outcome-first policy; existing installations migrate independently.

## Founder decisions, learning and lean channels

The inactive founder inbox adds `automode.py ask|decisions|answer|dismiss` for blocking decisions, including ESCALATE/founder-HOLD fallback detection, one desktop alert and hourly reminders. An answer is not broader protected-operation authority. `learn|learning|done` and `ask --research` expose non-blocking learning/research items in `12_Manual_Actions/human-actions.md`. Learning is suppressed while Ultimate Auto is RUNNING; plain-language Summary lines remain.

Wake budgets accept 1–96; the relay records low/exhausted alerts and stopped-session owner errors without silently retrying a delivery. `automode.py rotate` archives older channel rounds verbatim after a quiet window, keeping the preamble, one history pointer and the newest five rounds; `--dry-run` writes nothing. Status flags channels over 150 KB. Old-round consumers consult the history archive. No source history, founder decisions or deferral rows ship in templates.

Install the empty `templates/execution_plan/deferred-to-hardening.md` in project `06_Execution_Plan/` and `templates/manual_actions/human-actions.md` in `12_Manual_Actions/`, using the metadata creator for fresh instance identities. Set `AOSDF_DOCUMENTS_ROOT`, `AOSDF_DOCUMENT_TOOLS` and `AOSDF_PROJECT_ID` explicitly if the installed docs/tool layout differs. Source examples remain inactive; no rotation, notification or owner wake is run during installation.
