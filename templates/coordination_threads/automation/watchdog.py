#!/usr/bin/env python3
"""Heartbeat watchdog + checkpoint flagger — resilience to sleep/network/crash.

Classifies each agent's live claim (dispatch_core.health) and recovers true orphans safely:

  * ORPHAN  (lease expired AND heartbeat stale) = a crashed / slept / disconnected worker.
    `sweep` RECOVERS it — retiring its fence so it can never complete, and letting a fresh
    claim take a strictly-greater fence. No acknowledged work is lost (the task is immutable
    and re-read on resume) and no double-run can occur (fenced completion).
  * LEASE_EXPIRED_HEARTBEAT_FRESH = still heartbeating; a brief pause/sleep that resumed.
    NOT recovered — a timeout alone must never trigger a false takeover.
  * CHECKPOINT_DUE = a healthy but over-long run; the coordinator should request a clean
    checkpoint (worker writes context.md/As-built) and re-dispatch a FRESH session, which is
    how context stays compact. The watchdog only flags it; it does not kill the worker.

This module launches no worker and performs no live operation. `sweep` only clears dead
claims; re-dispatch stays with the coordinator (and, for real workers, the authorized pilot).
"""
from __future__ import annotations
from pathlib import Path
import dispatch_core as dc


def scan(config: dict, coord_root, heartbeat_s: float = 120.0, max_runtime_s: float = 3600.0) -> list[dict]:
    coord_root = Path(coord_root)
    rows = []
    for thread in config.get("threads", []):
        if thread.get("role") == "parked-planning-only":
            continue
        t = thread.get("thread")
        for ag in thread.get("agents", []):
            folder = coord_root / f"thread{t}" / ag["agent"]
            h = dc.health(folder, heartbeat_s=heartbeat_s, max_runtime_s=max_runtime_s)
            rows.append({"agent": ag["agent"], "thread": t, **h})
    return rows


def sweep(config: dict, coord_root, heartbeat_s: float = 120.0) -> list[str]:
    """Recover ORPHANS only (dispatch_core.recover re-checks both conditions). Returns the
    agents whose dead claims were cleared."""
    coord_root = Path(coord_root)
    reclaimed = []
    for thread in config.get("threads", []):
        if thread.get("role") == "parked-planning-only":
            continue
        t = thread.get("thread")
        for ag in thread.get("agents", []):
            folder = coord_root / f"thread{t}" / ag["agent"]
            if dc.recover(folder, heartbeat_s=heartbeat_s):
                reclaimed.append(ag["agent"])
    return reclaimed


def report_text(rows: list[dict]) -> str:
    lines = ["Agent        Thr Health                          since_hb  age(s)   fence"]
    for r in rows:
        shb = r.get("seconds_since_heartbeat")
        age = r.get("age_seconds")
        lines.append(f"{r['agent']:<12} {str(r['thread']):<3} {r['state']:<31} "
                     f"{str(shb if shb is not None else '-'):<9} "
                     f"{str(age if age is not None else '-'):<8} {str(r.get('fence') or '-')}")
    return "\n".join(lines)
