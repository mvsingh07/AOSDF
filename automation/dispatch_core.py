#!/usr/bin/env python3
"""Stage-2 dispatch core — immutable envelope + fenced claim/lease/heartbeat/recovery.

Built per stage2-dispatcher-plan.md (contracts P0-2, P0-3, P1-b). This module performs NO
launch and NO live operation. It is import-only and exercised by fakeworker.py + tests.

Safety properties it guarantees (validated by tests/test_dispatch_core.py):
  - Exactly one concurrent claim succeeds; a second claim on a live assignment is refused.
  - A completion/write is accepted ONLY from the holder of the CURRENT fence token, so an
    orphan or late worker that resumes with a stale fence can never record completion.
  - A worker must ACKNOWLEDGE the exact task (full SHA-256) before any write; a truncated,
    edited, missing or stale task input is rejected.
  - Recovery requires BOTH an expired lease AND a stale heartbeat (a timeout alone does not
    prove the old writer stopped) and is an explicit action, never automatic inside claim.

State lives in `<agent_folder>/.dispatch.json`; all mutations are serialized by a short-held
O_EXCL meta-lock `<agent_folder>/.dispatch.lock`. These are runtime files, not project state.
"""
from __future__ import annotations
import hashlib, json, os, time, datetime
from pathlib import Path

STATE_FILE = ".dispatch.json"
LOCK_FILE = ".dispatch.lock"


class DispatchError(RuntimeError):
    pass


class ClaimError(DispatchError):
    pass


class FenceError(DispatchError):
    pass


class StaleTaskError(DispatchError):
    pass


class AckError(DispatchError):
    pass


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _now() -> float:
    return time.time()


def task_sha256(folder: Path) -> str | None:
    p = folder / "task.md"
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def _has_learning(task_text: str) -> bool:
    """P1-b: a task carries learning context (reading links + a failure question)."""
    low = task_text.lower()
    return ("read alongside this task" in low) and ("?" in task_text)


# --- meta-lock + state io -----------------------------------------------------------------

def _acquire(folder: Path, timeout: float = 5.0) -> None:
    lock = folder / LOCK_FILE
    deadline = _now() + timeout
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            if _now() > deadline:
                raise ClaimError(f"{folder.name}: meta-lock busy (timeout)")
            time.sleep(0.01)


def _release(folder: Path) -> None:
    try:
        (folder / LOCK_FILE).unlink()
    except OSError:
        pass


def _load(folder: Path) -> dict:
    p = folder / STATE_FILE
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"last_fence": 0, "active": None, "history": []}


def _save(folder: Path, data: dict) -> None:
    tmp = folder / (STATE_FILE + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(folder / STATE_FILE))


def _is_orphan(active: dict, now: float, lease_s: float, heartbeat_s: float) -> bool:
    """Both conditions required: lease expired AND heartbeat stale."""
    lease = active.get("lease_expires_epoch")
    hb = active.get("heartbeat_epoch")
    if lease is None or hb is None:
        return False
    return now > lease and (now - hb) > heartbeat_s


# --- envelope + acknowledgement -----------------------------------------------------------

def build_envelope(folder: Path, sequence: int, run_id: str, now_utc: str | None = None) -> dict:
    sha = task_sha256(folder)
    if sha is None:
        raise StaleTaskError(f"{folder.name}: task.md missing — cannot build envelope")
    text = (folder / "task.md").read_text(encoding="utf-8", errors="replace")
    return {
        "agent_folder": str(folder),
        "sequence": sequence,
        "run_id": run_id,
        "task_sha256": sha,            # FULL sha256 (not truncated)
        "task_len": len(text),
        "created_utc": now_utc or _utc(),
        "learning_present": _has_learning(text),
    }


def acknowledge(folder: Path, envelope: dict) -> dict:
    """A worker must call this (and keep the token) before any write. Rejects a task that was
    truncated, edited, replaced or removed since the envelope was built."""
    sha = task_sha256(folder)
    if sha is None:
        raise StaleTaskError(f"{folder.name}: task.md missing at acknowledgement")
    if sha != envelope["task_sha256"]:
        raise StaleTaskError(f"{folder.name}: task.md changed since envelope "
                             f"(truncated/edited/stale) — refused")
    return {"ack_utc": _utc(), "task_sha256": sha, "run_id": envelope["run_id"]}


# --- fenced claim / lease / heartbeat / completion / recovery -----------------------------

def claim(folder: Path, owner: str, task_sha256_expected: str,
          lease_s: float = 900.0) -> dict:
    """Atomically claim the assignment. Exactly one concurrent caller succeeds; a second
    caller on a live (non-orphan) claim is refused. Returns the claim record incl. fence."""
    _acquire(folder)
    try:
        data = _load(folder)
        active = data.get("active")
        if active is not None:
            raise ClaimError(f"{folder.name}: already claimed by {active.get('owner')} "
                             f"(fence {active.get('fence')}); run recover() if it is an orphan")
        fence = int(data.get("last_fence", 0)) + 1
        now = _now()
        rec = {
            "fence": fence,
            "owner": owner,
            "claimed_utc": _utc(),
            "claimed_epoch": now,
            "lease_expires_epoch": now + lease_s,
            "heartbeat_epoch": now,
            "task_sha256": task_sha256_expected,
            "status": "running",
        }
        data["last_fence"] = fence
        data["active"] = rec
        _save(folder, data)
        return dict(rec)
    finally:
        _release(folder)


