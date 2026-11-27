#!/usr/bin/env python3
"""coordinator_trigger.py — launch thread coordinators launch-and-stop (the factory's hands).

Founder question (2026-10-28): "what about the thread coordinators, how will they be running —
all the time, or the same launch/stop approach?"

Answer embodied here: the SAME launch-and-stop approach as the Solution Architect and the workers.
A coordinator is a billed agent session, not a cheap daemon; keeping it always-on burns budget and
it has nothing to do between boundaries. So the cheap Python daemons are always-on; the coordinator
is SUMMONED for a sprint, runs its SELECT -> DISPATCH -> ... -> sprint-boundary loop in a visible,
watchable window, and exits. This daemon is the summoner: each tick it decides whether a thread's
coordinator is owed a launch, and (when the gate is armed) opens it.

A coordinator is owed a launch only when the channel's latest numbered round carries an
architect verdict ALIGNED/REDIRECT for its verified wave sprint. ACK -> GREEN is consumption,
not a second launch event. A live coordinator on the same thread blocks every new launch.
It is NOT owed when the latest round is AWAITING-ARCHITECT (architect's turn) or HOLD/ESCALATE
(parked / founder's turn), or when no wave sprint remains for the thread.

Live launch is DUAL-GATED, OFF by default, like supervisor.py --dispatch and the architect
write-back: config/coordinator_launch.json -> {"auto_launch": "authorized"} AND the
--i-have-authorized-coordinator-autolaunch flag. Without both, every launch is a PREVIEW that opens
nothing. The coordinator it launches grants nothing new: worker dispatch stays behind ITS own gate
(supervisor), hard gates stay where AGENTS.md puts them, the Solution Architect stays sole canonical writer.
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
VAR_DIR = os.path.join(HERE, "var")
RUNS_DIR = os.path.join(VAR_DIR, "coordinator-runs")
CONFIG_DIR = os.path.join(HERE, "config")
LAUNCH_CFG = os.path.join(CONFIG_DIR, "coordinator_launch.json")
CURSOR_PATH = os.path.join(VAR_DIR, "coordinator_trigger.cursor.json")

import architect_bridge as _bridge   # noqa: E402  (reuse channel scan)
import visible_launch as _vl          # noqa: E402
import wave as _wave                  # noqa: E402
import sprint as _sprint              # noqa: E402
import daemon as _d                   # noqa: E402
import channel_delivery as _delivery  # noqa: E402

NAME = "coordinator_trigger"

from layout import PROJECT_ROOT
REPO_ROOT = str(PROJECT_ROOT)
AGENT_SYS_DIR = str(Path(HERE).parent)
from layout import THREADS
THREADS_DIR = str(THREADS)

PROCEED_VERDICTS = {"ALIGNED", "REDIRECT"}
PARKED_VERDICTS = {"HOLD", "ESCALATE"}


def _json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def gate_open(flag_set: bool) -> bool:
    cfg = _json(LAUNCH_CFG, {}).get("auto_launch") == "authorized"
    return cfg and flag_set


def _thread_folder(thread_n: int) -> str:
    return os.path.join(THREADS_DIR, f"thread{thread_n}")


def _wave_has_work(thread_n: int, wave: dict | None) -> bool:
    return _wave.verified_thread_sprint(wave, thread_n) is not None


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # fail closed if liveness cannot be observed


def _legacy_run_alive(run_dir: Path) -> bool:
    """Observe a pre-PID-marker Terminal session by its unique log path in `script` argv."""
    try:
        proc = subprocess.run(["ps", "-axo", "command="], capture_output=True, text=True,
                              timeout=5, check=True)
    except (OSError, subprocess.SubprocessError):
        return True  # uncertain legacy window: block rather than duplicate
    return str(run_dir / "terminal.log") in proc.stdout


def live_coordinator_run(thread_n: int) -> str | None:
    """Return an active run path, including a just-launched window awaiting its PID file."""
    import owner_sessions
    external = owner_sessions.blocking_owner('coordinator', thread_n)
    if external:
        return external
    folder = Path(RUNS_DIR) / f"thread{thread_n}"
    if not folder.exists():
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    for run_dir in folder.iterdir():
        if not run_dir.is_dir():
            continue
        pid_file = run_dir / "coordinator.pid"
        if pid_file.exists():
            try:
                if _pid_alive(int(pid_file.read_text().strip())):
                    return str(run_dir)
            except ValueError:
                return str(run_dir)  # malformed live marker: fail closed
            continue
        launch = _json(run_dir / "launch.json", {})
        if not launch.get("window_id"):
            continue
        try:
            created = datetime.datetime.fromisoformat(launch["created_utc"])
            if (now - created).total_seconds() < 120:
                return str(run_dir)
        except (KeyError, ValueError, TypeError):
            return str(run_dir)
        if _legacy_run_alive(run_dir):
            return str(run_dir)
    return None


@contextmanager
def _launch_guard():
    """Serialize competing trigger processes across cursor read, live check and launch."""
    with _delivery.dispatch_guard():
        yield


def owed(thread_n: int, wave: dict | None) -> dict | None:
    """Return a reason-dict iff this thread's coordinator is owed a launch, else None."""
    chan = os.path.join(_bridge.CHANNEL_DIR, f"thread{thread_n}.md")
    latest = _bridge._latest_round(chan)
    status = (latest or {}).get("status")
    if status == _bridge.AWAITING:
        return None  # architect's turn
    if status in PARKED_VERDICTS:
        return None  # HOLD -> parked; ESCALATE -> founder
    if status == _bridge.GREEN:
        return None  # an ACK is not a new task; resume requires an explicit event
    if not _wave_has_work(thread_n, wave):
        return None  # no architect-verified, exact task scope for this thread
    scoped = _bridge.scoped_round(thread_n, wave, latest)
    if not scoped:
        return None
    if not latest or latest.get("round", 0) < scoped["opening_round"]:
        return None  # stale round from a previous wave cannot start this sprint
    if latest["round"] == scoped["opening_round"] and latest.get("bootstrap_wave") != wave.get("wave_id"):
        return None  # opening round must explicitly name this approved wave
    if status in PROCEED_VERDICTS:
        return {"thread": thread_n, "trigger": f"verdict {status} to consume", "round": latest}
    # Unknown or incomplete states have no launch authority.
    return None


