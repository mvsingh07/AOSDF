#!/usr/bin/env python3
"""Live read-only coordination dashboard — script.py styling over REAL data.

A standalone console dashboard modelled on automation/script.py (ANSI banner, a
status pipeline, a runtime-telemetry panel and a live [LVL] event stream, cleared
and repainted on an interval). The one essential difference from script.py: NOTHING
here is simulated. script.py fills its CPU / memory / worker / queue figures with
`random.*` and says so in its own footer; this dashboard reads every value from the
real coordination state through ``monitor.scan()``.

READ-ONLY, like monitor.py: it launches no worker, writes NO file (not even a
cursor), edits no source/schema/status, and infers no approvals. It only renders a
dispatch-mechanics VIEW — the authoritative task status is execution_plan.md, which
must be reconciled before any action.

Usage:
  python3 monitor_dashboard.py [--config PATH] [--interval SECONDS]
                               [--once] [--color auto|always|never]

  --interval SECONDS  repaint every SECONDS (default 5); ignored with --once
  --once              render a single frame and exit (no screen clear; pipe-safe)
  --color             auto (default: only on a TTY, honours NO_COLOR) | always | never
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from pathlib import Path

# Reuse the real, read-only scan + formatting helpers rather than re-deriving them.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import monitor  # noqa: E402  (local module, same directory)

WIDTH = 76

# Same ASCII banner as script.py ("AUTO" — the automation operations console).
_BANNER = r"""    █████╗ ██╗   ██╗████████╗ ██████╗
   ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗
   ███████║██║   ██║   ██║   ██║   ██║
   ██╔══██║██║   ██║   ██║   ██║   ██║
   ██║  ██║╚██████╔╝   ██║   ╚██████╔╝
   ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝"""

# state word -> (glyph, Skin attribute name) for the pipeline panel.
_STATE_LOOK = {
    "running": ("◉", "YELLOW"), "completed": ("✔", "GREEN"), "done": ("✔", "GREEN"),
    "incorporated": ("✔", "GREEN"), "accepted": ("✔", "GREEN"),
    "blocked": ("■", "RED"), "failed": ("✖", "RED"),
}
_ENDED_OK = {"completed", "done", "incorporated", "accepted"}


class Skin:
    """ANSI palette (mirrors script.py). When ``on`` is False every code is the
    empty string, so piped / --color never / non-TTY output is plain text."""

    def __init__(self, on: bool):
        self.on = on
        g = (lambda code: code if on else "")
        self.GREEN = g("\033[92m")
        self.CYAN = g("\033[96m")
        self.BLUE = g("\033[94m")
        self.YELLOW = g("\033[93m")
        self.RED = g("\033[91m")
        self.WHITE = g("\033[97m")
        self.DIM = g("\033[90m")
        self.BOLD = g("\033[1m")
        self.RESET = g("\033[0m")


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _now_hms() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")


def _now_full() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ── real-data gathering (read-only) ──────────────────────────────────────────
def _stale(a: dict) -> bool:
    """state.json older than its task.md — the seeded/stale snapshot case,
    matching monitor.py's definition exactly."""
    return (a["state_updated"] is not None and a["task_mtime"] is not None
            and a["task_mtime"] > a["state_updated"] + 1)


def _ack(a: dict) -> str:
    if not a["task_present"]:
        return "—"
    if a["state_io"] != "ok":
        return "?"
    return "yes" if a["task_digest"] == a["state_digest"] else "NO"


