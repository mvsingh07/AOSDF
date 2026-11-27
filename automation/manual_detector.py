#!/usr/bin/env python3
"""manual_detector.py — watch for manual actions and route them.

Founder direction (2026-10-28): the manual-action thread can be operated by the Solution Architect
agent for actions WITHIN the model's permissions/scope; anything out of scope sends a notification
(Slack, else macOS banner) so the founder deals with it. A simple question/confirmation goes to
Slack and is answered there only.

So this daemon classifies each newly-seen manual action and routes it:
  * Class A  (in model scope: a local, reversible, non-secret/non-spend/non-publish step)
        -> AUTO-EXECUTE path. DUAL-GATED, OFF by default (observe-before-automating), exactly like
           the architect write-back and worker dispatch. Until armed, it PREVIEWS: it notifies
           "ready to auto-execute" and records the intent, launching nothing.
  * Class B/C (needs the human: a secret/credential, spend, publish/deploy, DNS, console access,
           a decision, or anything the model may not do) -> NOTIFY the founder (question/escalate).

Inputs it watches (whichever exist):
  1. var/manual-queue.json  — the clean contract other agents append to:
        [{"id":"MA-072","title":"...","klass":"A|B|C","needs":"secret|spend|console|decision|none",
          "status":"open"}]
  2. New files under coordination-threads/thread1/ and thread1/guides/ (a new guide == a manual
     action was just assigned to the founder) — surfaced as class-C notifications by default.

Dedup via var/manual_detector.cursor.json so each item is routed once. Writes a heartbeat to
var/daemons/manual_detector.json each tick. Stdlib-only; launches nothing live; grants nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
VAR_DIR = os.path.join(HERE, "var")
CONFIG_DIR = os.path.join(HERE, "config")
QUEUE_PATH = os.path.join(VAR_DIR, "manual-queue.json")
CURSOR_PATH = os.path.join(VAR_DIR, "manual_detector.cursor.json")
THREAD1_DIR = os.path.normpath(os.path.join(HERE, os.pardir, "thread1"))

import daemon as _d        # noqa: E402
import notify as _notify   # noqa: E402

NAME = "manual_detector"
AUTOEXEC_CFG = os.path.join(CONFIG_DIR, "manual_exec.json")


def _json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, path)


def autoexec_gate_open() -> bool:
    """Gate 1 for Class-A manual-action auto-execution (config leg). Off unless armed; the live
    executor also needs its own authorize flag (gate 2), identical to the architect/dispatch gates."""
    return _json(AUTOEXEC_CFG, {}).get("auto_execute") == "authorized"


def _load_queue() -> list[dict]:
    q = _json(QUEUE_PATH, [])
    return q if isinstance(q, list) else []


def _scan_thread1_files() -> list[dict]:
    """New guide/assignment files under thread1/ as class-C manual-action signals."""
    items = []
    for base in (THREAD1_DIR, os.path.join(THREAD1_DIR, "guides")):
        if not os.path.isdir(base):
            continue
        for fn in sorted(os.listdir(base)):
            if fn.endswith(".md"):
                rel = os.path.relpath(os.path.join(base, fn), THREAD1_DIR)
                items.append({"id": f"guide:{rel}", "title": fn, "klass": "C",
                              "needs": "founder", "status": "open", "source": "thread1"})
    return items


def _route(item: dict, *, live_exec: bool) -> dict:
    """Decide the route for one item and act (notify / preview-exec). Returns a record."""
    klass = (item.get("klass") or "C").upper()
    iid = item.get("id", "?")
    title = item.get("title", "")
    if klass == "A":
        if live_exec and autoexec_gate_open():
            # Live auto-execution of a manual action is itself an outward step: the executor
            # launch is intentionally NOT wired here (needs a founder pilot, like the architect
            # write-back was). Until that executor exists, arm-and-run still only notifies.
            _notify.notify(f"{iid}: {title} — Class A, auto-exec gate ARMED but executor not yet "
                           f"wired; leaving for review.", title="Manual action", level="action")
            return {"id": iid, "klass": klass, "route": "autoexec-armed-but-unwired"}
        _notify.notify(f"{iid}: {title} — Class A (in-scope). Ready to auto-execute once the "
                       f"manual-exec gate is armed and the executor is piloted.", title="Manual action",
                       level="action")
        return {"id": iid, "klass": klass, "route": "autoexec-preview"}
    # Class B / C -> the human.
    needs = item.get("needs", "founder")
    _notify.notify(f"{iid}: {title} — needs you ({needs}). Out of model scope.",
                   title="Manual action", level="escalate" if klass == "C" else "question")
    return {"id": iid, "klass": klass, "route": "notify-founder", "needs": needs}


def tick(*, reset: bool = False, live_exec: bool = False, scan_thread1: bool = False) -> dict:
    cursor = {} if reset else _json(CURSOR_PATH, {})
    # Default input is the explicit queue (var/manual-queue.json), which is empty until an agent
    # appends an action -> zero noise on startup. The thread1/ doc scan is opt-in (--scan-thread1):
    # it treats every guide/context .md as a class-C signal, which is far too broad for a default.
    items = _load_queue()
    if scan_thread1:
        items += _scan_thread1_files()
    routed = []
    for item in items:
        iid = item.get("id")
        if not iid:
            continue
        sig = f"{item.get('status','open')}:{item.get('klass','C')}"
        if cursor.get(iid) == sig:
            continue  # already routed for this exact state
        routed.append(_route(item, live_exec=live_exec))
        cursor[iid] = sig
    # prune cursor to items we still see
    live_ids = {i.get("id") for i in items if i.get("id")}
    cursor = {k: v for k, v in cursor.items() if k in live_ids}
    _save_json(CURSOR_PATH, cursor)
    counts = {
        "seen": len(items),
        "routed_now": len(routed),
        "to_founder": sum(1 for r in routed if r["route"] == "notify-founder"),
        "class_a": sum(1 for r in routed if r["klass"] == "A"),
    }
    _d.write_status(
        NAME, state="running", path_mode=("auto-exec" if live_exec and autoexec_gate_open() else "notify"),
        live=bool(live_exec and autoexec_gate_open()),
        autoexec_gate="armed" if autoexec_gate_open() else "off",
        slack="configured" if _notify.slack_configured() else "fallback(macos/stdout)",
        summary=f"{counts['seen']} actions seen; {counts['routed_now']} routed this tick "
                f"({counts['to_founder']} to founder)",
        counts=counts,
    )
    return {"routed": routed, "counts": counts}


def watch(interval: float, *, reset: bool, live_exec: bool, scan_thread1: bool) -> int:
    print(f"[{NAME}] watch mode, interval={interval}s. Ctrl-C to stop.", flush=True)
    first = reset
    try:
        while True:
            res = tick(reset=first, live_exec=live_exec, scan_thread1=scan_thread1)
            first = False
            c = res["counts"]
            print(f"[{_d.utc()}] seen={c['seen']} routed={c['routed_now']} "
                  f"to_founder={c['to_founder']}", flush=True)
            time.sleep(max(5, interval))
    except KeyboardInterrupt:
        print(f"\n[{NAME}] stopped.")
        return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Watch for manual actions and route them (notify / gated auto-exec).")
    ap.add_argument("--watch", action="store_true", help="run continuously (daemon mode)")
    ap.add_argument("--once", action="store_true", help="single tick and exit")
    ap.add_argument("--interval", type=float, default=30.0)
    ap.add_argument("--reset", action="store_true", help="ignore the dedup cursor (re-route everything open)")
    ap.add_argument("--live-exec", action="store_true",
                    help="attempt the Class-A auto-exec path (still gated by config/manual_exec.json)")
    ap.add_argument("--scan-thread1", action="store_true",
                    help="also treat new thread1/ guide .md files as class-C signals (noisy; off by default)")
    a = ap.parse_args(argv)
    if a.watch:
        return watch(a.interval, reset=a.reset, live_exec=a.live_exec, scan_thread1=a.scan_thread1)
    res = tick(reset=a.reset, live_exec=a.live_exec, scan_thread1=a.scan_thread1)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
