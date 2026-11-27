#!/usr/bin/env python3
"""Bounded retry + progress policy (P0-10).

Stops after two unsuccessful corrections; refuses an analysis-only redispatch that carries no
new evidence (same evidence hash as the previous attempt); stops when the attempt budget is
exhausted. A new scope is reconciled first (handled by reconcile.py), not retried here.
"""
from __future__ import annotations
import datetime


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def empty_ledger() -> dict:
    return {"attempts": []}


def record_attempt(ledger: dict, outcome: str, evidence_hash: str, new_fact: bool | None = None) -> dict:
    """outcome in {'pass','fail'}. new_fact auto-derived (evidence differs from the previous
    attempt) when not given."""
    attempts = ledger.setdefault("attempts", [])
    prev_hash = attempts[-1]["evidence_hash"] if attempts else None
    if new_fact is None:
        new_fact = (evidence_hash != prev_hash)
    attempts.append({"outcome": outcome, "evidence_hash": evidence_hash,
                     "new_fact": bool(new_fact), "utc": _utc()})
    return ledger


def can_retry(ledger: dict, max_corrections: int = 2, budget: int = 5) -> tuple[bool, str]:
    attempts = ledger.get("attempts", [])
    if len(attempts) >= budget:
        return False, f"attempt budget exhausted ({len(attempts)}/{budget})"
    corrections = sum(1 for a in attempts if a["outcome"] == "fail")
    if corrections >= max_corrections:
        return False, f"{corrections} unsuccessful corrections — stop and report recovery path"
    if attempts and not attempts[-1]["new_fact"]:
        return False, "last attempt produced no new evidence (analysis-only) — do not redispatch"
    return True, "ok"
