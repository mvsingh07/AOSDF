#!/usr/bin/env python3
"""Proposal-only reconciliation of the seeded coordination state vs reality (P0-1).

PROPOSES a reconciliation for the Lead Coordinator to apply; it NEVER writes state.json/
task.md (reviewer condition 2 + the user's "do not lose current work" constraint). It flags a
completed agent as do-not-redispatch and a running agent as do-not-take-over (verify the live
interactive session first), surfaces stale/seeded snapshots, and reports whether configured
canonical_watch paths exist.
"""
from __future__ import annotations
import hashlib, json, datetime
from pathlib import Path


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _digest(path: Path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def _parse_utc(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def propose_reconciliation(config: dict, coord_root, config_dir=None) -> dict:
    coord_root = Path(coord_root)
    agents_out = []
    for thread in config.get("threads", []):
        if thread.get("role") == "parked-planning-only":
            continue
        tnum = thread.get("thread")
        for ag in thread.get("agents", []):
            folder = coord_root / f"thread{tnum}" / ag["agent"]
            state = _load_json(folder / "state.json")
            task_path = folder / "task.md"
            task_digest = _digest(task_path) if task_path.exists() else None
            try:
                task_mtime = task_path.stat().st_mtime if task_path.exists() else None
            except OSError:
                task_mtime = None
            status = (state or {}).get("status")
            state_digest = (state or {}).get("task_digest")
            state_updated = _parse_utc((state or {}).get("updated_utc"))
            stale = (state_updated is not None and task_mtime is not None and task_mtime > state_updated + 1)
            ack = (task_digest is not None and task_digest == state_digest)

            if status == "completed":
                guard = "do-not-redispatch (completed)"
            elif status == "running":
                guard = "do-not-take-over (verify the live interactive session before any Stage-2 claim)"
            else:
                guard = "ok"
            needs = (state is None) or stale or (task_path.exists() and not ack)
            agents_out.append({
                "agent": ag["agent"], "thread": tnum,
                "state_status": status, "state_seq": (state or {}).get("dispatch_sequence"),
                "ack": ack, "stale": stale, "state_present": state is not None,
                "guard": guard,
                "proposal": "reconcile-needed" if needs else "ok",
                "notes": "seeded snapshot predates its task.md" if stale else "",
            })

    missing = []
    base = Path(config_dir) if config_dir else None
    if base is not None:
        for rel in config.get("canonical_watch", []):
            if not (base / rel).resolve().exists():
                missing.append(rel)

    return {
        "generated_utc": _utc(),
        "writes_performed": False,   # invariant: this tool never writes live state
        "agents": agents_out,
        "canonical_paths_ok": (base is None) or (not missing),
        "missing_canonical_paths": missing,
        "note": "PROPOSAL only. The Lead Coordinator applies reconciliations against the live "
                "dated record; automation does not overwrite state.json/task.md.",
    }


def propose_from_file(config_path) -> dict:
    config_path = Path(config_path).resolve()
    config = _load_json(config_path)
    if config is None:
        raise RuntimeError(f"cannot read config {config_path}")
    coord_root = (config_path.parent / config.get("coordination_root", "..")).resolve()
    return propose_reconciliation(config, coord_root, config_dir=config_path.parent)
