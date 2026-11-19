#!/usr/bin/env python3
"""Sprint state for a thread coordinator (founder direction 2026-10-23).

A *sprint* is one coordinator execution covering a founder-approved set of tasks (one or many).
The coordinator runs the whole sprint in its own persistent, self-compacting session, advancing
task-by-task without asking the founder between tasks — stopping only at a hard gate, a genuine
blocker, or sprint completion.

On the first execution of a thread (no active sprint) the coordinator asks EXACTLY two questions,
with options, then records the answers here and begins dispatching:
  Q1 — Sprint scope: which task(s) this sprint covers (single or multiple, ordered).
  Q2 — LLM + model: which executor/model the workers run, with a suggestion by task complexity.

This module stores that decision as `thread<N>/sprint.json` and tracks per-task progress. It is
stdlib-only and writes only the sprint file it is given.
"""
from __future__ import annotations
import argparse, json, sys, datetime
from pathlib import Path

TASK_STATES = ("pending", "running", "done", "blocked")

# Q2 — available executors/models + a complexity-keyed suggestion. Friendly aliases map to the
# launcher's --model flag (Claude Code resolves opus/sonnet/haiku to the latest of each tier).
MODEL_MENU = [
    {"key": "claude-opus",   "executor": "claude", "model": "opus",
     "best_for": "HIGH complexity: new architecture, cross-cutting or security-sensitive work, "
                 "ambiguous scope, multi-file refactors."},
    {"key": "claude-sonnet", "executor": "claude", "model": "sonnet",
     "best_for": "MEDIUM complexity: standard feature/migration work within a clear contract. "
                 "A good default."},
    {"key": "claude-haiku",  "executor": "claude", "model": "haiku",
     "best_for": "LOW complexity: well-scoped, mechanical edits, docs, config."},
    {"key": "codex",         "executor": "codex",  "model": None,
     "best_for": "Code-execution-heavy, test-driven loops; runs in its own TUI with its own approvals."},
]


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def sprint_path(thread_folder: Path) -> Path:
    return thread_folder / "sprint.json"


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def is_first_run(path: Path) -> bool:
    """True when there is no active, fully-answered sprint — i.e. the coordinator must ask Q1/Q2."""
    s = load(path)
    if not s or s.get("status") != "active":
        return True
    ans = s.get("answered", {})
    return not (ans.get("scope") and ans.get("model"))


def new_sprint(path: Path, thread: int, scope_description: str, tasks: list[dict],
               executor: str, model: str | None) -> dict:
    """Record a founder-approved sprint. `tasks` is an ordered list of {id, name?, agent}."""
    norm = []
    for t in tasks:
        norm.append({"id": t["id"], "name": t.get("name", ""), "agent": t.get("agent", ""),
                     "status": "pending", "started_utc": None, "ended_utc": None, "note": ""})
    sprint = {
        "sprint_id": f"sprint-{thread}-{datetime.datetime.now(datetime.timezone.utc):%Y%m%d-%H%M%S}",
        "thread": thread,
        "created_utc": _utc(),
        "scope_description": scope_description,
        "executor": executor,
        "model": model,
        "answered": {"scope": True, "model": True},
        "status": "active",
        "tasks": norm,
    }
    path.write_text(json.dumps(sprint, indent=2) + "\n", encoding="utf-8")
    return sprint


def current_task(sprint: dict):
    """The task now in flight, else the next pending one, else None (sprint drained)."""
    for t in sprint.get("tasks", []):
        if t["status"] == "running":
            return t
    for t in sprint.get("tasks", []):
        if t["status"] == "pending":
            return t
    return None


