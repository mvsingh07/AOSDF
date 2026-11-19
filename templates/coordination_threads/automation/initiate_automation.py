#!/usr/bin/env python3
"""initiate_automation.py — start, supervise and show the automation runtime (the one entry point).

This is the single script the founder runs to bring the whole "factory" up and watch it. It manages
a set of cheap, always-on Python TRIGGER daemons (the nervous system). Those daemons detect owed work
and SUMMON short-lived, billed AGENT sessions (Solution Architect, thread coordinators, workers) in
visible, watchable windows that do a bounded unit and exit — see coordinator_trigger.py /
architect_bridge.py / supervisor.py. The agents are not daemons; the daemons are.

Managed daemons:
  * architect_bridge     — detect AWAITING-ARCHITECT rounds -> ping (safe) or invoke architect (armed)
  * coordinator_trigger  — detect a coordinator owed a launch -> preview (safe) or launch it (armed)
  * manual_detector      — detect manual actions -> notify founder / Slack (armed: gated auto-exec)

Two operating modes for the whole set:
  * SAFE (default)  — daemons run in notify/preview only; they open NO agent window and change nothing.
                      This is Easy-Mode-automated: the detectors still tell you what is owed.
  * ARMED (--arm)   — daemons pass their live flags. Each live launch is STILL independently gated by
                      its own config file (architect_bridge.json / coordinator_launch.json /
                      manual_exec.json); --arm only adds the second (flag) gate. With a config gate off,
                      that daemon keeps previewing even when armed. So --arm never bypasses a gate.

Commands:
    python3 initiate_automation.py                 # interactive (at a TTY): check the wave, ask what to
                                                   #   scope, and launch the Solution Architect — one command,
                                                   #   both cases (active wave -> continue; none -> define).
                                                   #   After a real launch it STAYS ATTACHED, repainting the live
                                                   #   dashboard (agents dispatched / active / inactive + status)
                                                   #   until Ctrl-C; detaching leaves the agents running.
                                                   #   Piped/non-interactive, it prints a status snapshot instead.
    python3 initiate_automation.py --begin          # force the interactive begin flow (same stay-attached follow)
    python3 initiate_automation.py --status         # one status snapshot (no prompts) + MODE + wave + dispatches
    python3 initiate_automation.py --watch          # repainting dashboard (blocks per daemon), Ctrl-C to stop
    python3 initiate_automation.py --start          # start any daemon not running (SAFE)
    python3 initiate_automation.py --start --arm     # start the set ARMED (live launches, still per-daemon gated)
    python3 initiate_automation.py --stop            # stop all managed daemons
    python3 initiate_automation.py --restart [--arm] # stop then start

Stdlib-only. The launcher writes only under var/daemons/ (pidfiles, logs). It starts each daemon in
its own session (setsid) so the daemons survive this launcher exiting; it grants no authorization.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import re                       # noqa: E402
import daemon as _d             # noqa: E402
import wave as _wave            # noqa: E402
import notify as _notify        # noqa: E402
import architect_invoke as _ai  # noqa: E402

THREADS_DIR = os.path.normpath(os.path.join(HERE, os.pardir))
SPRINT_TRACKER = os.path.join(THREADS_DIR, "SPRINT-TRACKER.md")
VAR_DIR = os.path.join(HERE, "var")
# Agent sessions open visible windows and are recorded as run dirs holding launch.json under these
# roots. We read them directly (not just daemon heartbeats) so the dashboard shows dispatched agents
# even when the trigger daemons are not running.
AGENT_RUN_ROOTS = (
    ("architect-runs", "architect"),
    ("coordinator-runs", "coordinator"),
)

PY = sys.executable or "python3"

DAEMONS = [
    {
        "name": "architect_bridge",
        "script": "architect_bridge.py",
        "safe": ["--watch"],
        "armed": ["--watch", "--auto", "--i-have-wired-and-authorized-architect-autowrite"],
        "desc": "architect write-back trigger",
    },
    {
        "name": "coordinator_trigger",
        "script": "coordinator_trigger.py",
        "safe": ["--watch"],
        "armed": ["--watch", "--i-have-authorized-coordinator-autolaunch"],
        "desc": "coordinator launch-and-stop trigger",
    },
    {
        "name": "manual_detector",
        "script": "manual_detector.py",
        "safe": ["--watch"],
        "armed": ["--watch", "--live-exec"],
        "desc": "manual-action router (Slack/notify)",
    },
]


def _pidfile(name: str) -> str:
    return os.path.join(_d.DAEMON_DIR, f"{name}.pid")


def _logfile(name: str) -> str:
    return os.path.join(_d.DAEMON_DIR, f"{name}.log")


def _read_pid(name: str) -> int | None:
    try:
        with open(_pidfile(name), "r", encoding="utf-8") as fh:
            return int(fh.read().strip())
    except (OSError, ValueError):
        return None


def _running_pid(name: str) -> int | None:
    pid = _read_pid(name)
    return pid if _d.pid_alive(pid) else None


def start_one(spec: dict, armed: bool, interval: float) -> dict:
    name = spec["name"]
    existing = _running_pid(name)
    if existing:
        return {"name": name, "action": "already-running", "pid": existing}
    os.makedirs(_d.DAEMON_DIR, exist_ok=True)
    # Integer-format the interval: architect_bridge's --interval is type=int (rejects "30.0");
    # the float-typed daemons accept the integer string equally. Watch loops are second-granularity.
    flags = list(spec["armed"] if armed else spec["safe"]) + ["--interval", str(int(interval))]
    argv = [PY, os.path.join(HERE, spec["script"]), *flags]
    log = open(_logfile(name), "a", encoding="utf-8")  # noqa: SIM115 (handed to the child)
    log.write(f"\n==== start {_d.utc()} armed={armed} argv={' '.join(flags)} ====\n")
    log.flush()
    proc = subprocess.Popen(
        argv, cwd=HERE, stdout=log, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, start_new_session=True,
    )
    with open(_pidfile(name), "w", encoding="utf-8") as fh:
        fh.write(str(proc.pid))
    return {"name": name, "action": "started", "pid": proc.pid, "armed": armed}


def stop_one(spec_or_name) -> dict:
    name = spec_or_name["name"] if isinstance(spec_or_name, dict) else spec_or_name
    pid = _running_pid(name)
    if not pid:
        # clean a stale pidfile if present
        try:
            os.remove(_pidfile(name))
        except OSError:
            pass
        return {"name": name, "action": "not-running"}
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except (OSError, ProcessLookupError):
        _d.stop_pid(pid)
    # give it a moment, then clean up
    for _ in range(10):
        if not _d.pid_alive(pid):
            break
        time.sleep(0.2)
    try:
        os.remove(_pidfile(name))
    except OSError:
        pass
    return {"name": name, "action": "stopped", "pid": pid}


def cmd_start(armed: bool, interval: float) -> int:
    print(f"Starting automation runtime — {'ARMED (live, per-daemon gated)' if armed else 'SAFE (notify/preview)'}")
    for spec in DAEMONS:
        r = start_one(spec, armed, interval)
        print(f"  {r['name']:<20} {r['action']}" + (f" (pid {r['pid']})" if r.get('pid') else ""))
    print()
    render_once()
    return 0


def cmd_stop() -> int:
    print("Stopping automation runtime…")
    for spec in DAEMONS:
        r = stop_one(spec)
        print(f"  {r['name']:<20} {r['action']}" + (f" (pid {r['pid']})" if r.get('pid') else ""))
    return 0


# --------------------------------------------------------------------------- #
#  Rendering — functional block/table view (appearance refinable later).
# --------------------------------------------------------------------------- #
def _fmt_age(sec) -> str:
    if sec is None:
        return "—"
    if sec < 90:
        return f"{int(sec)}s"
    if sec < 5400:
        return f"{int(sec/60)}m"
    return f"{int(sec/3600)}h"


def _status_rows() -> list[dict]:
    rows = []
    status_by_name = {s.get("name"): s for s in _d.read_all_status()}
    for spec in DAEMONS:
        name = spec["name"]
        pid = _running_pid(name)
        st = status_by_name.get(name, {})
        age = _d.age_seconds(st.get("ts"))
        # alive = pid running AND heartbeat fresh (< 5 min)
        fresh = age is not None and age < 300
        if pid and fresh:
            health = "● up"
        elif pid:
            health = "◐ stale"
        else:
            health = "○ down"
        rows.append({
            "name": name, "desc": spec["desc"], "pid": pid or "—", "health": health,
            "hb_mode": st.get("path_mode") or st.get("mode") or "—",
            "age": _fmt_age(age), "summary": st.get("summary", ""),
        })
    return rows


def _age_of(ts: str | None) -> float | None:
    """Seconds since an ISO timestamp, tolerating both the `...Z` and `+00:00` forms agents write."""
    if not ts:
        return None
    import datetime as _dt
    try:
        then = _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if then.tzinfo is None:
            then = then.replace(tzinfo=_dt.timezone.utc)
    except (ValueError, TypeError):
        return None
    return (_dt.datetime.now(_dt.timezone.utc) - then).total_seconds()


def _json_load(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _ps_commands() -> str:
    """One snapshot of running process command lines; '' if ps is unavailable."""
    try:
        return subprocess.run(["ps", "-axo", "command="], capture_output=True,
                              text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def _run_is_live(run_dir: str, ps_out: str) -> bool:
    """Is the agent session in this run dir still running?

    A recorded pid (coordinator/architect windows write coordinator.pid) is the strongest signal.
    Otherwise every visible window runs `script -F <run_dir>/terminal.log` (or tee's to it), so a
    live process whose command line still names that log path means the window is open.
    """
    try:
        with open(os.path.join(run_dir, "coordinator.pid"), "r", encoding="utf-8") as fh:
            return _d.pid_alive(int(fh.read().strip()))
    except (OSError, ValueError):
        pass
    tlog = os.path.join(run_dir, "terminal.log")
    return bool(ps_out) and tlog in ps_out


def _scan_dispatches() -> list[dict]:
    """Every real (non-preview) agent window ever opened, newest first, each tagged live/exited."""
    ps_out = _ps_commands()
    rows: list[dict] = []
    for sub, kind in AGENT_RUN_ROOTS:
        root = os.path.join(VAR_DIR, sub)
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            if "launch.json" not in files:
                continue
            lj = _json_load(os.path.join(dirpath, "launch.json"), {})
            if lj.get("dry_run"):
                continue  # preview only — never a real dispatch
            opened = bool(lj.get("window_id")) or os.path.exists(os.path.join(dirpath, ".launcher-once"))
            if not opened:
                continue
            m = re.search(r"thread(\d+)", dirpath)
            rows.append({
                "kind": kind,
                "thread": int(m.group(1)) if m else None,
                "sig": os.path.basename(dirpath),
                "executor": lj.get("executor", ""),
                "title": lj.get("title", ""),
                "created": lj.get("created_utc", ""),
                "live": _run_is_live(dirpath, ps_out),
            })
    rows.sort(key=lambda r: r.get("created") or "", reverse=True)
    return rows


def _dispatch_summary(rows: list[dict]) -> dict:
    total = len(rows)
    active = sum(1 for r in rows if r["live"])
    by_thread: dict = {}
    for r in rows:
        key = f"T{r['thread']}" if r["thread"] else (r["kind"][:4] or "—")
        agg = by_thread.setdefault(key, {"total": 0, "active": 0})
        agg["total"] += 1
        agg["active"] += 1 if r["live"] else 0
    return {"total": total, "active": active, "inactive": total - active, "by_thread": by_thread}


def render_dispatches(max_rows: int = 8) -> None:
    rows = _scan_dispatches()
    s = _dispatch_summary(rows)
    bar = "═" * 78
    per = "  ".join(f"{k}: {v['active']}/{v['total']} live" for k, v in sorted(s["by_thread"].items()))
    print(f" dispatched agents: {s['total']} total — {s['active']} active, {s['inactive']} inactive"
          + (f"   [{per}]" if per else ""))
    if not rows:
        print("   (no agent windows dispatched yet — the architect/coordinators open here when summoned)")
        return
    print(" " + "-" * 76)
    print(f" {'state':<9}{'thread':<8}{'role':<13}{'who':<8}{'session':<22}age")
    for r in rows[:max_rows]:
        health = "● live" if r["live"] else "○ exited"
        th = f"T{r['thread']}" if r["thread"] else "—"
        age = _fmt_age(_age_of(r["created"])) if r["created"] else "—"
        print(f" {health:<9}{th:<8}{r['kind']:<13}{(r['executor'] or '—')[:7]:<8}{r['sig'][:21]:<22}{age}")
    if len(rows) > max_rows:
        print(f"   …and {len(rows) - max_rows} more (older, exited).")
    _ = bar


def render_once() -> None:
    md = _d.mode_detail()
    wave = _wave.active_wave()
    bar = "═" * 78
    print(bar)
    print(f" SUPAGRAM AUTOMATION   mode: {md['mode']:<10}  ({md['detail']})")
    print(f" gates: architect {md['architect_gate']:<5} coordinator {md['coordinator_gate']:<5} "
          f"worker {md['worker_gate']:<5}  (a gate is 'armed' config only — mode shows what is LIVE)")
    print(f" wave: {_wave.summary_line(wave)}")
    print(f" slack: {'configured' if _notify.slack_configured() else 'fallback (macOS banner / stdout)'}")
    print(bar)
    print(f" {'daemon':<20}{'health':<9}{'pid':<8}{'path':<13}{'hb':<6}summary")
    print(" " + "-" * 76)
    for r in _status_rows():
        print(f" {r['name']:<20}{r['health']:<9}{str(r['pid']):<8}{r['hb_mode']:<13}{r['age']:<6}{r['summary'][:34]}")
    print(bar)
    render_dispatches()
    print(bar)
    print(" (SAFE = detectors only, no agent windows. ARM with --start --arm; each live launch is still")
    print("  gated by its own config file. Agents open in their own visible windows when summoned.)")


def cmd_watch(interval: float) -> int:
    print("[initiate_automation] dashboard — Ctrl-C to stop (daemons keep running).", flush=True)
    try:
        while True:
            # clear screen for the repaint (fallback: just print a separator)
            sys.stdout.write("\033[2J\033[H")
            render_once()
            sys.stdout.flush()
            time.sleep(max(2, interval))
    except KeyboardInterrupt:
        print("\n[initiate_automation] dashboard closed; daemons still running "
              "(stop them with --stop).")
        return 0


# --------------------------------------------------------------------------- #
#  Single-command begin flow — read wave state, ask the right question, act.
#
#  Founder directive 2026-10-29: `python3 initiate_automation.py` should, in one command,
#  detect whether a wave is active and either (a) offer to continue it and launch the
#  Solution Architect, or (b) map the sprint-tracker's open sprints, ask which to scope
#  into the next wave, define it, and launch the architect. One command, both cases.
# --------------------------------------------------------------------------- #
_SPRINT_ROW = re.compile(r"^\|\s*\*{0,2}(S\d+)\b")
_STATUS_WORDS = ("Completed", "In progress", "Blocked", "Planned", "Pending", "Deferred")


def _clean(cell: str) -> str:
    return cell.replace("**", "").replace("·", " ").strip()


def _parse_sprint_rows() -> list[dict]:
    """Parse the SPRINT-TRACKER master list into {id,title,status,owner,thread,scope} rows."""
    rows = []
    try:
        with open(SPRINT_TRACKER, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return rows
    for ln in lines:
        if not _SPRINT_ROW.match(ln):
            continue
        cells = [c.strip() for c in ln.split("|")]
        # leading/trailing empties from the | splits: cells[1]=Sprint … cells[7]=Owner
        if len(cells) < 8:
            continue
        sprint_cell, desc_cell, status_cell, owner_cell = cells[1], cells[2], cells[6], cells[7]
        m = re.search(r"S(\d+)", sprint_cell)
        if not m:
            continue
        sid = f"S{m.group(1)}"
        # title = sprint cell up to the first ' · ' / backtick, minus the "S# — " prefix
        title = _clean(re.split(r"[·`]", sprint_cell)[0])
        title = re.sub(r"^S\d+\s*[—-]\s*", "", title).strip()
        status = next((w for w in _STATUS_WORDS if status_cell.startswith(w)), _clean(status_cell).split()[0] if status_cell else "?")
        owners = set(re.findall(r"\bT([1-9][0-9]*)\b", owner_cell))
        thread = int(next(iter(owners))) if len(owners) == 1 and "Founder" not in owner_cell else None
        scope = _clean(desc_cell)[:160]
        rows.append({"id": sid, "title": title, "status": status, "owner": _clean(owner_cell),
                     "thread": thread, "scope": scope})
    return rows


def _ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    try:
        resp = input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default or ""
    return resp or (default or "")


def _next_wave_id() -> str:
    w = _wave.load()
    if w:
        m = re.search(r"(\d+)$", str(w.get("wave_id", "")))
        if m:
            return f"W-{int(m.group(1)) + 1}"
    return "W-1"


def _launch_architect_for_wave(wave: dict, model: str, dry_run: bool) -> bool:
    """Launch (or preview) the wave's Solution Architect. Returns True iff a real window opened."""
    if _ask("Launch the Solution Architect to work this wave now? [Y/n]", "Y").lower().startswith("n"):
        print("  Not launching. The wave is saved; run this command again when ready.")
        return False
    rec = _ai.invoke_wave(wave, dry_run=dry_run, model=model)
    launch = rec.get("launch", {})
    where = launch.get("window_id") or launch.get("note") or launch.get("refused") or "(see run dir)"
    verb = "WOULD launch (dry-run)" if dry_run else "launched"
    print(f"  Solution Architect {verb}: {launch.get('title','')}  {where}")
    if not _d._fresh_status("coordinator_trigger"):
        print("  NOTE: the coordinator_trigger daemon is not running — start the set with "
              "`--start` so the rounds the architect opens get picked up (SAFE = preview; "
              "arm coordinator launch separately to auto-open coordinators).")
    return bool(launch.get("window_id")) and not dry_run


def _follow_after_launch(interval: float) -> None:
    """Stay attached after a real launch and keep repainting the live dashboard (founder directive
    2026-10-31: the launcher must not exit after starting the wave — it keeps reporting the agents
    dispatched / active / inactive and their status). Ctrl-C detaches; daemons/agents keep running."""
    print("\n  Launch is live. Holding the dashboard open — it will keep reporting the agents "
          "dispatched, active and inactive. Ctrl-C to detach (agents keep running).")
    try:
        time.sleep(1.5)
    except KeyboardInterrupt:
        return
    cmd_watch(interval)


def _begin_new(model: str, dry_run: bool, interval: float = 30.0) -> int:
    rows = _parse_sprint_rows()
    open_rows = [r for r in rows if r["status"] not in ("Completed", "Deferred")]
    if not rows:
        print("Could not read the sprint tracker; defining a wave by hand is still possible via "
              "`python3 wave.py define …`.")
        return 1
    print("No automation wave is active. Open sprints from SPRINT-TRACKER.md (candidates for a wave):\n")
    for i, r in enumerate(open_rows, 1):
        th = f"T{r['thread']}" if r["thread"] else r["owner"]
        print(f"  {i:>2}. {r['id']:<4} [{r['status']:<11}] ({th:<12}) {r['title']}")
    print("  (Completed/Deferred sprints are hidden. Blocked/Pending ones wait on a named gate —"
          " the architect will escalate if you scope one that cannot yet proceed.)\n")
    sel = _ask("Which sprints go into the next wave? comma list of numbers or S-ids (blank = cancel)")
    if not sel:
        print("Cancelled; no wave defined.")
        return 0
    chosen = _resolve_selection(sel, open_rows)
    if not chosen:
        print("Nothing matched; no wave defined.")
        return 1
    for r in chosen:
        if r["thread"] is not None:
            continue
        allowed = set(re.findall(r"\bT([1-9][0-9]*)\b", r["owner"]))
        answer = _ask(f"Lead coordinator for multi-owner {r['id']} ({r['owner']}); enter T number")
        if not answer.isdigit() or answer not in allowed:
            print(f"Cannot auto-route {r['id']}: choose a listed lead thread explicitly.")
            return 1
        r["thread"] = int(answer)
    print("\nScoping into the wave:")
    for r in chosen:
        print(f"  - {r['id']} (Thread {r['thread'] or '?'}): {r['title']}")
    wave_id = _ask("Wave id", _next_wave_id())
    title = _ask("Wave title", f"{chosen[0]['id']}–{chosen[-1]['id']} automation wave")
    objective = _ask("Objective (optional)", "")
    sprints = [{"id": r["id"], "thread": r["thread"],
                "scope": f"{r['title']} — {r['scope']}", "status": "pending"} for r in chosen]
    wave = _wave.define(wave_id=wave_id, title=title, objective=objective, sprints=sprints)
    _wave.save(wave)
    print(f"\nWave written: {_wave.WAVE_PATH}")
    print(f"  {_wave.summary_line(wave)}\n")
    if _launch_architect_for_wave(wave, model, dry_run):
        _follow_after_launch(interval)
    return 0


def _resolve_selection(sel: str, rows: list[dict]) -> list[dict]:
    chosen, seen = [], set()
    for tok in re.split(r"[,\s]+", sel.strip()):
        if not tok:
            continue
        r = None
        if tok.isdigit():
            idx = int(tok) - 1
            if 0 <= idx < len(rows):
                r = rows[idx]
        else:
            tok_id = tok.upper() if tok.upper().startswith("S") else f"S{tok}"
            r = next((x for x in rows if x["id"] == tok_id), None)
        if r and r["id"] not in seen:
            chosen.append(r)
            seen.add(r["id"])
    return chosen


def _begin_active(wave: dict, model: str, dry_run: bool, interval: float = 30.0) -> int:
    print(f"An automation wave is ACTIVE: {_wave.summary_line(wave)}\n")
    for s in wave.get("sprints", []):
        print(f"  - {s.get('id')} (Thread {s.get('thread','?')}, {s.get('status','pending')}): {s.get('scope','')}")
    print()
    ans = _ask("[C]ontinue advancing it / [P]ause / [R]edefine from the tracker / [Q]uit", "C").lower()
    if ans.startswith("q"):
        print("Left the wave untouched.")
        return 0
    if ans.startswith("p"):
        wave["status"] = "paused"
        wave["updated_utc"] = _wave._utc()
        _wave.save(wave)
        print(f"Wave paused: {_wave.summary_line(wave)}")
        return 0
    if ans.startswith("r"):
        if not _ask("Redefining overwrites the current wave. Continue? [y/N]", "N").lower().startswith("y"):
            print("Kept the current wave.")
            return 0
        return _begin_new(model, dry_run, interval)
    # continue
    if _launch_architect_for_wave(wave, model, dry_run):
        _follow_after_launch(interval)
    return 0


def begin(model: str = "opus", dry_run: bool = False, interval: float = 30.0) -> int:
    render_once()
    print()
    wave = _wave.load()
    if wave and wave.get("status") == "active":
        return _begin_active(wave, model, dry_run, interval)
    if wave and wave.get("status") == "paused":
        print(f"A wave is PAUSED: {_wave.summary_line(wave)}")
        if _ask("Resume it? [Y/n]", "Y").lower().startswith("n"):
            return _begin_new(model, dry_run, interval)
        wave["status"] = "active"
        wave["updated_utc"] = _wave._utc()
        _wave.save(wave)
        return _begin_active(wave, model, dry_run, interval)
    return _begin_new(model, dry_run, interval)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Start/supervise/show the Example Project automation runtime.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--start", action="store_true", help="start any daemon not running")
    g.add_argument("--stop", action="store_true", help="stop all managed daemons")
    g.add_argument("--restart", action="store_true", help="stop then start")
    g.add_argument("--watch", action="store_true", help="repainting dashboard (read-only)")
    g.add_argument("--begin", action="store_true",
                   help="interactive: check the wave, ask what to scope, launch the Solution Architect")
    g.add_argument("--status", action="store_true", help="one status snapshot (no prompts)")
    ap.add_argument("--arm", action="store_true",
                    help="start daemons with their live flags (each still gated by its own config file)")
    ap.add_argument("--interval", type=float, default=30.0, help="daemon tick interval seconds")
    ap.add_argument("--model", default="opus", help="model for a launched Solution Architect (default opus)")
    ap.add_argument("--dry-run-launch", action="store_true",
                    help="with --begin: define/choose the wave but PREVIEW the architect launch (open nothing)")
    a = ap.parse_args(argv)

    if a.stop:
        return cmd_stop()
    if a.restart:
        cmd_stop()
        time.sleep(1)
        return cmd_start(a.arm, a.interval)
    if a.start:
        return cmd_start(a.arm, a.interval)
    if a.watch:
        return cmd_watch(a.interval)
    if a.status:
        render_once()
        return 0
    if a.begin:
        return begin(model=a.model, dry_run=a.dry_run_launch, interval=a.interval)
    # default: interactive begin at a TTY; a plain status snapshot when piped/non-interactive.
    if sys.stdin.isatty():
        return begin(model=a.model, dry_run=a.dry_run_launch, interval=a.interval)
    render_once()
    return 0


if __name__ == "__main__":
    sys.exit(main())