def boot_prompt(thread_n: int, reason: dict, wave: dict | None) -> str:
    agents_md = os.path.join(REPO_ROOT, "AGENTS.md")
    role_def = os.path.join(AGENT_SYS_DIR, "agents", "principal_engineer_agent.md")
    coord_def = os.path.join(THREADS_DIR, "coordinator-definition.md")
    channel_readme = os.path.join(_bridge.CHANNEL_DIR, "README.md")
    thread_md = os.path.join(_bridge.CHANNEL_DIR, f"thread{thread_n}.md")
    sprint_json = os.path.join(_thread_folder(thread_n), "sprint.json")
    supervisor = os.path.join(HERE, "supervisor.py")
    wave_line = ""
    if wave:
        cur = _wave.verified_thread_sprint(wave, thread_n)
        wave_line = (f" Read the verified automation wave {_wave.WAVE_PATH}. "
                     f"Your Thread {thread_n} sprint in wave {wave.get('wave_id')} is "
                     f"{cur.get('id') if cur else '(none)'}: {cur.get('scope','') if cur else ''}; "
                     f"exact ordered task IDs: {', '.join(cur.get('task_ids', [])) if cur else '(none)'}; "
                     f"scope review: {cur.get('scope_review_ref') if cur else '(none)'}. "
                     f"Advance through the wave's Thread {thread_n} sprints without returning to the "
                     f"founder between sprints.")
    return (
        f"You are the Thread {thread_n} coordinator (Principal Engineer) for the Supagram coordination "
        f"system. You were launched because: {reason.get('trigger')}. "
        f"Read, in order: {agents_md}; {role_def}; {coord_def}; {channel_readme}; your channel file "
        f"{thread_md}; and your sprint state {sprint_json}. "
        f"Run your assigned sprint autonomously per the coordinator definition: SELECT -> BATCH -> "
        f"ALIGN -> DISPATCH -> WAIT -> RECEIVE -> ACCEPT -> NEXT, without asking the founder between "
        f"tasks. Keep the whole sprint in this one coordinator session. "
        f"BATCH, do NOT fan out: never launch a separate worker per task. Group every compatible, ready, "
        f"same-thread task — same owner/area, no conflicting file/migration ownership, no unmet "
        f"inter-task dependency — into ONE worker dispatch and launch a SINGLE worker for that batch. "
        f"Split into a second worker only when scope is genuinely incompatible (different owner/area, "
        f"a real file-ownership conflict, or a dependency that must finish first); state that reason in "
        f"the dispatch record. "
        f"Proceed autonomously within your assigned sprint after its applicable Strategy B gates. "
        f"Consult the architect only at sprint completion, an actual cross-thread conflict, or ownership "
        f"ambiguity. Do not add a pre-dispatch architect gate. Never re-dispatch accepted or live work. "
        f"A GREEN ACK is consumption, not a fresh launch instruction. "
        f"A plan-ready result or a next-action summary is intermediate: continue through required review, "
        f"implementation, validation and administrative acceptance in this same bounded sprint. "
        f"For long waits use the existing session's native background Bash task and the installed "
        f"owner binding/continuation guide; do not detach an unobservable shell or create a replacement owner. "
        f"If usage limits interrupt this session, checkpoint the active claim, task digest, last receipt "
        f"and next action; do not relaunch or re-dispatch merely to recover from the limit. "
        f"Before editing any existing sprint artifact, compare its digest with accepted handoffs and "
        f"downstream references; never overwrite bytes already consumed by another thread. "
        f"Launch the batch's worker with `python3 {supervisor} --assign <agent>` (worker dispatch stays "
        f"behind its own gate). When the channel's latest round carries an architect verdict "
        f"(ALIGNED/REDIRECT), read it, append your COORDINATOR ACK, flip that round's status token to "
        f"GREEN, and apply the directive. Open an AWAITING-ARCHITECT round only at a sprint completion, "
        f"at an actual cross-thread conflict, or at a thread-assignment "
        f"ambiguity.{wave_line} "
        f"STOP at: sprint completion (write the round and stop), a hard gate (push/deploy/publish, DNS, "
        f"live-send, spend, secrets, live-delete, Class-B/C — do NOT cross it; surface it), or a genuine "
        f"blocker. {_wave.OWNERSHIP_COORDINATOR} When you stop, print one line "
        f"stating what you did and why you stopped."
    )