def mark(path: Path, task_id: str, status: str, note: str = "") -> dict:
    if status not in TASK_STATES:
        raise ValueError(f"status must be one of {TASK_STATES}")
    sprint = load(path)
    if sprint is None:
        raise FileNotFoundError(f"no sprint at {path}")
    found = False
    for t in sprint["tasks"]:
        if t["id"] == task_id:
            found = True
            t["status"] = status
            if note:
                t["note"] = note
            if status == "running" and not t["started_utc"]:
                t["started_utc"] = _utc()
            if status in ("done", "blocked"):
                t["ended_utc"] = _utc()
    if not found:
        raise KeyError(f"task {task_id} not in sprint")
    # sprint completes when no task is pending/running (all done or blocked)
    if all(t["status"] in ("done", "blocked") for t in sprint["tasks"]):
        sprint["status"] = "completed"
    path.write_text(json.dumps(sprint, indent=2) + "\n", encoding="utf-8")
    return sprint


def progress(sprint: dict) -> dict:
    tasks = sprint.get("tasks", [])
    done = sum(1 for t in tasks if t["status"] == "done")
    blocked = sum(1 for t in tasks if t["status"] == "blocked")
    cur = current_task(sprint)
    return {"done": done, "blocked": blocked, "total": len(tasks),
            "current": cur["id"] if cur else None, "status": sprint.get("status")}


def summary_line(sprint: dict) -> str:
    p = progress(sprint)
    cur = f"current {p['current']}" if p["current"] else "drained"
    blk = f", {p['blocked']} blocked" if p["blocked"] else ""
    return (f"sprint {sprint.get('sprint_id')} [{p['status']}] — {p['done']}/{p['total']} done{blk}; "
            f"{cur}; executor={sprint.get('executor')} model={sprint.get('model') or '(default)'}")


def model_menu_text() -> str:
    out = ["Q2 — LLM + model for this sprint's workers (pick one; override per task if needed):"]
    for m in MODEL_MENU:
        mdl = m["model"] or "default"
        out.append(f"  [{m['key']}]  {m['executor']} / {mdl}\n       → {m['best_for']}")
    out.append("Suggestion: match the hardest task in scope — HIGH→claude-opus, MEDIUM→claude-sonnet "
               "or codex, LOW→claude-haiku or codex.")
    return "\n".join(out)


def _parse_tasks(spec: str) -> list[dict]:
    """'SEQ-09:agent1-2:name,SEQ-17:agent1-1' → ordered task dicts."""
    tasks = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        tasks.append({"id": parts[0].strip(),
                      "agent": parts[1].strip() if len(parts) > 1 else "",
                      "name": parts[2].strip() if len(parts) > 2 else ""})
    return tasks


def main() -> int:
    ap = argparse.ArgumentParser(description="Sprint state for a thread coordinator")
    ap.add_argument("--thread-folder", required=True, help="path to thread<N>/ (holds sprint.json)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("models")
    sub.add_parser("show")
    sp = sub.add_parser("new")
    sp.add_argument("--thread", type=int, required=True)
    sp.add_argument("--scope", required=True)
    sp.add_argument("--tasks", required=True, help="ordered 'ID:agent[:name],...'")
    sp.add_argument("--executor", required=True)
    sp.add_argument("--model", default=None)
    mk = sub.add_parser("mark")
    mk.add_argument("--task", required=True)
    mk.add_argument("--status", required=True, choices=TASK_STATES)
    mk.add_argument("--note", default="")
    args = ap.parse_args()

    folder = Path(args.thread_folder).resolve()
    path = sprint_path(folder)

    if args.cmd == "models":
        print(model_menu_text()); return 0
    if args.cmd == "show":
        s = load(path)
        if not s:
            print("No sprint recorded for this thread. First run: ask Q1 (scope) + Q2 (model), then `new`.")
            return 0
        print(summary_line(s))
        for t in s["tasks"]:
            print(f"  {t['status']:<8} {t['id']:<12} {t.get('agent',''):<10} {t.get('name','')}")
        return 0
    if args.cmd == "new":
        folder.mkdir(parents=True, exist_ok=True)
        s = new_sprint(path, args.thread, args.scope, _parse_tasks(args.tasks), args.executor, args.model)
        print("Sprint recorded:"); print(summary_line(s)); return 0
    if args.cmd == "mark":
        s = mark(path, args.task, args.status, args.note)
        print(summary_line(s)); return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
