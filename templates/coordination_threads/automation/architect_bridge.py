#!/usr/bin/env python3
"""
architect_bridge.py — Coordinator <-> Architect channel bridge (Stage-1 safe).

Watches coordination-threads/coordinator-architect/thread<n>.md for alignment rounds and,
when a round is AWAITING-ARCHITECT, surfaces the founder-relay ping:

    Discuss Thread<n>

That is the entire job of the DEFAULT (notify) mode: detect that a coordinator owes the
architect a response, and print the one-word relay the founder carries to the architect
conversation. It writes nothing into the channel files. Its only writes are its own dedup
cursors (var/architect_bridge.cursor.json for notify pings; var/architect_bridge.auto.cursor.json
for the --auto path -- kept separate so a ping never deduplicates a later live launch, and a
preview never consumes a round), mirroring monitor.py.

The AUTO write-back path (the Solution Architect writing the ARCHITECT block itself, so a
continuously-running coordinator proceeds with no founder relay) is now WIRED to
`architect_invoke.py` but stays HARD-DISABLED behind a dual gate -- a config flag AND an
explicit authorize flag -- exactly like supervisor.py --dispatch. Wiring the invocation did
NOT enable that path: without the config gate, --auto only PREVIEWS (launches nothing), and
--preview-invoke always previews. The live launch opens a visible, watchable Terminal window
(like a worker), never a hidden process.

Usage:
    python3 architect_bridge.py                 # one-shot scan: table of each thread's latest round + status
    python3 architect_bridge.py --notify        # one-shot: emit `Discuss Thread<n>` for each AWAITING round (dedup via cursor)
    python3 architect_bridge.py --watch          # continuous notify loop (default interval 30s), Ctrl-C to stop
    python3 architect_bridge.py --watch --interval 60
    python3 architect_bridge.py --reset          # ignore prior cursor (re-emit everything owed)
    python3 architect_bridge.py --json           # raw per-thread state (for a dashboard)
    python3 architect_bridge.py --preview-invoke <n>  # show the exact architect launch for thread n; launch nothing
    python3 architect_bridge.py --auto           # invoke the architect for every owed round -- LIVE only if dual-gated, else previews
    python3 architect_bridge.py --watch --auto   # continuous: detect AWAITING-ARCHITECT and invoke (live only if gated)

No secrets are read or written. This is a channel bridge, not an authorization path; it
grants nothing. Status authority remains execution_plan.md; Thread 1 remains sole canonical writer.
"""

import argparse
import datetime as _dt
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CHANNEL_DIR = os.path.normpath(os.path.join(HERE, "..", "coordinator-architect"))
VAR_DIR = os.path.join(HERE, "var")
CURSOR = os.path.join(VAR_DIR, "architect_bridge.cursor.json")
# The --auto write-back path keeps its OWN dedup cursor, separate from the notify
# (Easy-Mode ping) cursor above, so a `Discuss Thread<n>` ping never makes a later
# live --auto think the round is already handled, and vice versa.
AUTO_CURSOR = os.path.join(VAR_DIR, "architect_bridge.auto.cursor.json")

# A round machine-comment line, e.g.:
#   <!-- round:1 checkpoint:post status:AWAITING-ARCHITECT opened:2026-10-27T05:10Z -->
_ROUND_RE = re.compile(r"<!--\s*round:(\d+)\s+checkpoint:([A-Za-z0-9_-]+)\s+status:([A-Za-z\-]+)")

AWAITING = "AWAITING-ARCHITECT"
ARCHITECT_VERDICTS = {"ALIGNED", "REDIRECT", "HOLD", "ESCALATE"}
GREEN = "GREEN"


def _now():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _thread_files():
    if not os.path.isdir(CHANNEL_DIR):
        return []
    out = []
    for name in sorted(os.listdir(CHANNEL_DIR)):
        m = re.fullmatch(r"thread(\d+)\.md", name)
        if m:
            out.append((int(m.group(1)), os.path.join(CHANNEL_DIR, name)))
    return out


