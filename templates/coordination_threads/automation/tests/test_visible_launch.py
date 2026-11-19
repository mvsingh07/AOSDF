#!/usr/bin/env python3
"""Tests for visible_launch (founder direction 2026-10-23).

Dry-run only: these never open a real Terminal window. Run:
    python3 tests/test_visible_launch.py
"""
from __future__ import annotations
import sys, json, tempfile, unittest, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import visible_launch as vl  # noqa: E402


class TestVisibleLaunch(unittest.TestCase):
    def test_codex_argv_shape(self):
        argv = vl.codex_argv(Path("/repo/run"))
        self.assertEqual(argv[:2], ["codex", "exec"])
        self.assertIn("--sandbox", argv)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "read-only")
        # all safe tools disabled, prompt from stdin
        for d in vl.CODEX_DISABLES:
            self.assertIn(d, argv)
        self.assertEqual(argv[-1], "-")

    def test_codex_interactive_argv(self):
        argv = vl.codex_interactive_argv(Path("/repo/run"), "do the task")
        self.assertEqual(argv[0], "codex")
        self.assertNotIn("exec", argv)          # interactive, not headless exec
        self.assertIn("--cd", argv)
        self.assertEqual(argv[-1], "do the task")  # prompt is the positional instruction

    def test_claude_argv_fresh_vs_resume(self):
        fresh = vl.claude_argv(Path("/repo/run"), "do the task")
        self.assertNotIn("--resume", fresh)
        self.assertEqual(fresh[-1], "do the task")
        resumed = vl.claude_argv(Path("/repo/run"), "p", resume="abc-123")
        self.assertIn("--resume", resumed)
        self.assertEqual(resumed[resumed.index("--resume") + 1], "abc-123")

    def test_interactive_script_has_caffeinate_and_pty(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            script = vl.build_launch_script(run, ["codex", "exec", "-"])
            body = script.read_text()
            self.assertIn("caffeinate", body)
            self.assertIn("/usr/bin/script -q -F", body)
            self.assertNotIn(" | ", body)
            self.assertIn("terminal.log", body)
            self.assertTrue(script.stat().st_mode & 0o100)  # executable

    def test_script_exports_coordinator_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            env = vl.profile_env({"CLAUDE_CONFIG_DIR": "/Users/x/.claude-vu08",
                                  "CODEX_HOME": "", "ANTHROPIC_API_KEY": "secret"})
            self.assertEqual(env, {"CLAUDE_CONFIG_DIR": "/Users/x/.claude-vu08"})
            body = vl.build_launch_script(run, ["claude", "p"], env=env).read_text()
            self.assertIn("export CLAUDE_CONFIG_DIR=/Users/x/.claude-vu08\n", body)
            self.assertNotIn("CODEX_HOME", body)
            self.assertNotIn("secret", body)
            self.assertLess(body.index("export CLAUDE_CONFIG_DIR"), body.index("exec "))

    def test_build_script_stdin_redirect_for_codex(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            stdin = run / "worker-input.txt"
            stdin.write_text("prompt", encoding="utf-8")
            script = vl.build_launch_script(run, ["codex", "exec", "-"], stdin_file=stdin)
            self.assertIn("< ", script.read_text())
            self.assertIn("worker-input.txt", script.read_text())

    @unittest.skipUnless(sys.platform == "darwin", "macOS script command")
    def test_interactive_child_has_terminal_and_preserves_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            script = vl.build_launch_script(run, [sys.executable, "-c",
                "import os,sys; print('PTY=' + str(all(os.isatty(i) for i in (0,1,2)))); sys.exit(7)"])
            result = subprocess.run(["bash", str(script)], input="", text=True,
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertIn("PTY=True", result.stdout)
            self.assertIn("PTY=True", (run / "terminal.log").read_text())

    def test_dry_run_opens_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            rec = vl.launch_visible(run, "codex", ["codex", "exec", "-"],
                                    title="t", dry_run=True)
            self.assertTrue(rec["dry_run"])
            self.assertIsNone(rec["window_id"])
            self.assertIn("PREVIEW ONLY", rec["note"])
            # no launcher-once guard written on a preview
            self.assertFalse((run / ".launcher-once").exists())
            # but the script + applescript + view are produced for inspection
            self.assertTrue((run / "launch-visible.sh").exists())
            self.assertTrue((run / "VIEW.md").exists())
            self.assertIn('tell application "Terminal"', rec["applescript"])
            self.assertIn("front window", rec["applescript"])

    def test_applescript_sets_custom_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = vl.launch_visible(Path(tmp), "claude", ["claude", "p"],
                                    title='Example Project — agent1-1', dry_run=True)
            self.assertIn("set custom title of front window", rec["applescript"])
            self.assertIn("Example Project", rec["applescript"])

    def test_launch_record_is_json_serializable(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            vl.launch_visible(run, "codex", ["codex", "exec", "-"], title="t", dry_run=True)
            # launch.json written on preview and is valid JSON
            data = json.loads((run / "launch.json").read_text())
            self.assertEqual(data["executor"], "codex")
            self.assertTrue(data["dry_run"])


class InactiveTemplateTests(unittest.TestCase):
    def test_real_launch_refuses_without_opening_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = vl.launch_visible(Path(tmp), "codex", ["false"], title="inactive", dry_run=False)
            self.assertIn("refused", record)
            self.assertFalse((Path(tmp) / "launch.sh").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
