#!/usr/bin/env python3
"""Stage-1 read-only coordination monitor (automation-proposal.md sections 7, 10).

READ-ONLY. The only file this writes is its own cursor (var/cursor.json), used for
duplicate suppression. It never launches a worker, never edits source/schema/canonical
status, never replaces a task.md, never runs a manual action, and never infers approvals.

It reports, since the last check (cursor):
  - new agent completion handoffs (deduplicated on the (dispatch_sequence, run_id) tuple,
    NOT on the status transition alone — a completed -> running -> completed sequence that
    a poll skipped past is still surfaced);
  - ready assignments not yet acknowledged (task.md changed but state not claimed);
  - human actions with guides that EXPLICITLY declare readiness (never inferred from the
    filename); other present guides are listed without asserting readiness;
  - ownership conflicts (overlapping write targets of concurrently-running agents)
    and missing cross-thread dependencies;
  - correctness warnings: unreadable/unparseable state.json or task.md, a digest mismatch
    (unacknowledged dispatch), a state.json older than its task.md (stale/seeded snapshot),
    and configured canonical-watch paths that do not exist.

These are DISPATCH-MECHANICS observations, not live task truth (status authority is
execution_plan.md). Reconcile against the live record before any takeover.

Usage:
  python3 monitor.py [--config config/adr-025.topology.json] [--reset] [--no-cursor] [--json]
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, textwrap, time, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Rendered report width (fits an 80-col terminal with a 1-space gutter).
WIDTH = 78

# ── presentation layer ───────────────────────────────────────────────────────
# A styled console skin modelled on automation/script.py (ANSI banner, colored
# status glyphs, a [LVL] event stream and a status-bar footer). It is COSMETIC
# ONLY: every value rendered still comes from the real read-only scan — unlike
# script.py, nothing here is random or simulated. Styling is off unless a real
# terminal is attached, so piped/cron/--json output and the test suite stay
# byte-for-byte plain.
GREEN, CYAN, BLUE, YELLOW, RED = "\033[92m", "\033[96m", "\033[94m", "\033[93m", "\033[91m"
WHITE, DIM, BOLD, RESET = "\033[97m", "\033[90m", "\033[1m", "\033[0m"

# AUTO — the automation operations console (same art as script.py).
_BANNER = r"""    █████╗ ██╗   ██╗████████╗ ██████╗
   ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗
   ███████║██║   ██║   ██║   ██║   ██║
   ██╔══██║██║   ██║   ██║   ██║   ██║
   ██║  ██║╚██████╔╝   ██║   ╚██████╔╝
   ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝"""

# state word -> (glyph, color) for the agent table and snapshot.
_STATE_LOOK = {
    "running": ("◉", YELLOW), "completed": ("✔", GREEN), "done": ("✔", GREEN),
    "incorporated": ("✔", GREEN), "accepted": ("✔", GREEN),
    "blocked": ("■", RED), "failed": ("✖", RED),
}
# event-stream level -> color (mirrors script.py's log() palette).
_LEVEL_COLOR = {"OK": GREEN, "INFO": CYAN, "WARN": YELLOW, "RUN": BLUE, "SYS": DIM, "ERR": RED}


class Style:
    """A color skin. When ``enabled`` is False every method returns its text
    unchanged, so a plain report is identical to the pre-skin output."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def _c(self, code: str, text: str) -> str:
        return f"{code}{text}{RESET}" if self.enabled else text

    def dim(self, t):     return self._c(DIM, t)
    def green(self, t):   return self._c(GREEN, t)
    def red(self, t):     return self._c(RED, t)
    def yellow(self, t):  return self._c(YELLOW, t)
    def cyan(self, t):    return self._c(CYAN, t)
    def heading(self, t): return self._c(BOLD + WHITE, t)
    def label(self, t):   return self._c(CYAN, t)
    def rule(self, t):    return self._c(DIM, t)

    def state_cell(self, status, width: int, glyph: bool = True) -> str:
        """Status word padded to ``width``; prefixed with a colored glyph (unless
        ``glyph`` is False, for narrow columns) when styling is on. Padding sits
        inside the color so column widths are preserved (ANSI codes are zero-width)."""
        s = str(status if status is not None else "n/a")
        if not self.enabled:
            return f"{s:<{width}}"
        mark, code = _STATE_LOOK.get(s.lower(), ("○", DIM))
        body = f"{mark} {s}" if glyph else s
        return f"{code}{body:<{width}}{RESET}"

    def log(self, level: str, message: str) -> list[str]:
        """One event-stream line (``HH:MM:SS  [LVL]  message``), wrapped to WIDTH.
        Plain mode falls back to a simple bullet so piped output stays readable."""
        if not self.enabled:
            return _bullet(message)
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        code = _LEVEL_COLOR.get(level, WHITE)
        tag = f"{self.dim(ts)}  {code}[{level:^4}]{RESET}  "
        wrapped = textwrap.wrap(message, width=WIDTH - 20,
                                break_long_words=False, break_on_hyphens=False) or [message]
        hang = " " * 15
        out = [f"  {tag}{wrapped[0]}"]
        out += [f"  {hang}{self.dim(w)}" for w in wrapped[1:]]
        return out


