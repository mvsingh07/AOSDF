"""Fail-closed coordinator routing checks. Run: python3 tests/test_auto_mode_ready.py"""
from __future__ import annotations

import sys
import tempfile
import unittest
import io
import json
from contextlib import nullcontext, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import coordinator_trigger as trigger  # noqa: E402
import initiate_automation as initiate  # noqa: E402
import visible_launch  # noqa: E402
import wave  # noqa: E402


def approved_wave():
    return {
        "wave_id": "pilot", "status": "active", "verified_by_architect": True,
        "sprints": [
            {"id": "S6", "thread": 1, "status": "pending", "task_ids": ["AUTO-01"],
             "scope_review_ref": "review-1", "model_policy": "codex", "target_tier": "dev",
             "founder_auth_ref": "wave-approval", "opening_round": 12},
            {"id": "S12", "thread": 2, "status": "pending", "task_ids": ["M10-T11-W4"],
             "scope_review_ref": "review-2", "model_policy": "codex", "target_tier": "dev",
             "founder_auth_ref": "wave-approval", "opening_round": 12},
        ],
    }


class AutoModeRouting(unittest.TestCase):
    def test_each_thread_gets_its_own_sprint(self):
        w = approved_wave()
        self.assertEqual(wave.verified_thread_sprint(w, 1)["id"], "S6")
        self.assertEqual(wave.verified_thread_sprint(w, 2)["id"], "S12")
        self.assertIsNone(wave.verified_thread_sprint(w, 3))

    def test_unverified_or_incomplete_scope_never_launches(self):
        w = approved_wave()
        w["verified_by_architect"] = False
        self.assertIsNone(wave.verified_thread_sprint(w, 1))
        w["verified_by_architect"] = True
        w["sprints"][0].pop("task_ids")
        self.assertIsNone(wave.verified_thread_sprint(w, 1))
        w["sprints"][0]["task_ids"] = ["AUTO-01"]
        w["sprints"][0].pop("scope_review_ref")
        self.assertIsNone(wave.verified_thread_sprint(w, 1))

    def test_held_round_blocks_even_verified_wave(self):
        with patch.object(trigger._bridge, "_latest_round", return_value={"round": 11, "status": "HOLD"}):
            self.assertIsNone(trigger.owed(2, approved_wave()))

    def test_no_wave_or_free_form_note_cannot_launch(self):
        with patch.object(trigger._bridge, "_latest_round", return_value=None):
            self.assertIsNone(trigger.owed(1, None))
            self.assertIsNone(trigger.owed(1, {"status": "active", "sprints": []}))

    def test_old_round_does_not_start_new_wave(self):
        with patch.object(trigger._bridge, "_latest_round", return_value={"round": 11, "status": "ALIGNED"}):
            self.assertIsNone(trigger.owed(1, approved_wave()))

    def test_verified_sprint_and_verdict_launch_only_owner(self):
        with patch.object(trigger._bridge, "_latest_round", return_value={"round": 12, "status": "ALIGNED", "bootstrap_wave": "pilot"}):
            self.assertEqual(trigger.owed(2, approved_wave())["thread"], 2)
            self.assertIsNone(trigger.owed(3, approved_wave()))

    def test_green_ack_never_launches_same_sprint(self):
        with patch.object(trigger._bridge, "_latest_round", return_value={"round": 12, "status": "GREEN", "bootstrap_wave": "pilot"}):
            self.assertIsNone(trigger.owed(1, approved_wave()))

    def test_wrong_bootstrap_wave_refused(self):
        with patch.object(trigger._bridge, "_latest_round", return_value={"round": 12, "status": "ALIGNED", "bootstrap_wave": "other"}):
            self.assertIsNone(trigger.owed(1, approved_wave()))

    def test_bootstrap_marker_parsed_from_numbered_round_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "thread1.md"
            p.write_text("prose bootstrap:wave:other\n<!-- round:12 checkpoint:sprint status:ALIGNED bootstrap:wave:pilot -->\n")
            self.assertEqual(trigger._bridge._latest_round(str(p))["bootstrap_wave"], "pilot")

    def test_latest_round_with_hyphenated_checkpoint_is_not_missed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "thread1.md"
            p.write_text(
                "<!-- round:13 checkpoint:sprint status:GREEN opened:2026-10-31T11:50:00Z -->\n"
                "<!-- round:14 checkpoint:redline-correction status:AWAITING-ARCHITECT opened:2026-10-31T12:55:00Z -->\n"
            )
            latest = trigger._bridge._latest_round(str(p))
            self.assertEqual(latest, {"round": 14, "checkpoint": "redline-correction", "status": "AWAITING-ARCHITECT"})

    def test_failed_visible_launch_does_not_consume_cursor(self):
        reason = {"thread": 1, "trigger": "verdict", "round": {"round": 12, "status": "ALIGNED"}}
        with patch.object(trigger, "gate_open", return_value=True), \
             patch.object(trigger._wave, "active_wave", return_value=approved_wave()), \
             patch.object(trigger._bridge, "_thread_files", return_value=[(1, "thread1.md")]), \
             patch.object(trigger, "owed", return_value=reason), \
             patch.object(trigger, "invoke", return_value={"launch": {"error": "window failed"}}), \
             patch.object(trigger, "_json", return_value={}), \
             patch.object(trigger, "live_coordinator_run", return_value=None), \
             patch.object(trigger, "_launch_guard", return_value=nullcontext()), \
             patch.object(trigger, "_save_cursor") as save, \
             patch.object(trigger._d, "write_status"):
            trigger.tick(True)
            self.assertEqual(save.call_args.args[0], {})

    def test_live_coordinator_blocks_second_launch(self):
        reason = {"thread": 1, "trigger": "verdict", "round": {"round": 12, "status": "ALIGNED"}}
        with patch.object(trigger, "gate_open", return_value=True), \
             patch.object(trigger._wave, "active_wave", return_value=approved_wave()), \
             patch.object(trigger._bridge, "_thread_files", return_value=[(1, "thread1.md")]), \
             patch.object(trigger, "owed", return_value=reason), \
             patch.object(trigger, "live_coordinator_run", return_value="active-run"), \
             patch.object(trigger, "_launch_guard", return_value=nullcontext()), \
             patch.object(trigger, "_json", return_value={}), \
             patch.object(trigger, "invoke") as invoke, \
             patch.object(trigger, "_save_cursor"), \
             patch.object(trigger._d, "write_status"):
            result = trigger.tick(True)
            invoke.assert_not_called()
            self.assertIn("live coordinator", result["results"][0]["skipped"])

    def test_pid_marker_detects_live_session_and_ignores_dead_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "thread1" / "round12-ALIGNED"
            run.mkdir(parents=True)
            (run / "coordinator.pid").write_text("12345\n")
            with patch.object(trigger, "RUNS_DIR", tmp), patch.object(trigger, "_pid_alive", return_value=True):
                self.assertEqual(trigger.live_coordinator_run(1), str(run))
            with patch.object(trigger, "RUNS_DIR", tmp), patch.object(trigger, "_pid_alive", return_value=False):
                self.assertIsNone(trigger.live_coordinator_run(1))

    def test_legacy_window_is_blocked_while_process_alive(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "thread1" / "round5-ALIGNED"
            run.mkdir(parents=True)
            (run / "launch.json").write_text(json.dumps({"window_id": 123, "created_utc": "2020-01-01T00:00:00+00:00"}))
            with patch.object(trigger, "RUNS_DIR", tmp), patch.object(trigger, "_legacy_run_alive", return_value=True):
                self.assertEqual(trigger.live_coordinator_run(1), str(run))
            with patch.object(trigger, "RUNS_DIR", tmp), patch.object(trigger, "_legacy_run_alive", return_value=False):
                self.assertIsNone(trigger.live_coordinator_run(1))

    def test_coordinator_launcher_records_session_pid_without_changing_worker_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            coordinator = visible_launch.build_launch_script(run, ["true"], record_pid=True).read_text()
            self.assertIn("coordinator.pid", coordinator)
            worker = visible_launch.build_launch_script(run, ["true"]).read_text()
            self.assertNotIn("coordinator.pid", worker)

    def test_failed_architect_launch_does_not_consume_cursor(self):
        import architect_invoke
        bridge = trigger._bridge
        row = {"thread": 1, "latest": {"round": 12, "status": bridge.AWAITING}}
        with patch.object(bridge, "_gates_open", return_value=True), \
             patch.object(bridge, "scan", return_value=[row]), \
             patch.object(bridge, "_load_cursor", return_value={}), \
             patch.object(architect_invoke, "invoke", return_value={"thread": 1, "round": row["latest"], "launch": {"error": "window failed"}}), \
             patch.object(bridge, "_save_cursor") as save, redirect_stdout(io.StringIO()):
            bridge.auto_invoke_owed(True)
            self.assertEqual(save.call_args.args[0], {})

    def test_tracker_multi_owner_is_not_silently_thread_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = Path(tmp) / "SPRINT-TRACKER.md"
            tracker.write_text("| S12 — shared | scope | x | x | x | Planned | T1 + T2 |\n"
                               "| S6 — single | scope | x | x | x | Planned | T1 |\n")
            with patch.object(initiate, "SPRINT_TRACKER", str(tracker)):
                rows = {r["id"]: r for r in initiate._parse_sprint_rows()}
            self.assertIsNone(rows["S12"]["thread"])
            self.assertEqual(rows["S6"]["thread"], 1)

    def test_wave_completion_requires_evidence_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "wave.json")
            receipt = Path(tmp) / "accepted.md"
            wave.save(approved_wave(), path)
            with self.assertRaises(ValueError):
                wave.mark_sprint(path, "S6", "done")
            receipt.write_text("accepted task-bound sprint evidence")
            updated = wave.mark_sprint(path, "S6", "done", evidence_ref=str(receipt))
            self.assertEqual(updated["sprints"][0]["status"], "done")
            self.assertEqual(updated["sprints"][0]["evidence_ref"], str(receipt.resolve()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