def _launch_argv(thread_n: int, prompt: str, model: str, executor: str):
    cd = Path(REPO_ROOT)
    executor, model = _vl.execution_choice(executor, model)
    if executor == "codex":
        return "codex", _vl.codex_interactive_argv(cd, prompt, yolo=True, model=model)
    return "claude", _vl.claude_argv(cd, prompt, skip_permissions=True, model=model)


def invoke(thread_n: int, reason: dict, wave: dict | None, *, dry_run: bool = True,
           live_authorized: bool = False, notification=None) -> dict:
    if dry_run:
        return _invoke_locked(thread_n, reason, wave, dry_run=True, notification=notification)
    if not gate_open(live_authorized):
        return {"launch": {"refused": "coordinator dual gate not authorized"}}
    with _launch_guard():
        _delivery.foreign_controller_conflict()
        if live_coordinator_run(thread_n) or _delivery.active_architect():
            return {"launch": {"refused": "existing owner is active; no replacement session"}}
        if not _bridge.scoped_round(thread_n, wave, reason.get("round")):
            return {"launch": {"refused": "unverified/stale coordinator scope"}}
        if _bridge._latest_round(os.path.join(_bridge.CHANNEL_DIR, f"thread{thread_n}.md")) != reason.get("round"):
            return {"launch": {"refused": "channel changed before coordinator launch"}}
        scoped = _bridge.scoped_round(thread_n, wave, reason['round'])
        if notification is None:
            notification = _delivery.emit(wave_id=wave['wave_id'], scope=_delivery.scope_sha(wave, scoped),
                thread=thread_n, recipient='coordinator', number=reason['round']['round'],
                status=reason['round']['status'], source=Path(_bridge.CHANNEL_DIR) / f'thread{thread_n}.md')
        _delivery.load(notification, recipient='coordinator', thread=thread_n,
                       wave_id=wave['wave_id'], scope=_delivery.scope_sha(wave, scoped))
        return _invoke_locked(thread_n, reason, wave, dry_run=False, notification=notification)