_PLAIN = Style(False)


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _utc_pretty() -> str:
    """Human-readable UTC stamp for report headings."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _section(title: str, style: "Style | None" = None) -> list[str]:
    """A titled section header: a blank line, the title, and a light underline."""
    st = style or _PLAIN
    return ["", st.heading(title), st.rule("─" * WIDTH)]


def _kv(label: str, value: str, width: int = 18, style: "Style | None" = None) -> str:
    """A left-aligned label / value row used in the posture block."""
    st = style or _PLAIN
    return f"  {st.label(f'{label:<{width}}')}{value}"


def _wrap_list(items: list[str], indent: str = "    ", sep: str = ", ") -> list[str]:
    """Wrap a comma-separated list to WIDTH, indenting continuation lines."""
    if not items:
        return []
    return textwrap.wrap(
        sep.join(items), width=WIDTH,
        initial_indent=indent, subsequent_indent=indent,
        break_long_words=False, break_on_hyphens=False,
    )


def _bullet(text: str, indent: str = "    ", marker: str = "• ") -> list[str]:
    """One bulleted item, wrapped to WIDTH with continuation lines hanging under the text."""
    return textwrap.wrap(
        text, width=WIDTH,
        initial_indent=indent + marker, subsequent_indent=indent + " " * len(marker),
        break_long_words=False, break_on_hyphens=False,
    ) or [indent + marker + text]


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _digest(text: str | None) -> str | None:
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _load_json_status(path: Path):
    """Return (obj_or_None, status) where status is 'ok' | 'absent' | 'error'."""
    if not path.exists():
        return None, "absent"
    txt = _read(path)
    if txt is None:
        return None, "error"
    try:
        return json.loads(txt), "ok"
    except json.JSONDecodeError:
        return None, "error"


def _load_json(path: Path):
    obj, _ = _load_json_status(path)
    return obj


def _mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _parse_utc(value) -> float | None:
    """Best-effort ISO-8601 -> epoch seconds; tolerates a trailing 'Z'."""
    if not isinstance(value, str) or not value:
        return None
    try:
        v = value.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(v).timestamp()
    except ValueError:
        return None


def _fmt_ts(epoch: float | None) -> str:
    if epoch is None:
        return "—"
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).strftime("%m-%d %H:%M:%S")


def _fmt_dur(start: float | None, end: float | None) -> str:
    if start is None or end is None or end < start:
        return "—"
    secs = int(end - start)
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m{secs % 60:02d}s"
    return f"{secs // 3600}h{(secs % 3600) // 60:02d}m"


# statuses that mean the run has ended (a result exists / was consumed)
_ENDED_STATUSES = {"completed", "incorporated", "accepted", "blocked", "failed", "done"}


def _run_info(folder: Path, seq, status, state_updated):
    """Start/end/launch facts for an agent's CURRENT run folder (runs/NNN).

    started: the visible-launch time (launch.json) if the worker was launched via the launcher,
             else the task.md issue time. ended: result.json mtime once the run has ended, else the
             state's updated_utc for an ended status. Also reports whether a visible window was opened.
    """
    info = {"started": None, "ended": None, "launched": False, "window": None, "running": False}
    if seq is None:
        return info
    try:
        run_dir = folder / "runs" / f"{int(seq):03d}"
    except (TypeError, ValueError):
        return info
    lj = _load_json(run_dir / "launch.json") if run_dir.is_dir() else None
    if isinstance(lj, dict) and lj.get("created_utc"):
        info["started"] = _parse_utc(lj["created_utc"])
    if run_dir.is_dir() and (run_dir / ".launcher-once").exists():
        info["launched"] = True
    tw = _load_json(run_dir / "terminal-window.json") if run_dir.is_dir() else None
    if isinstance(tw, dict):
        info["window"] = tw.get("window_id")
    if info["started"] is None:
        info["started"] = _mtime(folder / "task.md")
    res_m = _mtime(run_dir / "result.json") if run_dir.is_dir() else None
    ended = (status or "").lower() in _ENDED_STATUSES
    if ended:
        info["ended"] = res_m if res_m is not None else state_updated
    else:
        info["running"] = status == "running"
    return info


def _last_track_seq(track_text: str | None) -> int | None:
    """track.md is an append-only index; return the highest leading integer found."""
    if not track_text:
        return None
    best = None
    for line in track_text.splitlines():
        token = line.strip().lstrip("|").strip().split()[:1]
        if token and token[0].isdigit():
            best = max(best or 0, int(token[0]))
    return best


def _guide_readiness(path: Path) -> str:
    """Readiness is asserted ONLY by an explicit marker in the guide, never by existence.

    A guide is 'ready' only if one of its first 40 lines contains a status marker whose
    value is READY/ACTIONABLE (e.g. 'Status: READY', 'Readiness: ACTIONABLE'). A marker
    with any other value (DRAFT/BLOCKED/HELD/PENDING/...) is reported as that value.
    No marker -> 'unasserted' (present, readiness not claimed).
    """
    txt = _read(path)
    if txt is None:
        return "unreadable"
    for line in txt.splitlines()[:40]:
        low = line.strip().lower()
        for key in ("status:", "readiness:", "guide-status:"):
            if low.startswith(key):
                val = low[len(key):].strip().strip("*`").split()[:1]
                if not val:
                    continue
                v = val[0].rstrip(".,;")
                if v in ("ready", "actionable", "go"):
                    return "ready"
                return v  # explicit non-ready status (draft/blocked/held/pending/...)
    return "unasserted"


def scan(config_path: Path):
    config = _load_json(config_path)
    if config is None:
        print(f"ERROR: cannot read/parse config {config_path}", file=sys.stderr)
        sys.exit(2)
    coord_root = (config_path.parent / config.get("coordination_root", "..")).resolve()

    agents = []
    for thread in config.get("threads", []):
        tnum = thread.get("thread")
        for ag in thread.get("agents", []):
            folder = coord_root / f"thread{tnum}" / ag["agent"]
            state, state_io = _load_json_status(folder / "state.json")
            state = state or {}
            task_path = folder / "task.md"
            task_present = task_path.exists()
            task_text = _read(task_path) if task_present else None
            task_io = "ok" if (task_text is not None) else ("error" if task_present else "absent")
            task_mtime = _mtime(task_path)
            state_updated = _parse_utc(state.get("updated_utc"))
            run = _run_info(folder, state.get("dispatch_sequence"), state.get("status"), state_updated)
            agents.append({
                "run_started": run["started"],
                "run_ended": run["ended"],
                "run_running": run["running"],
                "run_launched": run["launched"],
                "run_window": run["window"],
                "agent": ag["agent"],
                "thread": tnum,
                "model": state.get("model") or ag.get("model"),
                "in_scope": tnum in config.get("active_threads", [t.get("thread") for t in config.get("threads", [])]),
                "folder": folder,
                "exists": folder.is_dir(),
                "state_io": state_io,                 # ok | absent | error
                "state_status": state.get("status"),
                "state_digest": state.get("task_digest"),
                "state_seq": state.get("dispatch_sequence"),
                "state_run_id": state.get("run_id"),
                "state_updated": state_updated,        # epoch or None
                "task_io": task_io,                    # ok | absent | error
                "task_digest": _digest(task_text),
                "task_present": task_present,
                "task_mtime": task_mtime,
                "track_seq": _last_track_seq(_read(folder / "track.md")),
                "context_mtime": _mtime(folder / "context.md"),
                "owned": [t for t in state.get("owned_write_targets", ag.get("owned_write_targets", [])) if "no source" not in t.lower()],
                "parked": thread.get("role") == "parked-planning-only",
            })
    return config, coord_root, agents


def overlaps(a: list[str], b: list[str]) -> list[str]:
    """Coarse overlap: a shared path prefix before any glob wildcard."""
    def norm(items):
        return {x.split("**")[0].split("*")[0].strip().rstrip("/") for x in items}
    na, nb = norm(a), norm(b)
    hits = []
    for x in na:
        for y in nb:
            if x and y and (x == y or x.startswith(y + "/") or y.startswith(x + "/")):
                hits.append(f"{x} ~ {y}")
    return hits


def report(config, coord_root, agents, cursor, config_path: Path, style: "Style | None" = None):
    st = style or _PLAIN
    new_cursor = dict(cursor)
    now = time.time()
    in_scope = [a for a in agents if not a["parked"] and a.get("in_scope", True)]

    # ---- change/warning detection (identical logic; grouped into typed buckets) --------
    warnings, handoffs, ready_items, guides_ready, guides_other, deps = [], [], [], [], [], []

    for a in agents:
        if a["parked"] or not a.get("in_scope", True):
            continue
        key = f"thread{a['thread']}/{a['agent']}"
        prev = cursor.get(key, {})
        if not isinstance(prev, dict):   # tolerate an older/other cursor schema
            prev = {}

        if not a["exists"]:
            warnings.append(f"{key}: folder not yet created (setup pending).")
        if a["state_io"] == "error":
            warnings.append(f"{key}: state.json present but unparseable — mechanics unknown.")
        elif a["state_io"] == "absent" and a["exists"]:
            warnings.append(f"{key}: no state.json — mechanics unknown.")
        if a["task_io"] == "error":
            warnings.append(f"{key}: task.md present but unreadable.")
        stale = (a["state_updated"] is not None and a["task_mtime"] is not None
                 and a["task_mtime"] > a["state_updated"] + 1)
        if stale and prev.get("stale") != True:
            warnings.append(f"{key}: state.json predates its task.md — seeded/stale snapshot; "
                            f"reconcile against the live record before acting.")

        # completion handoff — dedup on (seq, run_id), not status transition alone
        done_marker = f"{a['state_seq']}:{a['state_run_id']}" if a["state_status"] == "completed" else None
        if a["state_status"] == "completed" and done_marker != prev.get("done_marker"):
            handoffs.append(f"{key}: completed (seq {a['state_seq']}, run {a['state_run_id']}).")
        carry_done = done_marker if a["state_status"] == "completed" else prev.get("done_marker")

        # ready / unacknowledged assignment
        if (a["task_io"] == "ok" and a["state_io"] == "ok"
                and a["task_digest"] != a["state_digest"]
                and prev.get("task_digest") != a["task_digest"]):
            ready_items.append(f"{key}: task.md not yet reflected in state.json (ack = NO).")

        new_cursor[key] = {"state_status": a["state_status"], "task_digest": a["task_digest"],
                           "done_marker": carry_done, "track_seq": a["track_seq"],
                           "context_mtime": a["context_mtime"], "stale": stale}

    # human actions with guides — readiness is explicit, never inferred from filename
    for thread in config.get("threads", []):
        gdir = coord_root / f"thread{thread.get('thread')}" / "guides"
        if not gdir.is_dir():
            continue
        ready, other = [], []
        for p in sorted(gdir.glob("*.md")):
            if p.name.lower() == "readme.md":
                continue
            r = _guide_readiness(p)
            (ready if r == "ready" else other).append(f"{p.name} ({r})" if r != "ready" else p.name)
        gkey = f"guides/thread{thread.get('thread')}"
        prev_guides = cursor.get(gkey)
        if not isinstance(prev_guides, dict):   # tolerate an older/other cursor schema
            prev_guides = {}
        if ready and prev_guides.get("ready") != ready:
            guides_ready.append((thread.get("thread"), ready))
        if other and prev_guides.get("other") != other:
            guides_other.append((thread.get("thread"), other))
        new_cursor[gkey] = {"ready": ready, "other": other}

    # ownership conflicts (concurrently-running overlap)
    running = [a for a in agents if a["state_status"] == "running" and not a["parked"]
               and a.get("in_scope", True) and a["state_digest"] == a["task_digest"]]
    for i in range(len(running)):
        for j in range(i + 1, len(running)):
            ov = overlaps(running[i]["owned"], running[j]["owned"])
            if ov:
                warnings.append(f"CONFLICT — {running[i]['agent']} & {running[j]['agent']} running with "
                                f"overlapping write targets: {'; '.join(ov)}.")

    # canonical-watch path validation (configured authority paths must exist)
    missing_paths = []
    for rel in config.get("canonical_watch", []):
        if not (config_path.parent / rel).resolve().exists():
            missing_paths.append(rel)
    pkey = "config/canonical_watch_missing"
    if missing_paths and cursor.get(pkey) != missing_paths:
        warnings.append(f"configured canonical_watch path(s) do not exist: {', '.join(missing_paths)}.")
    new_cursor[pkey] = missing_paths

    any_change = bool(warnings or handoffs or ready_items or guides_ready or guides_other)
    if any_change and not cursor:   # first-run: surface the standing cross-thread routes
        for dep in config.get("cross_thread_dependencies", []):
            deps.append(f"{dep['from']} → {dep['to']}  ({dep['route']})")

    # real (never simulated) counts for the snapshot block and status bar
    _ENDED_OK = {"completed", "done", "incorporated", "accepted"}
    n_scope = len(in_scope)
    n_running = sum(1 for a in in_scope if a["state_status"] == "running")
    n_completed = sum(1 for a in in_scope if (a["state_status"] or "").lower() in _ENDED_OK)
    n_blocked = sum(1 for a in in_scope if (a["state_status"] or "").lower() in ("blocked", "failed"))
    n_handoff, n_ready, n_warn = len(handoffs), len(ready_items), len(warnings)
    n_conflict = sum(1 for w in warnings if w.startswith("CONFLICT"))
    n_guides_ready = sum(len(names) for _, names in guides_ready)

    # ================================ render =============================================
    lines: list[str] = []
    if st.enabled:
        lines.append(st._c(BOLD + CYAN, _BANNER))
        lines.append("  " + st._c(BOLD + WHITE, "COORDINATION MONITOR")
                     + st.dim("   ·   Stage-1 read-only operations console"))
        lines.append(st.rule("═" * WIDTH))
        lines.append("  " + st.label(f"{'RUN':<10}") + str(config.get("run", "(run)")))
        lines.append("  " + st.label(f"{'SNAPSHOT':<10}") + _utc_pretty()
                     + st.dim(f"   ·   read-only (Stage {config.get('stage')})"))
        lines.append(st.rule("═" * WIDTH))
    else:
        lines.append("═" * WIDTH)
        lines.append(f" COORDINATION MONITOR · {config.get('run', '(run)')}")
        lines.append(f" {_utc_pretty()} · read-only (Stage {config.get('stage')})")
        lines.append("═" * WIDTH)

    # posture ----------------------------------------------------------------------------
    mode = str(config.get("mode", "?")).upper()
    assign = config.get("assign_launch", "not-authorized")
    wlm = config.get("worker_launch_mode", "full-auto")
    wlm_cmd = {"full-auto": "codex --yolo / claude --dangerously-skip-permissions",
               "interactive": "per-action approval"}.get(wlm, wlm)
    active = ", ".join(map(str, config.get("active_threads",
                       [t.get("thread") for t in config.get("threads", [])])))
    lines += _section(" AUTOMATION POSTURE", st)
    lines.append(_kv("Mode", f"{mode}   (Stage {config.get('stage')}, read-only monitor)", style=st))
    lines.append(_kv("Lead coordinator", str(config.get("lead_coordinator")), style=st))
    lines.append(_kv("Assign-launch", str(assign), style=st))
    lines.append(_kv("Worker mode", f"{wlm}  ({wlm_cmd})", style=st))
    lines.append(_kv("Active threads", active, style=st))
    if config.get("execution_backend"):
        for i, seg in enumerate(_wrap_list([config["execution_backend"]], indent="")):
            lines.append(_kv("Execution" if i == 0 else "", seg, style=st))
    lines.append(_kv("Note", "dispatch-mechanics view; live task status is execution_plan.md", style=st))
    lines.append(_kv("", "— reconcile against the canonical record before any takeover.", style=st))

    # runtime snapshot (real scan counts — not simulated like script.py) -----------------
    att = f"{n_warn} warning(s) · {n_conflict} conflict(s)"
    att = st.red(att) if n_conflict else (st.yellow(att) if n_warn else st.green(att))
    lines += _section(" RUNTIME SNAPSHOT", st)
    lines.append(_kv("In scope", f"{n_scope} agent(s): {n_running} running · "
                                  f"{n_completed} completed · {n_blocked} blocked/failed", style=st))
    lines.append(_kv("Since last check", f"{n_handoff} handoff(s) · {n_ready} ready/unacked · "
                                         f"{n_guides_ready} guide(s) ready", style=st))
    lines.append(_kv("Attention", att, style=st))

    # sprints ----------------------------------------------------------------------------
    sprint_rows = []
    for thread in config.get("threads", []):
        sp = _load_json(coord_root / f"thread{thread.get('thread')}" / "sprint.json")
        if isinstance(sp, dict) and sp.get("tasks"):
            tasks = sp["tasks"]
            done = sum(1 for t in tasks if t.get("status") == "done")
            blocked = sum(1 for t in tasks if t.get("status") == "blocked")
            cur = next((t["id"] for t in tasks if t.get("status") == "running"),
                       next((t["id"] for t in tasks if t.get("status") == "pending"), None))
            sprint_rows.append((f"thread{thread.get('thread')}", str(sp.get("status")),
                                f"{done}/{len(tasks)} done" + (f", {blocked} blocked" if blocked else ""),
                                (cur or "drained"), (sp.get("model") or "(default)")))
    if sprint_rows:
        lines += _section(" SPRINTS", st)
        lines.append("  " + st.dim(f"{'Thread':<9}{'Status':<9}{'Progress':<18}{'Current / next':<28}Model"))
        lines.append("  " + st.rule("─" * (WIDTH - 2)))
        for th, sp_status, prog, cur, model in sprint_rows:
            lines.append(f"  {th:<9}" + st.state_cell(sp_status, 9, glyph=False)
                         + f"{prog:<18}{cur:<28}{model}")

    # agents -----------------------------------------------------------------------------
    lines += _section(" AGENTS", st)
    lines.append("  " + st.dim(f"{'Agent':<11}{'Thr':<5}{'Model':<8}{'State':<13}"
                               f"{'Seq':<6}{'Task':<6}{'Ack':<5}Flags"))
    lines.append("  " + st.rule("─" * (WIDTH - 2)))
    for a in in_scope:
        if not a["task_present"]:
            ack = "—"
        elif a["state_io"] != "ok":
            ack = "?"
        else:
            ack = "yes" if a["task_digest"] == a["state_digest"] else "NO"
        flags = []
        if a["state_io"] == "absent":
            flags.append("no-state")
        elif a["state_io"] == "error":
            flags.append("bad-state")
        if a["task_io"] == "error":
            flags.append("bad-task")
        if (a["state_updated"] is not None and a["task_mtime"] is not None
                and a["task_mtime"] > a["state_updated"] + 1):
            flags.append("stale")
        task_cell = {"ok": "yes", "absent": "no", "error": "err"}[a["task_io"]]
        flags_str = ", ".join(flags) or "—"
        if st.enabled:
            ack_cell = st.red(ack) if ack == "NO" else (st.green(ack) if ack == "yes" else st.dim(ack))
            if flags:
                bad = any(f in ("bad-state", "bad-task") for f in flags)
                flags_str = (st.red if bad else st.yellow)(flags_str)
            else:
                flags_str = st.dim("—")
        else:
            ack_cell = ack
        lines.append("  " + f"{a['agent']:<11}{str(a['thread']):<5}{str(a['model'] or ''):<8}"
                     + st.state_cell(a["state_status"], 13)
                     + f"{str(a['state_seq'] if a['state_seq'] is not None else '—'):<6}"
                     + f"{task_cell:<6}"
                     + ack_cell + " " * (5 - len(ack))
                     + flags_str)

    # run timeline -----------------------------------------------------------------------
    if in_scope:
        lines += _section(" RUN TIMELINE  (current dispatch per agent)", st)
        lines.append("  " + st.dim(f"{'Agent':<11}{'Seq':<6}{'Started (UTC)':<18}"
                                   f"{'Ended (UTC)':<18}{'Elapsed':<9}Window"))
        lines.append("  " + st.rule("─" * (WIDTH - 2)))
        for a in in_scope:
            seq = a["state_seq"]
            started, ended, running_now = a["run_started"], a["run_ended"], a["run_running"]
            if running_now:
                end_cell, dur = "running", _fmt_dur(started, now)
            elif ended is not None:
                end_cell, dur = _fmt_ts(ended), _fmt_dur(started, ended)
            else:
                end_cell, dur = "—", "—"
            win = (f"win {a['run_window']}" if a["run_window"] else ("launched" if a["run_launched"] else "—"))
            lines.append(f"  {a['agent']:<11}{str(seq if seq is not None else '—'):<6}"
                         f"{_fmt_ts(started):<18}{end_cell:<18}{dur:<9}{win}")
        by_thread: dict = {}
        for a in in_scope:
            t = by_thread.setdefault(a["thread"], {"starts": [], "ends": [], "running": False})
            if a["run_started"] is not None:
                t["starts"].append(a["run_started"])
            if a["run_running"]:
                t["running"] = True
            elif a["run_ended"] is not None:
                t["ends"].append(a["run_ended"])
        if by_thread:
            lines.append("")
            for tnum in sorted(by_thread):
                t = by_thread[tnum]
                first = _fmt_ts(min(t["starts"])) if t["starts"] else "—"
                if t["running"]:
                    last = st.yellow("active (worker running)")
                elif t["ends"]:
                    last = _fmt_ts(max(t["ends"]))
                else:
                    last = "—"
                lines.append(f"  thread{tnum} span   {first}  →  {last}")

    excluded = [a for a in agents if not a.get("in_scope", True)]
    if excluded:
        lines += _section(" OUT OF SCOPE  (records unchanged)", st)
        lines += [st.dim(x) for x in _wrap_list([a["agent"] for a in excluded])]

    # changes — rendered as a colored [LVL] event stream when styling is on --------------
    lines += _section(" LIVE EVENT STREAM" if st.enabled else " CHANGES SINCE LAST CHECK", st)
    if not any_change:
        lines.append("  " + st.dim("No new handoffs, ready assignments, guides, warnings, or conflicts."))
    elif st.enabled:
        for it in handoffs:
            lines += st.log("OK", it)
        for it in ready_items:
            lines += st.log("INFO", it)
        for it in warnings:
            lines += st.log("ERR" if it.startswith("CONFLICT") else "WARN", it)
        for tnum, names in guides_ready:
            lines += st.log("OK", f"Guides READY — thread{tnum} ({len(names)}): " + ", ".join(names))
        for tnum, names in guides_other:
            lines += st.log("INFO", f"Guides present, readiness not asserted — "
                                    f"thread{tnum} ({len(names)}): " + ", ".join(names))
        for d in deps:
            lines += st.log("SYS", d)
    else:
        def block(title, items):
            if items:
                lines.append(f"  {title}")
                for it in items:
                    lines.extend(_bullet(it))
        block("Handoffs", handoffs)
        block("Ready / unacknowledged", ready_items)
        block("Warnings", warnings)
        for tnum, names in guides_ready:
            lines.append(f"  Guides READY — thread{tnum} ({len(names)})")
            lines.extend(f"    • {n}" for n in names)
        for tnum, names in guides_other:
            lines.append(f"  Guides present, readiness not asserted — thread{tnum} ({len(names)})")
            lines.extend(f"    • {n}" for n in names)
        block("Cross-thread dependencies", deps)

    # status bar (styled mode only; real counts) -----------------------------------------
    if st.enabled:
        lines.append(st.rule("═" * WIDTH))
        clean = not (n_warn or n_conflict)
        dot = st.green("●") if clean else st.yellow("●")
        word = st.green("OPERATIONAL") if clean else st.yellow("ATTENTION")
        warn_cell = st.red(str(n_warn)) if n_warn else "0"
        bar = (f"  {dot} {word}   {st.dim('|')}   AGENTS: {n_scope}   {st.dim('|')}   "
               f"RUNNING: {n_running}   {st.dim('|')}   HANDOFFS: {n_handoff}   {st.dim('|')}   "
               f"WARNINGS: {warn_cell}")
        lines.append(bar)
        lines.append("  " + st.dim(f"read-only (Stage {config.get('stage')}) · dispatch-mechanics "
                                   f"view — reconcile against execution_plan.md before any takeover."))

    lines.append("")
    return "\n".join(lines), new_cursor, any_change


def display_signature(config, agents, cursor):
    """Stable display identity: timestamps in rendered headings never cause noise."""
    visible = [{k: a.get(k) for k in (
        "agent", "thread", "model", "state_status", "state_seq", "state_run_id",
        "state_digest", "task_digest", "state_io", "task_io", "in_scope", "parked",
        "run_launched", "run_window", "run_running", "run_ended",
    )} for a in agents]
    return json.dumps({"agents": visible, "cursor": cursor,
                       "active_threads": config.get("active_threads"),
                       "execution_backend": config.get("execution_backend")}, sort_keys=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage-1 read-only coordination monitor")
    ap.add_argument("--config", default=str(HERE / "config" / "adr-025.topology.json"))
    ap.add_argument("--reset", action="store_true", help="clear the cursor before scanning")
    ap.add_argument("--no-cursor", action="store_true", help="do not read or write the cursor")
    ap.add_argument("--json", action="store_true", help="emit the raw agent scan as JSON")
    ap.add_argument("--changes-only", action="store_true", help="in continuous mode, print only when observed status changes")
    ap.add_argument("--interval", type=float, default=None, metavar="SECONDS",
                    help="run continuously, reprinting status every SECONDS (Ctrl-C to stop); "
                         "omit for a single one-shot report (e.g. for cron)")
    ap.add_argument("--color", choices=("auto", "always", "never"), default="auto",
                    help="styled ANSI console skin (banner, colored status, event stream): "
                         "'auto' (default) only when stdout is a real terminal and NO_COLOR is unset; "
                         "'always' forces it; 'never' keeps plain text (for pipes/cron/logs)")
    args = ap.parse_args()

    config_path = Path(args.config).resolve()

    if args.json:
        _, _, agents = scan(config_path)
        print(json.dumps([{k: (str(v) if isinstance(v, Path) else v) for k, v in a.items()} for a in agents],
                         indent=2, default=str))
        return 0

    # Color is cosmetic only and must never leak into piped/cron/captured output.
    if args.color == "always":
        color_on = True
    elif args.color == "never":
        color_on = False
    else:
        color_on = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    style = Style(color_on)

    cfg0 = _load_json(config_path) or {}
    cursor_file = (config_path.parent / cfg0.get("cursor_path", "var/cursor.json")).resolve()
    use_cursor = not args.no_cursor
    cursor = {} if (args.reset or args.no_cursor) else (_load_json(cursor_file) or {})

    last_signature = None
    # In styled continuous mode, repaint in place (like script.py) instead of scrolling.
    live_repaint = style.enabled and bool(args.interval and args.interval > 0)

    def tick() -> bool:
        nonlocal cursor, last_signature
        config, coord_root, agents = scan(config_path)
        text, cursor, _ = report(config, coord_root, agents, cursor, config_path, style)
        signature = display_signature(config, agents, cursor)
        printed = not args.changes_only or signature != last_signature
        if printed:
            if live_repaint:
                _clear()
            print(text, flush=True)
        last_signature = signature
        if use_cursor:
            cursor_file.parent.mkdir(parents=True, exist_ok=True)
            cursor_file.write_text(json.dumps(cursor, indent=2) + "\n", encoding="utf-8")
        return printed

    if args.interval and args.interval > 0:
        print(f"[monitor] continuous mode — status every {args.interval:g}s; Ctrl-C to stop.", flush=True)
        try:
            while True:
                if tick() and not live_repaint:
                    print(style.rule("-" * 72), flush=True)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[monitor] stopped.", flush=True)
        return 0

    tick()
    return 0


if __name__ == "__main__":
    sys.exit(main())
