#!/usr/bin/env python3
"""Fake-worker acceptance tests for dispatch_core (stage2-dispatcher-plan.md P0-2, P0-3, P1-b).

No real model, no shared app. Run:  python3 tests/test_dispatch_core.py
"""
from __future__ import annotations
import sys, time, threading, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import dispatch_core as dc          # noqa: E402
import fakeworker as fw             # noqa: E402


def _folder(tmp: str, task: str = "# Task\n\nRead alongside this task: x. What breaks?\n") -> Path:
    f = Path(tmp)
    (f / "task.md").write_text(task, encoding="utf-8")
    return f


class DispatchCoreTests(unittest.TestCase):

    def test_happy_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = fw.run_fake(_folder(tmp), "w1", "ok")
            self.assertTrue(out["claimed"] and out["completed"])
            self.assertIsNone(out["refused"])

    def test_concurrent_claim_exactly_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = _folder(tmp)
            env = dc.build_envelope(folder, 1, "r")
            results, errors = [], []

            def worker():
                try:
                    results.append(dc.claim(folder, "w", env["task_sha256"]))
                except dc.ClaimError as e:
                    errors.append(e)

            threads = [threading.Thread(target=worker) for _ in range(8)]
            for t in threads: t.start()
            for t in threads: t.join()
            self.assertEqual(len(results), 1, "exactly one claim must succeed")
            self.assertEqual(len(errors), 7)

    def test_orphan_cannot_complete_after_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = _folder(tmp)
            env = dc.build_envelope(folder, 1, "r1")
            # worker A claims with an already-expired lease, then "crashes" (never completes)
            a = dc.claim(folder, "A", env["task_sha256"], lease_s=-1.0)
            ack_a = dc.acknowledge(folder, env)
            # recovery: both lease expired and heartbeat stale -> reclaimed
            self.assertTrue(dc.recover(folder, lease_s=-1.0, heartbeat_s=-1.0))
            # worker B claims cleanly, gets a strictly greater fence
            b = dc.claim(folder, "B", env["task_sha256"])
            self.assertGreater(b["fence"], a["fence"])
            # orphan A returns and tries to complete with its stale fence -> refused
            with self.assertRaises(dc.FenceError):
                dc.complete(folder, a["fence"], ack_a, {"gate": "pass"})
            # B completes legitimately
            ack_b = dc.acknowledge(folder, env)
            done = dc.complete(folder, b["fence"], ack_b, {"gate": "pass"})
            self.assertEqual(done["status"], "completed")

    def test_recovery_requires_both_lease_and_heartbeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = _folder(tmp)
            env = dc.build_envelope(folder, 1, "r")
            dc.claim(folder, "A", env["task_sha256"], lease_s=-1.0)  # lease expired...
            # ...but heartbeat is fresh -> NOT an orphan, timeout alone is insufficient
            self.assertFalse(dc.recover(folder, lease_s=-1.0, heartbeat_s=9999.0))

    def test_second_live_claim_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = fw.run_fake(_folder(tmp), "A", "crash")   # A holds a live (fresh) claim
            self.assertTrue(out["claimed"])
            out2 = fw.run_fake(_folder(tmp), "B", "ok")      # B must be refused
            self.assertFalse(out2["claimed"])
            self.assertTrue(str(out2["refused"]).startswith("claim:"))

    def test_edited_task_completion_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = fw.run_fake(_folder(tmp), "A", "edit-task")
            self.assertTrue(out["claimed"])
            self.assertFalse(out["completed"])
            self.assertIn("StaleTaskError", str(out["refused"]))

    def test_stale_envelope_ack_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = _folder(tmp)
            env = dc.build_envelope(folder, 1, "r")
            (folder / "task.md").write_text("DIFFERENT\n", encoding="utf-8")  # edited after envelope
            with self.assertRaises(dc.StaleTaskError):
                dc.acknowledge(folder, env)

    def test_no_write_before_ack(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = fw.run_fake(_folder(tmp), "A", "no-ack")
            self.assertFalse(out["completed"])
            self.assertIn("AckError", str(out["refused"]))

    def test_missing_task_envelope_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(dc.StaleTaskError):
                dc.build_envelope(Path(tmp), 1, "r")   # no task.md

    def test_learning_fields_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dc.build_envelope(_folder(tmp), 1, "r")
            self.assertTrue(env["learning_present"])
        with tempfile.TemporaryDirectory() as tmp:
            env = dc.build_envelope(_folder(tmp, task="# Task\n\nno learning block here\n"), 1, "r")
            self.assertFalse(env["learning_present"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
