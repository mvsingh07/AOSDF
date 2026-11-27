# Existing-owner file coordination

This transport extends the existing bridge, architect invocation and coordinator trigger. It does not install a separate sprint controller. The [coordinator contract](coordination-threads/coordinator-definition.md), [alignment protocol](coordination-threads/coordinator-architect/README.md) and [current workflow rules](../reference/current-workflow-rules.md) remain authoritative.

## Assignment and round identity

A registered task, owning thread, bounded deliverable, scope/model authority and durable assignment must exist before dispatch. Coordinators administer the workflow; workers implement their bounded task. Every automated round identifies the exact wave, scope, thread, recipient, source and status. New instructions open a new round; they do not edit an already-consumed instruction into new work.

## Delivery, read and acceptance

`channel_delivery.py` captures an immutable source snapshot and creates a deduplicated notification. A queued file does not establish native wake, read or acceptance. The actual recipient reads the pinned snapshot, writes its own verified read ACK and provides a linked answer or concrete scoped blocker. An exact verified ACK closes that routing round even when the recipient changes its channel status afterward. A stale/malformed/unread notification cannot create an ACK or acceptance.

Peer questions normally go to `coordination-threads/thread<N>/instructions/`; maintained guides are also accepted. Existing root-level peer sources remain readable for compatibility. Process validated peer snapshots before mutable architect notifications. After peers drain, stale channel state still requires reconciliation.

## Existing sessions and bounded continuation

`owner_sessions.py` binds a current existing architect/coordinator by runtime identity, process fingerprint, repository and profile. Reservations, dead/uncertain records and live claims block replacement. `coordinator_continuation.py` cooperatively waits and resumes the same owner; it never impersonates an ACK or silently launches a replacement.

An optional bounded mailbox renewal is communication-only: one immutable grant per wave/scope/binding, at most 24 blocks and 3600 seconds, clipped to the original wave deadline. Earlier receipts and exhausted budgets are preserved. Actual native background wait remains necessary for same-session idle wake; file publication alone cannot wake an ended conversation.

## Wake relay and controller

`owner_wake.py` supports installation-verified Codex app, Codex terminal queue and Claude adapters. Select adapters per bound owner; retain that owner's profile. The Claude background-resume option defaults off. Check the installed CLI/runtime contracts before enabling a path; support in another installation is not acceptance evidence here.

Wake input includes owed channel rounds, peer mail, worker results, founder notices and a single all-threads-drained question to the architect. Missing tags can be reported for repair without granting new scope. The architect responds with the next registered assignment or a concrete HOLD/ESCALATE and consolidated founder-gate list.

Require an explicitly enabled relay, an SA-verified active wave, an unexpired original deadline, idle owner, per-event deduplication and a wake budget of at most 96 per owner. Idle windows are 300–7200 seconds. No automatic deadline renewal, account switch, owner takeover, work dispatch or protected operation follows from a wake.

`automode.py` exposes `status`, `watch`, `header`, `start`, `pause`, `continue`, `close`, `restart`, `wake` and `tell`. The read-only console shows both process Mode and controller state. Live operations require separate project adoption and authorization; the source ships only inactive examples. A Mode script is a thin front door to this same engine and refuses conflicting Modes.

## Validation and installation limits

Run the isolated `automation/tests` suite from the framework root. Native CLI/session integration and each owner's first wake need destination-specific acceptance. The current delivery/wake adapters validate a three-thread reference topology; other topologies need explicit adaptation and tests. Config, owner identities, live waves, sockets, active mailbox grants and runtime histories are not portable release content.

## Outcome-first channels and founder inbox

C16/C17 keep task delivery ahead of refinement. Rounds are about 15 lines, end in a plain-language `**Summary:**` line, and use channel-tail reads. `channel_rotate.py`/`automode.py rotate` move old rounds verbatim to `coordinator-architect/history/thread<N>.md`, keeping a single pointer and the newest five rounds. The split/count is verified, recent or concurrent writes are refused, and history is created with document metadata. Older-round lookup must inspect both live and history sources; the generic bounded-job adapter keeps its inactive launch boundary.

A blocking founder decision is recorded before stopping via `ask` with options, recommendation and blocked work. ESCALATE and founder-HOLD rounds are detected as a fallback. Inbox records notify once, remind hourly and route a founder answer as an existing guarded notice. Non-blocking learning items/human-actions are separate from decisions and manual setup, and are suppressed during RUNNING Ultimate Auto. Budget alerts identify the 96-wake cap; owner health reports stopped Codex `systemError` causes without granting replay or takeover authority.