def _latest_round(path):
    """Return the highest-numbered round's (round, checkpoint, status) or None."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    best = None
    for m in _ROUND_RE.finditer(text):
        rnd = int(m.group(1))
        rec = {"round": rnd, "checkpoint": m.group(2), "status": m.group(3)}
        end = text.find("-->", m.end())
        if end != -1:
            bootstrap = re.search(r"\bbootstrap:wave:([A-Za-z0-9_-]+)\b", text[m.start():end])
            if bootstrap:
                rec["bootstrap_wave"] = bootstrap.group(1)
        if best is None or rnd > best["round"]:
            best = rec
    return best


def scan():
    rows = []
    for n, path in _thread_files():
        latest = _latest_round(path)
        rows.append({"thread": n, "file": os.path.basename(path), "latest": latest})
    return rows


def _load_cursor(path=CURSOR):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _save_cursor(data, path=CURSOR):
    os.makedirs(VAR_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, path)


def _owed(latest):
    """A round owes the architect a response iff its latest round is AWAITING-ARCHITECT."""
    return bool(latest and latest.get("status") == AWAITING)


def print_table(rows):
    print(f"=== Coordinator <-> Architect channel  ({_now()}) ===")
    print(f"channel: {CHANNEL_DIR}")
    if not rows:
        print("  (no thread<n>.md files yet)")
        return
    owed = []
    for r in rows:
        latest = r["latest"]
        if not latest:
            desc = "no rounds / placeholder"
        else:
            desc = f"round {latest['round']} [{latest['checkpoint']}] -> {latest['status']}"
        flag = ""
        if _owed(latest):
            flag = "   <-- OWES ARCHITECT"
            owed.append(r["thread"])
        print(f"  Thread {r['thread']}: {desc}{flag}")
    print("-" * 60)
    if owed:
        print("Founder relay — type each of these to the architect conversation:")
        for n in owed:
            print(f"    Discuss Thread{n}")
    else:
        print("Nothing owed to the architect. All rounds aligned/green or parked.")


def notify(reset=False):
    """Emit `Discuss Thread<n>` for every thread that owes the architect, deduped via cursor."""
    rows = scan()
    cursor = {} if reset else _load_cursor()
    emitted = []
    for r in rows:
        latest = r["latest"]
        if not _owed(latest):
            continue
        key = str(r["thread"])
        sig = f"{latest['round']}:{latest['status']}"
        if cursor.get(key) == sig:
            continue  # already pinged for this exact round/status
        emitted.append(r["thread"])
        cursor[key] = sig
    for n in emitted:
        print(f"Discuss Thread{n}")
        _macos_banner(f"Discuss Thread{n}")
    if not reset:
        # keep cursor entries only for threads that still exist
        live = {str(r["thread"]) for r in rows}
        cursor = {k: v for k, v in cursor.items() if k in live}
    _save_cursor(cursor)
    return emitted


def _macos_banner(msg):
    """Best-effort desktop notification on macOS; silent no-op elsewhere/on failure."""
    if sys.platform != "darwin":
        return
    try:
        import subprocess
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{msg}" with title "Coordinator channel"'],
            check=False, capture_output=True, timeout=5,
        )
    except Exception:
        pass


def _heartbeat(path_mode, summary, *, live=False):
    """Best-effort daemon heartbeat for the supervisor/dashboard; never fatal if daemon.py absent.

    Stamps this daemon's OWN effective path (`path_mode`) and whether it is actually launching
    the architect live (`live`). The global runtime mode is computed centrally from these flags
    (daemon.runtime_mode), so we never stamp a global mode word here that could go stale/misleading.
    """
    try:
        import daemon as _d
        _d.write_status("architect_bridge", state="running",
                        path_mode=path_mode, live=bool(live), summary=summary)
    except Exception:
        pass


def watch(interval, reset=False):
    print(f"[architect_bridge] watch mode, interval={interval}s. Ctrl-C to stop.")
    first = reset
    try:
        while True:
            got = notify(reset=first)
            first = False
            if not got:
                # quiet tick; a timestamp line keeps the watcher legible
                print(f"[{_now()}] nothing owed.", flush=True)
                _heartbeat("notify", "no thread owes the architect", live=False)
            else:
                line = ', '.join('Thread%d' % n for n in got)
                print(f"[{_now()}] pinged: {line}", flush=True)
                _heartbeat("notify", f"pinged: {line}", live=False)
            time.sleep(max(5, interval))
    except KeyboardInterrupt:
        print("\n[architect_bridge] stopped.")


def watch_auto(interval, flag_set, *, model="opus", reset=False):
    """Continuous detect-and-invoke loop: the software-factory path. Each tick scans the channel
    and, for any newly-owed round, invokes the Solution Architect (LIVE only if dual-gated, else a
    preview). This is the auto counterpart of watch(); it replaces the founder relay on the happy
    path and leaves only ESCALATE for the human."""
    mode = "LIVE" if _gates_open(flag_set) else "PREVIEW (dual-gate not set)"
    print(f"[architect_bridge] watch+auto mode [{mode}], interval={interval}s. Ctrl-C to stop.")
    first = reset
    try:
        while True:
            res = auto_invoke_owed(flag_set, model=model, reset=first)
            first = False
            n = len([r for r in res if not r.get("skipped")])
            live = _gates_open(flag_set)
            _heartbeat("auto-live" if live else "auto-preview",
                       f"{n} architect launch(es) this tick" if n else "no owed round this tick",
                       live=live)
            time.sleep(max(5, interval))
    except KeyboardInterrupt:
        print("\n[architect_bridge] stopped.")


# --------------------------------------------------------------------------- #
#  AUTO write-back path -- HARD-DISABLED (dual-gated, like supervisor dispatch)
# --------------------------------------------------------------------------- #
def _auto_enabled():
    """
    Two independent gates, both required, neither set here:
      1. config:  automation/config/architect_bridge.json -> {"auto_writeback": "authorized"}
      2. flag:    --i-have-wired-and-authorized-architect-autowrite
    Even with both, a real headless-architect invocation that writes the ARCHITECT block
    must be wired and reviewed first. This function only reports the gate state.
    """
    cfg_path = os.path.join(HERE, "config", "architect_bridge.json")
    cfg_ok = False
    try:
        with open(cfg_path, "r", encoding="utf-8") as fh:
            cfg_ok = json.load(fh).get("auto_writeback") == "authorized"
    except (OSError, ValueError):
        cfg_ok = False
    return cfg_ok


def _gates_open(flag_set):
    """Live auto write-back requires BOTH gates. Gate 3 (invocation) is now wired."""
    return _auto_enabled() and flag_set


def auto_invoke_owed(flag_set, *, model="opus", reset=False):
    """For every thread that owes the architect, invoke the Solution Architect.

    LIVE (opens a visible window) only when both gates are open; otherwise every invocation is
    a dry-run PREVIEW that launches nothing. Deduped via the same cursor as notify(), so a
    standing round is invoked once, not every tick. The launched architect writes the ARCHITECT
    block itself; this function writes nothing into the channel.
    """
    import architect_invoke as _ai  # local import avoids a circular import at module load

    live = _gates_open(flag_set)
    rows = scan()
    # The auto path has its own cursor, and a PREVIEW never consumes a round: dedup only
    # tracks rounds we actually LAUNCHED live. So any number of previews can run first and
    # the first live --auto still fires for every owed round.
    cursor = {} if reset else _load_cursor(AUTO_CURSOR)
    results = []
    for r in rows:
        latest = r["latest"]
        if not _owed(latest):
            continue
        key = str(r["thread"])
        sig = f"{latest['round']}:{latest['status']}"
        if live and cursor.get(key) == sig:
            continue  # already LAUNCHED for this exact round
        rec = _ai.invoke(r["thread"], dry_run=not live, model=model)
        results.append(rec)
        if live and rec.get("launch", {}).get("window_id"):
            cursor[key] = sig
    if live:
        live_set = {str(r["thread"]) for r in rows}
        cursor = {k: v for k, v in cursor.items() if k in live_set}
        _save_cursor(cursor, AUTO_CURSOR)

    print(f"=== architect auto-invoke ({'LIVE' if live else 'PREVIEW — launches nothing'}) {_now()} ===")
    if not live:
        print("  gate 1 (config auto_writeback=authorized): "
              + ("SET" if _auto_enabled() else "not set"))
        print("  gate 2 (--i-have-wired-and-authorized-architect-autowrite): "
              + ("SET" if flag_set else "not set"))
        print("  gate 3 (architect invocation wired): WIRED (architect_invoke.py)")
        print("  -> both gates required for a live launch; previewing instead.")
    if not results:
        if live:
            print("  nothing owed (every owed round already launched this cursor; --reset to re-launch).")
        else:
            print("  nothing owed — no thread is AWAITING-ARCHITECT.")
    for rec in results:
        t = rec.get("thread")
        if rec.get("skipped"):
            print(f"  Thread {t}: {rec['skipped']}")
            continue
        launch = rec.get("launch", {})
        where = launch.get("window_id") or launch.get("note") or launch.get("refused") or "(no launch)"
        print(f"  Thread {t}: round {rec['round']['round']} -> architect {'LAUNCHED' if live else 'preview'} "
              f"[{launch.get('title','')}] {where}")
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description="Coordinator<->Architect channel bridge (Stage-1 safe).")
    p.add_argument("--notify", action="store_true", help="one-shot: emit `Discuss Thread<n>` for owed rounds")
    p.add_argument("--watch", action="store_true", help="continuous notify loop")
    p.add_argument("--interval", type=int, default=30, help="watch interval seconds (min 5)")
    p.add_argument("--reset", action="store_true", help="ignore prior cursor")
    p.add_argument("--json", action="store_true", help="raw per-thread state")
    p.add_argument("--auto", action="store_true",
                   help="invoke the architect for every owed round (LIVE only if dual-gated, else previews)")
    p.add_argument("--preview-invoke", type=int, metavar="THREAD",
                   help="show the exact architect launch for one thread; launch nothing")
    p.add_argument("--model", default="opus", help="claude model for the invoked architect (default opus)")
    p.add_argument("--i-have-wired-and-authorized-architect-autowrite",
                   dest="auto_flag", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args(argv)

    if args.preview_invoke is not None:
        import architect_invoke as _ai
        print(json.dumps(_ai.invoke(args.preview_invoke, dry_run=True, model=args.model), indent=2))
        return 0
    if args.json:
        print(json.dumps(scan(), indent=2))
        return 0
    if args.watch:
        if args.auto:
            watch_auto(args.interval, args.auto_flag, model=args.model, reset=args.reset)
        else:
            watch(args.interval, reset=args.reset)
        return 0
    if args.auto:
        auto_invoke_owed(args.auto_flag, model=args.model, reset=args.reset)
        return 0
    if args.notify:
        emitted = notify(reset=args.reset)
        if not emitted:
            print("Nothing owed to the architect.")
        return 0
    print_table(scan())
    return 0


if __name__ == "__main__":
    sys.exit(main())
