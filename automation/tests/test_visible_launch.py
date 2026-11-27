#!/usr/bin/env python3
"""Tests for visible_launch (founder direction 2026-10-23).

Dry-run only: these never open a real Terminal window. Run:
    python3 tests/test_visible_launch.py
"""
from __future__ import annotations
import sys, json, tempfile, unittest, subprocess
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import visible_launch as vl  # noqa: E402


class TestVisibleLaunch(unittest.TestCase):
    def setUp(self):
        # The source choices are intentionally editable by the operator. Each
        # test declares its own choices; do not change a live account selection
        # merely to exercise the inheritance/default contract.
        for name in ('CLAUDE_PROFILE_DIR', 'CODEX_PROFILE_DIR'):
            selected = patch.object(vl, name, None)
            selected.start(); self.addCleanup(selected.stop)

    def test_editable_source_choices_win_per_call_and_stay_executor_specific(self):
        with tempfile.TemporaryDirectory() as selected, tempfile.TemporaryDirectory() as per_call, \
                patch.dict(vl.os.environ, {"CLAUDE_CONFIG_DIR": "/inherited-claude", "CODEX_HOME": "/inherited-codex"}, clear=True), \
                patch.object(vl, "CLAUDE_PROFILE_DIR", Path(selected)), \
                patch.object(vl, "CODEX_PROFILE_DIR", Path(per_call)):
            claude = vl.launch_profile("claude-worker", ["claude", "prompt"], per_call)
            self.assertEqual(claude, {"CLAUDE_CONFIG_DIR": str(Path(selected).resolve()), "CODEX_HOME": "/inherited-codex"})
            codex = vl.launch_profile("codex-coordinator", ["codex", "prompt"], codex_profile_dir=selected)
            self.assertEqual(codex, {"CLAUDE_CONFIG_DIR": "/inherited-claude", "CODEX_HOME": str(Path(per_call).resolve())})
            self.assertEqual(vl.os.environ["CODEX_HOME"], "/inherited-codex")

    def test_codex_override_rejects_resume_but_allows_config_and_prompt_values(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(vl, "CODEX_PROFILE_DIR", Path(tmp)):
            for argv in (["codex", "resume", "id"], ["codex", "exec", "resume", "id"],
                         ["codex", "--model", "model", "fork", "id"], ["codex", "--resume=id"]):
                with self.subTest(argv=argv), self.assertRaisesRegex(ValueError, "fresh session"):
                    vl.launch_profile("codex", argv)
            for argv in (["codex", "exec", "-c", "resume", "prompt"],
                         ["codex", "--model", "resume", "prompt"],
                         ["codex", "--", "resume"], ["codex", "please resume the task"]):
                with self.subTest(argv=argv):
                    self.assertEqual(vl.launch_profile("codex", argv)["CODEX_HOME"], str(Path(tmp).resolve()))

    def test_source_claude_choice_rejects_continue_fork_and_resume_aliases(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(vl, "CLAUDE_PROFILE_DIR", tmp):
            for flag in ("--fork-session", "--resume=id", "--continue", "-r", "-c"):
                with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, "fresh session"):
                    vl.launch_profile("claude", ["claude", flag, "prompt"])

    def test_codex_per_call_override_validation_and_generated_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            for executor, path in (("claude", tmp), ("codex", "relative"), ("codex", tmp + "/missing")):
                with self.subTest(executor=executor,path=path), self.assertRaises(ValueError):
                    vl.launch_profile(executor, [], codex_profile_dir=path)
            with patch.object(vl.subprocess, "run") as opened:
                result = vl.launch_visible(Path(tmp) / "run", "codex", ["codex", "prompt"],
                                           title="preview", dry_run=True, codex_profile_dir=tmp)
                opened.assert_not_called()
                self.assertEqual(result["profile_env"]["CODEX_HOME"], str(Path(tmp).resolve()))
                self.assertIn("export CODEX_HOME=", Path(result["script"]).read_text())

    def test_explicit_profile_is_per_launch_and_preserves_codex(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(vl.os.environ,
                {"CLAUDE_CONFIG_DIR": "/inherited", "CODEX_HOME": "/codex"}, clear=True):
            self.assertEqual(vl.launch_profile("claude", []),
                             {"CLAUDE_CONFIG_DIR": "/inherited", "CODEX_HOME": "/codex"})
            env = vl.launch_profile("claude-coordinator", [], tmp)
            self.assertEqual(env, {"CLAUDE_CONFIG_DIR": str(Path(tmp).resolve()), "CODEX_HOME": "/codex"})
            self.assertEqual(vl.os.environ["CLAUDE_CONFIG_DIR"], "/inherited")

    def test_profile_rejects_invalid_path_executor_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            for executor, argv, path in [("codex", [], tmp), ("claude", [], "relative"),
                    ("claude", [], tmp + "/missing"), ("claude", ["--resume", "id"], tmp),
                    ("claude", ["--resume=id"], tmp), ("claude", ["--continue"], tmp)]:
                with self.subTest(executor=executor, argv=argv, path=path), self.assertRaises(ValueError):
                    vl.launch_profile(executor, argv, path)

    def test_secret_env_cannot_be_exported(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
            vl.build_launch_script(Path(tmp), ["claude"], env={"ANTHROPIC_API_KEY": "never-export"})

    def test_profile_shell_quoting_does_not_execute(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            value = "profile $(touch SHOULD-NOT-EXIST) ' with spaces"
            body = vl.build_launch_script(run, ["true"], env={"CLAUDE_CONFIG_DIR": value}).read_text()
            self.assertIn(vl.shlex.quote(value), body)

    def test_real_launch_reservation_and_preview_cannot_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(vl.subprocess, "run") as opened:
            opened.return_value = subprocess.CompletedProcess([], 0, stdout="42", stderr="")
            run = Path(tmp)
            first = vl.launch_visible(run, "claude", ["claude", "first"], title="first")
            before = {p.name: p.read_bytes() for p in run.iterdir() if p.is_file()}
            second = vl.launch_visible(run, "claude", ["claude", "different"], title="different", dry_run=True)
            self.assertEqual(first["window_id"], "42")
            self.assertIn("refused", second)
            self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir() if p.is_file()})
            self.assertEqual(opened.call_count, 1)

    def test_failed_launch_is_sticky(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(vl.subprocess, "run") as opened:
            opened.return_value = subprocess.CompletedProcess([], 1, stdout="", stderr="Terminal refused")
            run = Path(tmp)
            self.assertIn("error", vl.launch_visible(run, "claude", ["claude"], title="t"))
            self.assertIn("refused", vl.launch_visible(run, "claude", ["claude"], title="t"))
            self.assertEqual(opened.call_count, 1)

    def test_generated_view_metadata_has_unique_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a", Path(tmp) / "b"
            a.mkdir(); b.mkdir()
            texts = [vl.write_view(p, "t", "claude").read_text() for p in (a, b)]
            for text in texts:
                self.assertTrue(text.startswith("---\n"))
                self.assertIn('document_schema: "aosdf-doc/v1"', text)
            self.assertNotEqual(texts[0].split('id: ')[1].splitlines()[0],
                                texts[1].split('id: ')[1].splitlines()[0])

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
            env = vl.profile_env({"CLAUDE_CONFIG_DIR": "/Users/x/.claude-alternate",
                                  "CODEX_HOME": "", "ANTHROPIC_API_KEY": "secret"})
            self.assertEqual(env, {"CLAUDE_CONFIG_DIR": "/Users/x/.claude-alternate"})
            body = vl.build_launch_script(run, ["claude", "p"], env=env).read_text()
            self.assertIn("export CLAUDE_CONFIG_DIR=/Users/x/.claude-alternate\n", body)
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
                                    title='Supagram — agent1-1', dry_run=True)
            self.assertIn("set custom title of front window", rec["applescript"])
            self.assertIn("Supagram", rec["applescript"])

    def test_launch_record_is_json_serializable(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            vl.launch_visible(run, "codex", ["codex", "exec", "-"], title="t", dry_run=True)
            # launch.json written on preview and is valid JSON
            data = json.loads((run / "launch.json").read_text())
            self.assertEqual(data["executor"], "codex")
            self.assertTrue(data["dry_run"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
