# File-change signals — inactive, notification only

The stdlib helper observes local, bounded control files; never executes their text, launches a command/LLM/worker, or infers authority. No runtime state ships. Configure project root, actor, control paths, state directory and UTC deadline explicitly; actors are project-defined safe identifiers. Credential-bearing paths, workspace escapes and symlinks are refused.

Example invocation shape (replace every placeholder before use):

```sh
bash watch.sh --root <absolute-project-root> --actor <actor-id> --path <relative-control-file> --state-dir <absolute-root>/runtime/signals --mode watch --interval 1 --timeout 50 --until <future-UTC-ISO8601>
```

In an already authorized existing session, attach the same parameters with `--mode receive`. Observer and receiver locks are separate. Without an attached receive tool call, an observer cannot wake an ended conversation. `wait` is a bounded standalone observer. Baseline emits no changed event; unchanged files do not redeliver; cursor survives restart; fast changes coalesce path metadata to the latest snapshot. Delivery is metadata, not exactly-once task claiming or accepted work.

Use a deadline and bounded waits; runtime stays excluded. Stop only verified helper PIDs on rollback, preserving unrelated coordinator/worker/app processes. Validate baseline/change/unchanged/restart, timeout/deadline, lock exclusivity, concurrent receiver, aggregated paths, containment/credential/symlink refusal and SIGTERM cleanup using temporary local fixtures. No application/email acceptance is implied.
