#!/usr/bin/env python3
"""Watchdog resilience tests (sleep/network/crash). Run: python3 tests/test_watchdog.py"""
from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import dispatch_core as dc    # noqa: E402
import watchdog as W          # noqa: E402


def _folder(tmp):
    f = Path(tmp) / "thread1" / "agent1-1"
    f.mkdir(parents=True)
    (f / "task.md").write_text("# task\nRead alongside this task: x. what breaks?\n")
    return f


def _cfg():
    return {"threads": [{"thread": 1, "agents": [{"agent": "agent1-1"}]}]}


class WatchdogTests(unittest.TestCase):

    def test_healthy_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _folder(tmp)
            dc.claim(f, "w", dc.task_sha256(f))
            self.assertEqual(dc.health(f)["state"], "healthy")

    def test_orphan_detected_and_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _folder(tmp)
            dc.claim(f, "w", dc.task_sha256(f), lease_s=-1.0)   # lease already expired
            h = dc.health(f, heartbeat_s=-1.0)                  # heartbeat considered stale
            self.assertEqual(h["state"], "orphan")
            reclaimed = W.sweep(_cfg(), Path(tmp), heartbeat_s=-1.0)
            self.assertEqual(reclaimed, ["agent1-1"])
            self.assertEqual(dc.health(f)["state"], "idle")     # claim cleared

    def test_lease_expired_but_heartbeat_fresh_not_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _folder(tmp)
            dc.claim(f, "w", dc.task_sha256(f), lease_s=-1.0)   # lease expired...
            h = dc.health(f, heartbeat_s=9999.0)                # ...but heartbeat fresh
            self.assertEqual(h["state"], "lease_expired_heartbeat_fresh")
            reclaimed = W.sweep(_cfg(), Path(tmp), heartbeat_s=9999.0)
            self.assertEqual(reclaimed, [], "a fresh-heartbeat worker must not be taken over")

    def test_checkpoint_due_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _folder(tmp)
            dc.claim(f, "w", dc.task_sha256(f))
            h = dc.health(f, max_runtime_s=-1.0)                # any age exceeds the budget
            self.assertEqual(h["state"], "checkpoint_due")
            self.assertTrue(h["checkpoint_due"])

    def test_idle_when_no_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = _folder(tmp)
            self.assertEqual(dc.health(f)["state"], "idle")
            rows = W.scan(_cfg(), Path(tmp))
            self.assertEqual(rows[0]["state"], "idle")


if __name__ == "__main__":
    unittest.main(verbosity=2)