def gather(config_path: Path) -> dict:
    """One read-only snapshot of the live coordination state.

    Everything here is derived from monitor.scan() + the same per-agent fields
    the monitor renders; no value is invented or randomised."""
    config, coord_root, agents = monitor.scan(config_path)
    in_scope = [a for a in agents if not a["parked"] and a.get("in_scope", True)]
    now = time.time()

    warnings: list[tuple[str, str]] = []   # (level, message)
    for a in in_scope:
        key = f"thread{a['thread']}/{a['agent']}"
        if not a["exists"]:
            warnings.append(("WARN", f"{key}: folder not yet created (setup pending)"))
        if a["state_io"] == "error":
            warnings.append(("ERR", f"{key}: state.json present but unparseable"))
        elif a["state_io"] == "absent" and a["exists"]:
            warnings.append(("WARN", f"{key}: no state.json — mechanics unknown"))
        if a["task_io"] == "error":
            warnings.append(("ERR", f"{key}: task.md present but unreadable"))
        if _stale(a):
            warnings.append(("WARN", f"{key}: state.json predates task.md — stale/seeded snapshot"))

    # ownership conflicts among concurrently-running, acknowledged agents
    running_ack = [a for a in in_scope
                   if a["state_status"] == "running" and a["state_digest"] == a["task_digest"]]
    for i in range(len(running_ack)):
        for j in range(i + 1, len(running_ack)):
            ov = monitor.overlaps(running_ack[i]["owned"], running_ack[j]["owned"])
            if ov:
                warnings.append(("ERR", f"CONFLICT — {running_ack[i]['agent']} & "
                                        f"{running_ack[j]['agent']} overlap: {'; '.join(ov)}"))

    # guides with an EXPLICIT readiness marker (never inferred from the filename)
    guides_ready = 0
    for thread in config.get("threads", []):
        gdir = coord_root / f"thread{thread.get('thread')}" / "guides"
        if gdir.is_dir():
            for p in sorted(gdir.glob("*.md")):
                if p.name.lower() != "readme.md" and monitor._guide_readiness(p) == "ready":
                    guides_ready += 1

    # sprint summary per thread (optional file)
    sprints = []
    for thread in config.get("threads", []):
        sp = monitor._load_json(coord_root / f"thread{thread.get('thread')}" / "sprint.json")
        if isinstance(sp, dict) and sp.get("tasks"):
            tasks = sp["tasks"]
            done = sum(1 for t in tasks if t.get("status") == "done")
            blocked = sum(1 for t in tasks if t.get("status") == "blocked")
            cur = next((t["id"] for t in tasks if t.get("status") == "running"),
                       next((t["id"] for t in tasks if t.get("status") == "pending"), None))
            sprints.append({"thread": thread.get("thread"), "status": str(sp.get("status")),
                            "done": done, "total": len(tasks), "blocked": blocked,
                            "current": cur or "drained"})

    n_running = sum(1 for a in in_scope if a["state_status"] == "running")
    n_completed = sum(1 for a in in_scope if (a["state_status"] or "").lower() in _ENDED_OK)
    n_blocked = sum(1 for a in in_scope if (a["state_status"] or "").lower() in ("blocked", "failed"))
    n_unacked = sum(1 for a in in_scope if _ack(a) == "NO")

    return {
        "config": config,
        "config_path": config_path,
        "in_scope": in_scope,
        "all_agents": agents,
        "warnings": warnings,
        "sprints": sprints,
        "now": now,
        "telemetry": {
            "active_threads": config.get("active_threads",
                                         [t.get("thread") for t in config.get("threads", [])]),
            "agents": len(in_scope),
            "running": n_running,
            "completed": n_completed,
            "blocked": n_blocked,
            "unacked": n_unacked,
            "guides_ready": guides_ready,
            "warnings": len(warnings),
            "conflicts": sum(1 for _, msg in warnings if msg.startswith("CONFLICT")),
        },
    }


# ── rendering (script.py layout) ─────────────────────────────────────────────
def _line(skin: Skin, char: str = "─") -> None:
    print(skin.DIM + char * WIDTH + skin.RESET)


def _log(skin: Skin, level: str, message: str, stamp: str) -> None:
    colors = {"INFO": skin.CYAN, "OK": skin.GREEN, "WARN": skin.YELLOW,
              "RUN": skin.BLUE, "SYS": skin.DIM, "ERR": skin.RED}
    color = colors.get(level, skin.WHITE)
    print(f"{skin.DIM}{stamp}{skin.RESET}  {color}[{level:^4}]{skin.RESET}  {message}")


