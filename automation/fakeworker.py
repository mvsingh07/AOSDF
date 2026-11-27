#!/usr/bin/env python3
"""Fake worker executable for Stage-2 mechanics validation (stage2-dispatcher-plan.md).

A fake worker exercises the dispatch_core contract with NO real model and NO shared app, so
race/restart/orphan behaviour can be validated safely. Behaviours:
  - "ok"         : claim -> ack -> complete with a passing result.
  - "fail-gate"  : claim -> ack -> complete with a FAILING required gate (not acceptance).
  - "crash"      : claim -> ack -> return WITHOUT completing (simulates a lost session/orphan).
  - "edit-task"  : claim -> ack -> rewrite task.md -> try to complete (must be refused).
  - "no-ack"     : claim -> try to complete WITHOUT acknowledging (must be refused).

Returns a plain dict describing the outcome; raises nothing for the refusal cases — it records
the refusal so a test can assert it.
"""
from __future__ import annotations
from pathlib import Path
import dispatch_core as dc


def run_fake(folder: Path, owner: str, behavior: str = "ok",
             sequence: int = 1, run_id: str = "fake-run") -> dict:
    folder = Path(folder)
    out: dict = {"owner": owner, "behavior": behavior, "claimed": False,
                 "completed": False, "refused": None, "fence": None}

    env = dc.build_envelope(folder, sequence=sequence, run_id=run_id)
    try:
        claim = dc.claim(folder, owner=owner, task_sha256_expected=env["task_sha256"])
    except dc.ClaimError as e:
        out["refused"] = f"claim:{e}"
        return out
    out["claimed"] = True
    out["fence"] = claim["fence"]

    if behavior == "no-ack":
        try:
            dc.complete(folder, claim["fence"], ack={}, result={"gate": "pass"})
            out["completed"] = True
        except dc.DispatchError as e:
            out["refused"] = f"complete:{type(e).__name__}:{e}"
        return out

    try:
        ack = dc.acknowledge(folder, env)
    except dc.StaleTaskError as e:
        out["refused"] = f"ack:{e}"
        return out

    if behavior == "crash":
        out["note"] = "returned without completing (orphan)"
        return out

    if behavior == "edit-task":
        (folder / "task.md").write_text("REPLACED MID-RUN\n", encoding="utf-8")

    result = {"gate": "fail" if behavior == "fail-gate" else "pass",
              "run_id": run_id, "sequence": sequence}
    try:
        dc.complete(folder, claim["fence"], ack=ack, result=result)
        out["completed"] = True
        out["result"] = result
    except dc.DispatchError as e:
        out["refused"] = f"complete:{type(e).__name__}:{e}"
    return out
