#!/usr/bin/env python3
"""wave.py — the automation WAVE: the founder's one-time autonomy envelope.

A *sprint* (sprint.py) is one coordinator execution over a set of tasks. A *wave* sits one level
above: it is one or many sprints the founder authorizes IN ONE GO at the start, after which the
Solution Architect and the coordinators proceed sprint-by-sprint WITHOUT further founder approval,
escalating only at a genuine stop condition (a hard gate, a real blocker, or wave end).

Founder direction (2026-10-28): "define an automation wave scope that can constitute one or many
sprints in one go, to the solution architect when we launch it for the first time; otherwise it
can keep moving as required automatically without any approval from a human."

So the wave is read by the architect on its FIRST launch of the wave and injected into its boot
prompt (see architect_invoke.boot_prompt). It changes *when* the human is asked, never *what* is
gated: every hard gate in AGENTS.md/ADRs still stops the wave cold via ESCALATE.

File: config/wave.json  (copy config/wave.example.json; absent = no wave = Easy-Mode per-sprint).
Stdlib-only; writes only config/wave.json.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(HERE, "config")
WAVE_PATH = os.path.join(CONFIG_DIR, "wave.json")

SPRINT_STATES = ("pending", "running", "done", "blocked")
WAVE_STATES = ("active", "paused", "complete")

HARD_GATES = (
    "push/deploy/publish, DNS changes, live email send, spend, secrets/Keychain, "
    "live-data deletion, or any Class-B/Class-C manual action"
)

# Plan/tracker ownership split (founder directive 2026-10-29). Injected into agent boot prompts so
# the division is carried by every launched session, not just documented.
OWNERSHIP_ARCHITECT = (
    "PLAN OWNERSHIP: Captain creates/replans; Solution Architect is sole ongoing canonical "
    "execution_plan.md writer. Register addendum rows and sprint mapping before implementation. "
    "Reconcile accepted evidence without routine technical review or suite reruns. "
    "Coordinators own their sprint/tracker row; workers report result/As-built deltas only. "
    "Read current-workflow-rules for C1-C13; no automatic extra review or plan revision."
)
OWNERSHIP_COORDINATOR = (
    "PLAN OWNERSHIP: write only your own sprint/tracker row and context; never execution_plan.md. "
    "Workers write owned task evidence, not tracker status. Report canonical deltas to SA. "
    "Route ownership conflict/sprint completion/ambiguity to SA; no per-result reapproval."
)


def _utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path: str = WAVE_PATH) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save(wave: dict, path: str = WAVE_PATH) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(wave, fh, indent=2)
    os.replace(tmp, path)


def active_wave(path: str = WAVE_PATH) -> dict | None:
    w = load(path)
    return w if (w and w.get("status") == "active") else None


def progress(wave: dict) -> dict:
    sprints = wave.get("sprints", [])
    done = sum(1 for s in sprints if s.get("status") == "done")
    blocked = sum(1 for s in sprints if s.get("status") == "blocked")
    running = sum(1 for s in sprints if s.get("status") == "running")
    return {"done": done, "running": running, "blocked": blocked, "total": len(sprints)}


def current_sprint(wave: dict) -> dict | None:
    """The next sprint to act on: first running, else first pending."""
    sprints = wave.get("sprints", [])
    for s in sprints:
        if s.get("status") == "running":
            return s
    for s in sprints:
        if s.get("status") == "pending":
            return s
    return None


def thread_sprint(wave: dict | None, thread_n: int) -> dict | None:
    """Select this thread's first running/pending sprint, never another thread's."""
    if not wave or wave.get("status") != "active":
        return None
    candidates = [s for s in wave.get("sprints", []) if s.get("thread") == thread_n]
    for state in ("running", "pending"):
        for sprint in candidates:
            if sprint.get("status") == state:
                return sprint
    return None


def verified_thread_sprint(wave: dict | None, thread_n: int) -> dict | None:
    """Fail closed until the architect records exact scope and versioned review."""
    sprint = thread_sprint(wave, thread_n)
    if not sprint or not wave.get("verified_by_architect"):
        return None
    task_ids = sprint.get("task_ids")
    if not isinstance(task_ids, list) or not task_ids or any(not isinstance(i, str) or not i.strip() for i in task_ids):
        return None
    if not sprint.get("scope_review_ref") or not sprint.get("model_policy"):
        return None
    if not sprint.get("target_tier") or not sprint.get("founder_auth_ref"):
        return None
    if not isinstance(sprint.get("opening_round"), int) or sprint["opening_round"] < 1:
        return None
    return sprint


def summary_line(wave: dict | None) -> str:
    if not wave:
        return "no active wave (Easy-Mode: per-sprint founder approval)"
    p = progress(wave)
    cur = current_sprint(wave)
    cur_txt = f" | next: {cur['id']} T{cur.get('thread','?')}" if cur else " | all sprints resolved"
    return (f"{wave.get('wave_id','?')} [{p['done']}/{p['total']} sprints"
            + (f", {p['blocked']} blocked" if p['blocked'] else "")
            + f"] {wave.get('status','?')}{cur_txt}")


def boot_addendum(wave: dict | None) -> str:
    """Text appended to the architect's boot prompt on a wave launch. Empty when no wave is active."""
    if not wave:
        return ""
    lines = [
        "",
        "AUTOMATION WAVE IN EFFECT — this is a founder-authorized multi-sprint envelope "
        f"({wave.get('wave_id')}): \"{wave.get('title','')}\".",
        f"Objective: {wave.get('objective','(see sprints)')}",
        "Sprints in this wave (ordered):",
    ]
    for s in wave.get("sprints", []):
        lines.append(f"  - {s.get('id')}  (Thread {s.get('thread','?')}, status {s.get('status','pending')}): "
                     f"{s.get('scope','')}")
    lines += [
        "You are authorized to confirm the partition for, and advance through, ALL sprints in this "
        "wave WITHOUT returning to the founder between sprints. Keep the thread partitions correct and "
        "non-overlapping as each sprint opens. Proceed autonomously (ALIGNED/REDIRECT as needed).",
        "STOP and ESCALATE (naming exactly what the founder must decide) ONLY for: a hard gate "
        f"[{HARD_GATES}]; a genuine blocker (missing authority/credentials, a validation gate failing "
        "twice, non-serializable ownership overlap, real objective ambiguity); or wave completion. "
        "Nothing else returns to the human until the wave ends.",
    ]
    return "\n".join(lines)