def _invoke_locked(thread_n, reason, wave, *, dry_run, notification):
    if not dry_run and wave and wave.get('delivery_only'):
        return {'thread': thread_n, 'reason': reason, 'launch': {'refused': 'delivery-only envelope grants no actor launch'}}
    # Executor/model from the thread's recorded sprint decision (Q2), else claude/opus.
    sp = _sprint.load(Path(_thread_folder(thread_n)) / "sprint.json") or {}
    requested_executor = (sp.get("executor") or "claude").lower()
    model = sp.get("model") or ("opus" if requested_executor == "claude" else None)
    executor, model = _vl.execution_choice(requested_executor, model)
    prompt = boot_prompt(thread_n, reason, wave)
    scoped = _wave.verified_thread_sprint(wave, thread_n)
    if scoped:
        scope_hash = _delivery.scope_sha(wave, scoped)
        prompt += _delivery.polling_text("coordinator", thread_n, wave["wave_id"], scope_hash)
        prompt += (f" New numbered boundaries must include wave:{wave['wave_id']} scope:{scope_hash} "
                   "in their machine comment; retain those tokens when acknowledging GREEN.")
    if notification:
        prompt += f" Read and explicitly acknowledge this exact notification first: {notification}."
    tag = reason.get("round", {})
    sig = f"round{tag.get('round','x')}-{tag.get('status','start')}"
    run_dir = Path(RUNS_DIR) / f"thread{thread_n}" / sig
    ex_name, argv = _launch_argv(thread_n, prompt, model, executor)
    title = f"Supagram — Thread {thread_n} Coordinator — {sig}"
    profile = _json(LAUNCH_CFG, {}).get("claude_profile")
    if profile is not None and profile not in _vl.CLAUDE_PROFILES:
        raise ValueError("unknown explicit Claude dispatcher profile")
    kwargs = {}
    if profile and ex_name == "claude":
        kwargs["claude_profile_dir"] = _vl.CLAUDE_PROFILES[profile]
    launch = _vl.launch_visible(run_dir, f"{ex_name}-coordinator", argv, title=title,
                                dry_run=dry_run, record_pid=True, requested_executor=requested_executor, **kwargs)
    return {"thread": thread_n, "executor": executor, "model": model, "reason": reason,
            "dry_run": dry_run, "launch": launch, "prompt": prompt}


def _tick_once(flag_set: bool, *, reset: bool = False) -> dict:
    live = gate_open(flag_set)
    wave = _wave.active_wave()
    cursor = {} if reset else _json(CURSOR_PATH, {})
    results = []
    for n, _path in _bridge._thread_files():
        reason = owed(n, wave)
        if not reason:
            continue
        key = str(n)
        rnd = reason.get("round") or {}
        scoped = _wave.verified_thread_sprint(wave, n)
        sig = f"{wave.get('wave_id') if wave else '-'}:{scoped.get('id') if scoped else '-'}:{rnd.get('round','-')}:{rnd.get('status','start')}"
        if live and cursor.get(key) == sig:
            continue  # already launched for this exact state
        if live:
            _delivery.foreign_controller_conflict()
            notification = _delivery.emit(wave_id=wave["wave_id"], scope=_delivery.scope_sha(wave, scoped),
                thread=n, recipient="coordinator", number=rnd["round"], status=rnd["status"],
                source=Path(_bridge.CHANNEL_DIR) / f"thread{n}.md")
            active = live_coordinator_run(n)
            if active:
                results.append({"thread": n, "reason": reason, "skipped": f"live coordinator: {active}; notification queued, read pending",
                                "notification": str(notification),
                                "launch": {"refused": "single-flight guard"}})
                continue
        rec = invoke(n, reason, wave, dry_run=not live, live_authorized=live,
                     notification=notification if live else None)
        results.append(rec)
        if live and rec.get("launch", {}).get("window_id"):
            cursor[key] = sig
    if live:
        live_set = {str(n) for n, _ in _bridge._thread_files()}
        cursor = {k: v for k, v in cursor.items() if k in live_set}
        _save_cursor(cursor)
    _d.write_status(
        NAME, state="running", path_mode=("live" if live else "preview"), live=live,
        coordinator_gate="armed" if _json(LAUNCH_CFG, {}).get("auto_launch") == "authorized" else "off",
        wave=_wave.summary_line(wave),
        summary=(f"{len(results)} coordinator(s) {'launched' if live else 'previewed'} this tick"
                 if results else "no coordinator owed a launch this tick"),
    )
    return {"live": live, "results": results}


