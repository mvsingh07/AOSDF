# Numbered coordinator ↔ Solution Architect alignment channel

One `thread<N>.md` per configured thread, plus matching machine round records. Create records only for the selected project topology. Consult on sprint completion, assignment ambiguity or ownership conflict; no routine per-result architect approval.

A round is append-only and numbered monotonically, with UTC checkpoint, task/run/revision/digest/claim identity, artifact references, required evidence and unresolved owner gates. Coordinator writes its `COORDINATOR → ARCHITECT` block; SA writes its `ARCHITECT → COORDINATOR` block and verdict; coordinator writes ACK/consumption. Never overwrite the other's block.

State: `AWAITING-ARCHITECT` → `ALIGNED | REDIRECT | HOLD | ESCALATE` → consumed ACK. A machine GREEN token is alignment metadata, not authority. REDIRECT requiring further review or plan revision waits for founder approval; do not automatically start a correction/review cycle. HOLD/ESCALATE stop dependent work only. Easy relays via Discuss Thread; Auto follows an explicitly approved bounded wave. Consult [current policy](../../../reference/current-workflow-rules.md) after installation.

On restart reconcile latest numbered round, machine status, sprint and accepted receipt; consume once and do not redispatch accepted work. File notifications observe metadata only; no agent wakeup is promised without an attached receiver.