def define(*, wave_id: str, title: str, objective: str, sprints: list[dict]) -> dict:
    for s in sprints:
        s.setdefault("status", "pending")
    wave = {
        "wave_id": wave_id,
        "title": title,
        "objective": objective,
        "created_utc": _utc(),
        "autonomous": True,
        "verified_by_architect": False,
        "status": "active",
        "stop_conditions": [
            f"any hard gate ({HARD_GATES})",
            "a genuine blocker (missing authority/creds, a gate failing twice, ownership overlap, ambiguity)",
            "wave completion (all sprints done)",
        ],
        "sprints": sprints,
    }
    return wave


def mark_sprint(path: str, sprint_id: str, status: str, note: str = "", evidence_ref: str = "") -> dict:
    if status not in SPRINT_STATES:
        raise ValueError(f"status must be one of {SPRINT_STATES}")
    if status in ("done", "blocked") and (not evidence_ref or not Path(evidence_ref).is_file()):
        raise ValueError("done/blocked requires an existing sprint acceptance or blocker evidence file")
    wave = load(path)
    if not wave:
        raise FileNotFoundError("no wave to update")
    found = False
    for s in wave.get("sprints", []):
        if s.get("id") == sprint_id:
            s["status"] = status
            if note:
                s["note"] = note
            if evidence_ref:
                s["evidence_ref"] = str(Path(evidence_ref).resolve())
            s["updated_utc"] = _utc()
            found = True
            break
    if not found:
        raise KeyError(f"sprint {sprint_id} not in wave")
    # Auto-complete the wave when every sprint is resolved done.
    sprints = wave.get("sprints", [])
    if sprints and all(s.get("status") == "done" for s in sprints):
        wave["status"] = "complete"
        wave["completed_utc"] = _utc()
    save(wave, path)
    return wave


def _parse_sprints(spec: str) -> list[dict]:
    """'S1:2:scope text;S2:2:other scope' -> list of sprint dicts (id:thread:scope, ; separated)."""
    out = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(":", 2)
        if len(parts) < 3:
            raise ValueError(f"bad sprint spec {chunk!r}; want 'ID:THREAD:scope'")
        out.append({"id": parts[0].strip(), "thread": int(parts[1]), "scope": parts[2].strip(),
                    "status": "pending"})
    if not out:
        raise ValueError("no sprints parsed")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Define / show / advance the automation wave.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("define", help="create config/wave.json (overwrites any existing wave)")
    d.add_argument("--id", required=True, dest="wave_id")
    d.add_argument("--title", required=True)
    d.add_argument("--objective", default="")
    d.add_argument("--sprints", required=True, help="'ID:THREAD:scope;ID:THREAD:scope' (ordered)")

    sub.add_parser("show", help="print the current wave + progress")

    m = sub.add_parser("mark", help="set a sprint's status")
    m.add_argument("--sprint", required=True)
    m.add_argument("--status", required=True, choices=SPRINT_STATES)
    m.add_argument("--note", default="")
    m.add_argument("--evidence-ref", default="", help="required existing acceptance/blocker file for done/blocked")

    st = sub.add_parser("set-status", help="pause/resume/complete the whole wave")
    st.add_argument("--status", required=True, choices=WAVE_STATES)

    a = ap.parse_args(argv)

    if a.cmd == "define":
        wave = define(wave_id=a.wave_id, title=a.title, objective=a.objective,
                      sprints=_parse_sprints(a.sprints))
        save(wave)
        print(f"wave written: {WAVE_PATH}")
        print(summary_line(wave))
        return 0
    if a.cmd == "show":
        wave = load()
        if not wave:
            print("no wave defined (config/wave.json absent). Easy-Mode: per-sprint approval.")
            return 0
        print(summary_line(wave))
        print(json.dumps(wave, indent=2))
        return 0
    if a.cmd == "mark":
        wave = mark_sprint(WAVE_PATH, a.sprint, a.status, a.note, a.evidence_ref)
        print(summary_line(wave))
        return 0
    if a.cmd == "set-status":
        wave = load()
        if not wave:
            print("no wave to update.")
            return 2
        wave["status"] = a.status
        wave["updated_utc"] = _utc()
        save(wave)
        print(summary_line(wave))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
