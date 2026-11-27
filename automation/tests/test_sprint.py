#!/usr/bin/env python3
"""Tests for sprint.py (founder direction 2026-10-23). Run: python3 tests/test_sprint.py"""
from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sprint  # noqa: E402


class TestSprint(unittest.TestCase):
    def test_first_run_true_when_no_sprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(sprint.is_first_run(sprint.sprint_path(Path(tmp))))

    def test_new_sprint_and_first_run_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = sprint.sprint_path(Path(tmp))
            s = sprint.new_sprint(p, 1, "SEQ-09 then SEQ-17",
                                  [{"id": "SEQ-09", "agent": "agent1-2"}, {"id": "SEQ-17", "agent": "agent1-1"}],
                                  "claude", "opus")
            self.assertEqual(s["status"], "active")
            self.assertEqual(len(s["tasks"]), 2)
            self.assertFalse(sprint.is_first_run(p))
            self.assertEqual(sprint.current_task(s)["id"], "SEQ-09")

    def test_mark_advances_and_completes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = sprint.sprint_path(Path(tmp))
            sprint.new_sprint(p, 1, "two", [{"id": "A", "agent": "x"}, {"id": "B", "agent": "y"}], "codex", None)
            s = sprint.mark(p, "A", "running")
            self.assertEqual(sprint.current_task(s)["id"], "A")
            s = sprint.mark(p, "A", "done")
            self.assertEqual(sprint.current_task(s)["id"], "B")   # advanced
            self.assertEqual(s["status"], "active")
            s = sprint.mark(p, "B", "done")
            self.assertEqual(s["status"], "completed")            # drained → completed
            self.assertIsNone(sprint.current_task(s))

    def test_blocked_counts_as_ended_for_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = sprint.sprint_path(Path(tmp))
            sprint.new_sprint(p, 2, "one", [{"id": "A", "agent": "x"}], "claude", "sonnet")
            s = sprint.mark(p, "A", "blocked", note="needs MA-065")
            self.assertEqual(s["status"], "completed")
            self.assertEqual(sprint.progress(s)["blocked"], 1)

    def test_mark_unknown_task_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = sprint.sprint_path(Path(tmp))
            sprint.new_sprint(p, 1, "one", [{"id": "A", "agent": "x"}], "claude", "opus")
            with self.assertRaises(KeyError):
                sprint.mark(p, "ZZZ", "done")

    def test_model_menu_has_all_executors(self):
        txt = sprint.model_menu_text()
        self.assertIn("claude-opus", txt)
        self.assertIn("codex", txt)
        self.assertIn("HIGH", txt)

    def test_parse_tasks(self):
        tasks = sprint._parse_tasks("SEQ-09:agent1-2:quotas, SEQ-17:agent1-1")
        self.assertEqual(tasks[0], {"id": "SEQ-09", "agent": "agent1-2", "name": "quotas"})
        self.assertEqual(tasks[1]["id"], "SEQ-17")
        self.assertEqual(tasks[1]["agent"], "agent1-1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
