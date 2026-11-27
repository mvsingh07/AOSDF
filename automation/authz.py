#!/usr/bin/env python3
"""Explicit authorization records + secret redaction (P0-9).

Authorization is SEPARATE from execution and is keyed to the exact (action, environment,
target, effect). A record for effect=read does NOT authorize effect=mutate; a record for one
target does not cover another. The Stage-2 flag authorizes nothing by itself (it gates the
dispatcher, not a mutation/spend/deploy/send). An external read/smoke is not "safe" merely by
label — its effect must be declared and matched.
"""
from __future__ import annotations
import re, datetime

EFFECTS = ("read", "mutate", "spend", "deploy", "send", "delete")


class NotAuthorized(RuntimeError):
    pass


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def authorize(action: str, environment: str, target: str, effect: str, approved_by: str) -> dict:
    """Create an authorization record (an approval act, distinct from executing anything)."""
    if effect not in EFFECTS:
        raise ValueError(f"unknown effect {effect!r}")
    return {"action": action, "environment": environment, "target": target, "effect": effect,
            "approved_by": approved_by, "approved_utc": _utc()}


def _matches(rec: dict, request: dict) -> bool:
    return all(rec.get(k) == request.get(k) for k in ("action", "environment", "target", "effect"))


def is_authorized(records: list[dict], request: dict) -> bool:
    """request = {action, environment, target, effect}. Exact match on all four required."""
    if request.get("effect") not in EFFECTS:
        return False
    return any(_matches(r, request) for r in records)


def execute_guard(records: list[dict], request: dict, stage_authorized: bool = False) -> None:
    """Raise unless an explicit matching authorization exists. `stage_authorized` is the
    dispatcher's Stage-2 flag and is intentionally IGNORED here — it cannot authorize an
    effect. Only a matching record can."""
    if not is_authorized(records, request):
        raise NotAuthorized(
            f"no authorization for action={request.get('action')} env={request.get('environment')} "
            f"target={request.get('target')} effect={request.get('effect')} "
            f"(stage flag does not authorize effects)")


_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|authorization|bearer)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),
    re.compile(r"\bce_(?:live|trial|test)_[A-Za-z0-9]+"),
]


def redact(text: str) -> str:
    """Scrub obvious secret material before any evidence is written. Conservative, not a
    guarantee — secrets are still never requested or intentionally captured."""
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out