def render(skin: Skin, data: dict) -> None:
    tel = data["telemetry"]
    config = data["config"]
    attention = tel["warnings"] or tel["conflicts"]

    print(skin.CYAN + skin.BOLD + "\n" + _BANNER + skin.RESET)
    print(skin.WHITE + skin.BOLD + "          COORDINATION OPERATIONS CONSOLE" + skin.RESET)
    print(skin.DIM + "          Dispatch mechanics · live read-only telemetry" + skin.RESET)
    _line(skin, "═")

    if tel["conflicts"]:
        status, scol = "● DEGRADED", skin.RED
    elif attention:
        status, scol = "● ATTENTION", skin.YELLOW
    else:
        status, scol = "● OPERATIONAL", skin.GREEN
    active = ", ".join(map(str, tel["active_threads"]))
    print(f"  {skin.CYAN}SYSTEM STATUS{skin.RESET}   : {scol}{status}{skin.RESET}")
    print(f"  {skin.CYAN}RUN{skin.RESET}             : {config.get('run', '(run)')}")
    print(f"  {skin.CYAN}STAGE{skin.RESET}           : {config.get('stage')}  "
          f"{skin.DIM}(read-only monitor){skin.RESET}")
    print(f"  {skin.CYAN}ACTIVE THREADS{skin.RESET}  : {active}")
    print(f"  {skin.CYAN}TIMESTAMP{skin.RESET}       : {_now_full()}")
    _line(skin)

    # [01] AGENT PIPELINE ------------------------------------------------------
    print(skin.WHITE + skin.BOLD + "\n  [01] AGENT PIPELINE" + skin.RESET)
    if not data["in_scope"]:
        print(f"      {skin.DIM}no in-scope agents{skin.RESET}")
    for a in data["in_scope"]:
        state = a["state_status"] or "n/a"
        glyph, cattr = _STATE_LOOK.get(str(state).lower(), ("○", "DIM"))
        color = getattr(skin, cattr)
        name = f"{a['agent']} ({'thread%s' % a['thread']})"
        ack = _ack(a)
        extra = []
        if a["state_seq"] is not None:
            extra.append(f"seq {a['state_seq']}")
        extra.append(f"ack {ack}")
        if a["run_running"] and a["run_started"] is not None:
            extra.append(f"up {monitor._fmt_dur(a['run_started'], data['now'])}")
        detail = ", ".join(extra)
        print(f"      {color}{glyph}  {name:<26}{skin.RESET}"
              f"[{color}{state:^12}{skin.RESET}]  {skin.DIM}{detail}{skin.RESET}")

    # sprints (only if present) ------------------------------------------------
    if data["sprints"]:
        print(skin.WHITE + skin.BOLD + "\n  [01b] SPRINTS" + skin.RESET)
        for sp in data["sprints"]:
            tail = f", {sp['blocked']} blocked" if sp["blocked"] else ""
            print(f"      thread{sp['thread']}  {skin.DIM}{sp['status']:<10}{skin.RESET}"
                  f"{sp['done']}/{sp['total']} done{tail}  →  {sp['current']}")

    _line(skin)

    # [02] RUNTIME TELEMETRY (real counts) -------------------------------------
    print(skin.WHITE + skin.BOLD + "\n  [02] RUNTIME TELEMETRY" + skin.RESET)
    print(f"      AGENTS IN SCOPE  : {tel['agents']}")
    print(f"      RUNNING          : {skin.YELLOW if tel['running'] else ''}{tel['running']}{skin.RESET}")
    print(f"      COMPLETED        : {skin.GREEN if tel['completed'] else ''}{tel['completed']}{skin.RESET}")
    print(f"      BLOCKED/FAILED   : {skin.RED if tel['blocked'] else ''}{tel['blocked']}{skin.RESET}")
    print(f"      READY / UNACKED  : {tel['unacked']}")
    print(f"      GUIDES READY     : {tel['guides_ready']}")
    print(f"      WARNINGS         : {skin.YELLOW if tel['warnings'] else ''}{tel['warnings']}{skin.RESET}")
    print(f"      CONFLICTS        : {skin.RED if tel['conflicts'] else ''}{tel['conflicts']}{skin.RESET}")
    _line(skin)

    # [03] LIVE EVENT STREAM (real) --------------------------------------------
    print(skin.WHITE + skin.BOLD + "\n  [03] LIVE EVENT STREAM" + skin.RESET)
    stamp = _now_hms()
    events: list[tuple[str, str]] = []
    for a in data["in_scope"]:
        state = (a["state_status"] or "n/a").lower()
        if state in _ENDED_OK:
            lvl = "OK"
        elif state == "running":
            lvl = "RUN"
        elif state in ("blocked", "failed"):
            lvl = "ERR"
        else:
            lvl = "INFO"
        events.append((lvl, f"thread{a['thread']}/{a['agent']} — {a['state_status'] or 'n/a'} "
                            f"(ack {_ack(a)})"))
    events.extend(data["warnings"])
    if not events:
        print(f"      {skin.DIM}no agents / no observations{skin.RESET}")
    for lvl, msg in events[:16]:
        _log(skin, lvl, msg, stamp)

    _line(skin, "═")
    errs = data["telemetry"]["warnings"]
    print(f"\n  {scol}{status}{skin.RESET}  {skin.DIM}|{skin.RESET}  "
          f"{skin.CYAN}THREADS: {active}{skin.RESET}  {skin.DIM}|{skin.RESET}  "
          f"{skin.WHITE}WARNINGS: {errs}{skin.RESET}")
    print(f"\n  {skin.DIM}Live read-only view of real coordination state — nothing here is "
          f"simulated.{skin.RESET}")
    print(f"  {skin.DIM}Authoritative task status is execution_plan.md; reconcile before any "
          f"takeover.{skin.RESET}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Live read-only coordination dashboard (script.py style)")
    ap.add_argument("--config", default=str(HERE / "config" / "adr-025.topology.json"),
                    help="topology config (default: config/adr-025.topology.json)")
    ap.add_argument("--interval", type=float, default=5.0, metavar="SECONDS",
                    help="repaint every SECONDS (default 5); ignored with --once")
    ap.add_argument("--once", action="store_true",
                    help="render a single frame and exit (no screen clear; pipe-safe)")
    ap.add_argument("--color", choices=("auto", "always", "never"), default="auto",
                    help="ANSI styling: auto (TTY + NO_COLOR unset) | always | never")
    args = ap.parse_args()

    if args.color == "always":
        color_on = True
    elif args.color == "never":
        color_on = False
    else:
        color_on = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    skin = Skin(color_on)

    config_path = Path(args.config).resolve()
    repaint = skin.on and not args.once   # clear-and-redraw only for a live TTY loop

    def frame() -> None:
        data = gather(config_path)
        if repaint:
            _clear()
        render(skin, data)

    if args.once:
        frame()
        return 0

    print(f"[dashboard] live mode — repaint every {args.interval:g}s; Ctrl-C to stop.", flush=True)
    try:
        while True:
            frame()
            time.sleep(max(1.0, args.interval))
    except KeyboardInterrupt:
        print(f"\n\n{skin.YELLOW}  Dashboard closed.{skin.RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
