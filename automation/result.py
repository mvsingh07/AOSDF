#!/usr/bin/env python3
"""Structured result + gate-evidence validation (stage2-dispatcher-plan.md P0-6).

A result is accepted ONLY when it validates against its envelope and every REQUIRED gate
passes. design/local/shared/live stages are distinct: a dev/local result can never assert a
live-delivery acceptance. Incomplete (missing evidence) or mismatched (wrong task_sha256)
results are refused. Stdlib-only hand validation mirrors schema/result.schema.json.
"""
from __future__ import annotations

VALID_STAGES = ("design", "local", "shared", "live")
GATE_STATUS = ("pass", "fail", "skip")


def validate_result(result: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors block acceptance; warnings (e.g. missing learning
    fields) never gate engineering."""
    errors, warnings = [], []
    required = ["run_id", "sequence", "agent", "task_sha256", "fence", "stage", "gates", "created_utc"]
    for k in required:
        if k not in result or result[k] in (None, "", []):
            errors.append(f"missing required field: {k}")
    if result.get("stage") not in VALID_STAGES:
        errors.append(f"invalid stage: {result.get('stage')!r}")

    gates = result.get("gates")
    if not isinstance(gates, list) or not gates:
        errors.append("gates must be a non-empty list")
        gates = []
    for i, g in enumerate(gates):
        if not isinstance(g, dict):
            errors.append(f"gate[{i}] not an object"); continue
        if g.get("kind") not in ("required", "optional"):
            errors.append(f"gate[{i}] bad kind: {g.get('kind')!r}")
        if g.get("status") not in GATE_STATUS:
            errors.append(f"gate[{i}] bad status: {g.get('status')!r}")
        if g.get("kind") == "required" and g.get("status") == "skip":
            errors.append(f"gate[{i}] ({g.get('name')}) is required and cannot be skipped")
        if g.get("status") in ("pass", "fail") and not g.get("evidence"):
            errors.append(f"gate[{i}] ({g.get('name')}) has status {g.get('status')} but no evidence")

    for name in ("deferred", "new_files"):
        if name in result and (not isinstance(result[name], list) or any(not isinstance(item, str) for item in result[name])):
            errors.append(f"{name} must be a list of strings")

    teaches = result.get("teaches") or {}
    for k in ("changed_behavior", "example_ref", "limitation", "self_check"):
        if not teaches.get(k):
            warnings.append(f"learning field missing: teaches.{k}")
    return errors, warnings


def required_gates_pass(result: dict) -> bool:
    gates = result.get("gates") or []
    req = [g for g in gates if g.get("kind") == "required"]
    return bool(req) and all(g.get("status") == "pass" for g in req)


def is_acceptable(result: dict, envelope: dict) -> tuple[bool, list[str]]:
    """A result is acceptable iff it validates, matches the envelope's task, and every
    required gate passed. Returns (ok, reasons_if_not)."""
    errors, _ = validate_result(result)
    reasons = list(errors)
    if envelope is not None:
        if result.get("task_sha256") != envelope.get("task_sha256"):
            reasons.append("task_sha256 mismatch vs envelope (result answers a different task)")
        if "fence" in envelope and result.get("fence") != envelope.get("fence"):
            reasons.append("fence mismatch vs envelope")
    if not required_gates_pass(result):
        reasons.append("a required gate did not pass")
    return (not reasons), reasons


def acceptance(result: dict, envelope: dict | None = None) -> dict:
    """Acceptance is SCOPED TO THE RESULT'S STAGE. A local/dev pass is accepted at 'local',
    never promoted to 'live'. claims_live is true only for a passing stage=='live' result."""
    ok, reasons = is_acceptable(result, envelope) if envelope is not None else (
        (not validate_result(result)[0]) and required_gates_pass(result), [])
    stage = result.get("stage")
    return {
        "accepted": ok,
        "accepted_at_stage": stage if ok else None,
        "claims_live": bool(ok and stage == "live"),
        "reasons": reasons,
    }