def heartbeat(folder: Path, fence: int, lease_s: float = 900.0) -> None:
    _acquire(folder)
    try:
        data = _load(folder)
        active = data.get("active")
        if not active or active.get("fence") != fence or active.get("status") != "running":
            raise FenceError(f"{folder.name}: heartbeat from a non-current fence {fence}")
        now = _now()
        active["heartbeat_epoch"] = now
        active["lease_expires_epoch"] = now + lease_s
        _save(folder, data)
    finally:
        _release(folder)


def complete(folder: Path, fence: int, ack: dict, result: dict) -> dict:
    """Record completion. Rejected unless the caller holds the CURRENT fence AND presented a
    valid ack AND the live task.md still matches (no mid-run replacement)."""
    _acquire(folder)
    try:
        data = _load(folder)
        active = data.get("active")
        if not active or active.get("fence") != fence:
            raise FenceError(f"{folder.name}: completion from stale/invalid fence {fence} "
                             f"(current {active.get('fence') if active else None}) — refused")
        if active.get("status") != "running":
            raise FenceError(f"{folder.name}: assignment not running (status {active.get('status')})")
        if not ack or ack.get("task_sha256") != active.get("task_sha256"):
            raise AckError(f"{folder.name}: completion without a valid acknowledgement — refused")
        live = task_sha256(folder)
        if live != active.get("task_sha256"):
            raise StaleTaskError(f"{folder.name}: task.md replaced during run — completion refused")
        active["status"] = "completed"
        active["result"] = result
        active["completed_utc"] = _utc()
        data.setdefault("history", []).append(active)
        data["active"] = None
        _save(folder, data)
        return dict(active)
    finally:
        _release(folder)


def release(folder: Path, fence: int) -> None:
    _acquire(folder)
    try:
        data = _load(folder)
        active = data.get("active")
        if active and active.get("fence") == fence:
            active["status"] = "released"
            active["released_utc"] = _utc()
            data.setdefault("history", []).append(active)
            data["active"] = None
            _save(folder, data)
    finally:
        _release(folder)


def health(folder: Path, heartbeat_s: float = 120.0, max_runtime_s: float = 3600.0) -> dict:
    """Classify the active claim for the watchdog. Lease is read from the claim (a heartbeat
    refreshes it), so an expired lease means heartbeats stopped. States:
      idle                          - no active claim
      healthy                       - heartbeating, lease valid, within runtime budget
      checkpoint_due                - healthy but running longer than max_runtime_s (compact + re-dispatch)
      lease_expired_heartbeat_fresh - lease lapsed but still heartbeating -> DO NOT take over
      orphan                        - lease expired AND heartbeat stale -> safe to recover
    """
    data = _load(Path(folder))
    active = data.get("active")
    if not active:
        return {"state": "idle", "active": None}
    now = _now()
    lease = active.get("lease_expires_epoch")
    hb = active.get("heartbeat_epoch")
    started = active.get("claimed_epoch")
    lease_expired = lease is not None and now > lease
    hb_stale = hb is not None and (now - hb) > heartbeat_s
    age = (now - started) if started else None
    checkpoint_due = age is not None and age > max_runtime_s
    if lease_expired and hb_stale:
        state = "orphan"
    elif lease_expired:
        state = "lease_expired_heartbeat_fresh"
    elif checkpoint_due:
        state = "checkpoint_due"
    else:
        state = "healthy"
    return {
        "state": state, "owner": active.get("owner"), "fence": active.get("fence"),
        "lease_expired": lease_expired, "heartbeat_stale": hb_stale,
        "seconds_since_heartbeat": round(now - hb, 1) if hb else None,
        "age_seconds": round(age, 1) if age is not None else None,
        "checkpoint_due": checkpoint_due,
    }


def recover(folder: Path, lease_s: float = 900.0, heartbeat_s: float = 120.0) -> bool:
    """Explicit stale-run recovery. Clears an active claim ONLY if it is a true orphan
    (expired lease AND stale heartbeat). Leaves last_fence intact so the next claim gets a
    strictly-greater fence and the orphan can never complete. Returns True if it reclaimed."""
    _acquire(folder)
    try:
        data = _load(folder)
        active = data.get("active")
        if not active:
            return False
        if not _is_orphan(active, _now(), lease_s, heartbeat_s):
            return False
        active["status"] = "orphaned"
        active["recovered_utc"] = _utc()
        data.setdefault("history", []).append(active)
        data["active"] = None
        _save(folder, data)
        return True
    finally:
        _release(folder)