def tick(flag_set: bool, *, reset: bool = False) -> dict:
    if gate_open(flag_set):
        try:
            with _launch_guard():
                return _tick_once(flag_set, reset=reset)
        except BlockingIOError:
            return {"live": True, "results": [], "busy": True}
    return _tick_once(flag_set, reset=reset)


def _save_cursor(cursor: dict) -> None:
    os.makedirs(VAR_DIR, exist_ok=True)
    tmp = CURSOR_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cursor, fh, indent=2)
    os.replace(tmp, CURSOR_PATH)


def _print(res: dict) -> None:
    mode = "LIVE" if res["live"] else "PREVIEW — launches nothing"
    print(f"=== coordinator trigger ({mode}) {_d.utc()} ===")
    if not res["results"]:
        print("  no coordinator owed a launch.")
    for r in res["results"]:
        launch = r.get("launch", {})
        where = launch.get("window_id") or launch.get("note") or launch.get("refused") or "(no launch)"
        print(f"  Thread {r['thread']} [{r.get('executor','existing')}/{r.get('model','owner')}] — {r['reason']['trigger']} -> "
              f"{'LAUNCHED' if res['live'] else 'preview'} [{launch.get('title','')}] {where}")


def watch(interval: float, flag_set: bool, *, reset: bool) -> int:
    mode = "LIVE" if gate_open(flag_set) else "PREVIEW (gate not armed)"
    print(f"[{NAME}] watch mode [{mode}], interval={interval}s. Ctrl-C to stop.", flush=True)
    first = reset
    try:
        while True:
            res = tick(flag_set, reset=first)
            first = False
            _print(res)
            time.sleep(max(5, interval))
    except KeyboardInterrupt:
        print(f"\n[{NAME}] stopped.")
        return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Launch thread coordinators launch-and-stop (gated).")
    ap.add_argument("--watch", action="store_true", help="run continuously (daemon mode)")
    ap.add_argument("--delivery-only", action="store_true", help="queue scoped file events; never launch actors")
    ap.add_argument("--once", action="store_true", help="single tick and exit (default)")
    ap.add_argument("--preview", type=int, metavar="THREAD",
                    help="build+print the coordinator launch for one thread; launch nothing")
    ap.add_argument("--interval", type=float, default=30.0)
    ap.add_argument("--reset", action="store_true", help="ignore the dedup cursor")
    ap.add_argument("--i-have-authorized-coordinator-autolaunch", dest="flag", action="store_true",
                    help="gate 2 of 2 for a LIVE coordinator launch (config is gate 1)")
    a = ap.parse_args(argv)

    if a.delivery_only:
        if a.flag or a.reset or a.preview is not None:
            ap.error('delivery-only cannot be combined with launch/reset options')
        if a.watch:
            _delivery.watch_delivery('coordinator', a.interval)
        else:
            print(json.dumps(_delivery.delivery_only_tick('coordinator'), indent=2))
        return 0

    if a.preview is not None:
        wave = _wave.active_wave()
        reason = owed(a.preview, wave) or {"thread": a.preview, "trigger": "manual preview (not currently owed)",
                                           "round": {}}
        rec = invoke(a.preview, reason, wave, dry_run=True)
        print(json.dumps(rec, indent=2))
        return 0
    if a.watch:
        return watch(a.interval, a.flag, reset=a.reset)
    res = tick(a.flag, reset=a.reset)
    _print(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
