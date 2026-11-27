#!/usr/bin/env python3
"""Tests for result.py (P0-6) and consume.py (P0-7). Run: python3 tests/test_result_consume.py"""
from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import result as R          # noqa: E402
import consume as C         # noqa: E402


def _result(stage="local", req_status="pass", with_evidence=True, task="abc", fence=2, run="r1", seq=1):
    return {
        "run_id": run, "sequence": seq, "agent": "agent1-1", "task_sha256": task, "fence": fence,
        "stage": stage, "created_utc": "2026-10-22T00:00:00+00:00",
        "canonical_task_ids": ["SEQ-17"],
        "gates": [
            {"name": "tsc", "kind": "required", "status": req_status,
             "evidence": "tsc 0 errors" if with_evidence else ""},
            {"name": "lint", "kind": "optional", "status": "skip"},
        ],
        "teaches": {"changed_behavior": "x", "example_ref": "y", "limitation": "z", "self_check": "q?"},
    }


class ResultTests(unittest.TestCase):

    def test_happy_accepted_at_its_stage(self):
        env = {"task_sha256": "abc", "fence": 2}
        acc = R.acceptance(_result(stage="local"), env)
        self.assertTrue(acc["accepted"])
        self.assertEqual(acc["accepted_at_stage"], "local")
        self.assertFalse(acc["claims_live"], "a local result must not claim live")

    def test_failed_required_gate_blocks_acceptance(self):
        env = {"task_sha256": "abc", "fence": 2}
        acc = R.acceptance(_result(req_status="fail"), env)
        self.assertFalse(acc["accepted"])
        self.assertIn("a required gate did not pass", acc["reasons"])

    def test_missing_evidence_refused(self):
        errors, _ = R.validate_result(_result(with_evidence=False))
        self.assertTrue(any("no evidence" in e for e in errors))

    def test_task_sha_mismatch_refused(self):
        ok, reasons = R.is_acceptable(_result(task="abc"), {"task_sha256": "DIFFERENT", "fence": 2})
        self.assertFalse(ok)
        self.assertTrue(any("mismatch" in r for r in reasons))

    def test_live_claim_only_from_live_stage(self):
        env = {"task_sha256": "abc", "fence": 2}
        self.assertTrue(R.acceptance(_result(stage="live"), env)["claims_live"])
        self.assertFalse(R.acceptance(_result(stage="shared"), env)["claims_live"])

    def test_required_gate_cannot_skip(self):
        r = _result()
        r["gates"][0]["status"] = "skip"
        errors, _ = R.validate_result(r)
        self.assertTrue(any("cannot be skipped" in e for e in errors))


class ConsumeTests(unittest.TestCase):

    def test_exactly_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            jp = Path(tmp) / "journal.json"
            env = {"task_sha256": "abc", "fence": 2}
            first = C.consume(_result(), jp, env)
            self.assertEqual(first["status"], "consumed")
            second = C.consume(_result(), jp, env)
            self.assertEqual(second["status"], "already-consumed")
            self.assertTrue(second["duplicate"])
            self.assertEqual(first["annotation"], second["annotation"])

    def test_two_consecutive_dispatches_each_consumed_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            jp = Path(tmp) / "journal.json"
            env = {"task_sha256": "abc", "fence": 2}
            a = C.consume(_result(run="r1", seq=1), jp, env)
            b = C.consume(_result(run="r2", seq=2), jp, env)
            self.assertEqual(a["status"], "consumed")
            self.assertEqual(b["status"], "consumed")
            import json
            data = json.loads(jp.read_text())
            self.assertEqual(len(data["entries"]), 2)

    def test_restart_resumes_partial_without_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            jp = Path(tmp) / "journal.json"
            # simulate a crash after phase-1 record, before annotate
            import json
            res = _result(run="r9", seq=9)
            jp.write_text(json.dumps({"entries": {"r9::9": {"phase": "recorded",
                          "result_hash": "x", "recorded_utc": "t"}}}))
            done = C.resume_pending(jp, {"r9::9": res}, {"r9::9": {"task_sha256": "abc", "fence": 2}})
            self.assertEqual(done, ["r9::9"])
            # a subsequent consume of the same key is a no-op (already annotated)
            again = C.consume(res, jp, {"task_sha256": "abc", "fence": 2})
            self.assertEqual(again["status"], "already-consumed")

    def test_failed_result_yields_failure_evidence_not_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            jp = Path(tmp) / "journal.json"
            out = C.consume(_result(req_status="fail"), jp, {"task_sha256": "abc", "fence": 2})
            self.assertEqual(out["annotation"]["kind"], "failure-evidence")
            self.assertFalse(out["annotation"]["accepted"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
