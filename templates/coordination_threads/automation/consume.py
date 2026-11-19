#!/usr/bin/env python3
"""Exactly-once result consumption + journaled single-writer reconciliation (P0-7).

The dispatcher must consume each completed dispatch's result exactly once and propose a
single canonical annotation for the Lead Coordinator to apply (proposal §6.1 — automation
NEVER writes canonical status itself). The journal is the exactly-once ledger, keyed on
(run_id, sequence); it is two-phase (record -> annotate) so a crash between phases is
recoverable on restart with no duplicate decision and no stale status.

An unaccepted result (a failed required gate) is still consumed, but yields a
FAILURE-EVIDENCE annotation, never a done-flip — preserving "never close without evidence"
and "a failed required test blocks acceptance".
"""
from __future__ import annotations
import hashlib, json, os, time, datetime
from pathlib import Path
import result as result_mod

LOCK = ".consume.lock"


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _key(result: dict) -> str:
    return f"{result.get('run_id')}::{result.get('sequence')}"


def _result_hash(result: dict) -> str:
    return hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()[:16]


def _acquire(path: Path, timeout: float = 5.0) -> None:
    lock = path.parent / LOCK
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd); return
        except FileExistsError:
            if time.time() > deadline:
                raise RuntimeError("consume journal lock busy")
            time.sleep(0.01)


def _release(path: Path) -> None:
    try:
        (path.parent / LOCK).unlink()
    except OSError:
        pass


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"entries": {}}


def _save(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))


def _annotation(result: dict, envelope: dict | None) -> dict:
    acc = result_mod.acceptance(result, envelope)
    kind = "done-proposal" if acc["accepted"] else "failure-evidence"
    return {
        "kind": kind,                       # the Lead Coordinator applies a done-proposal; never automation
        "canonical_task_ids": result.get("canonical_task_ids", []),
        "stage": result.get("stage"),
        "accepted": acc["accepted"],
        "accepted_at_stage": acc["accepted_at_stage"],
        "claims_live": acc["claims_live"],
        "reasons": acc["reasons"],
        "evidence_result": {"run_id": result.get("run_id"), "sequence": result.get("sequence"),
                            "result_hash": _result_hash(result)},
        "proposed_utc": _utc(),
        "note": "PROPOSED annotation for the Lead Coordinator; automation does not write canonical status.",
    }


def consume(result: dict, journal_path: Path, envelope: dict | None = None) -> dict:
    """Idempotent. First call records + annotates; a repeat call returns the SAME proposed
    annotation without a second decision. Returns {status, annotation, duplicate}."""
    journal_path = Path(journal_path)
    _acquire(journal_path)
    try:
        data = _load(journal_path)
        entries = data.setdefault("entries", {})
        k = _key(result)
        existing = entries.get(k)
        if existing and existing.get("phase") == "annotated":
            return {"status": "already-consumed", "annotation": existing["annotation"], "duplicate": True}
        if not existing:
            # phase 1: record intent (crash here -> phase 2 re-driven on restart, idempotent)
            entries[k] = {"phase": "recorded", "result_hash": _result_hash(result),
                          "recorded_utc": _utc()}
            _save(journal_path, data)
        # phase 2: produce the single proposed annotation and mark annotated
        ann = _annotation(result, envelope)
        entries[k]["phase"] = "annotated"
        entries[k]["annotation"] = ann
        entries[k]["annotated_utc"] = _utc()
        _save(journal_path, data)
        return {"status": "consumed", "annotation": ann, "duplicate": False}
    finally:
        _release(journal_path)


def resume_pending(journal_path: Path, results_by_key: dict, envelopes_by_key: dict | None = None) -> list[str]:
    """After a restart, re-drive any entry stuck in phase 'recorded' to 'annotated' using the
    same result, producing the same annotation. Returns the keys it completed."""
    journal_path = Path(journal_path)
    envelopes_by_key = envelopes_by_key or {}
    _acquire(journal_path)
    try:
        data = _load(journal_path)
        done = []
        for k, entry in data.get("entries", {}).items():
            if entry.get("phase") == "recorded" and k in results_by_key:
                entry["annotation"] = _annotation(results_by_key[k], envelopes_by_key.get(k))
                entry["phase"] = "annotated"
                entry["annotated_utc"] = _utc()
                done.append(k)
        if done:
            _save(journal_path, data)
        return done
    finally:
        _release(journal_path)
