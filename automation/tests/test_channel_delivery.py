"""File delivery, role routing and local-process proof. No AI or Terminal launches."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import channel_delivery as d
import architect_bridge as bridge
import architect_invoke as architect
import coordinator_trigger as trigger
import wave
import owner_sessions


def fixture_wave():
    return {"wave_id": "fixture", "status": "active", "verified_by_architect": True,
            "sprints": [{"id": f"S{n}", "thread": n, "status": "pending", "task_ids": [f"FIXTURE-{n}"],
                         "scope_review_ref": "fixture-review", "model_policy": "claude-opus",
                         "target_tier": "isolated-fixture", "founder_auth_ref": "TASK-12-file-proof",
                         "opening_round": 1} for n in (1, 2, 3)]}


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        p = patch.object(owner_sessions, 'OWNERS', self.root / 'owners'); p.start(); self.addCleanup(p.stop)
        for name, value in (("MAILBOX_ROOT", self.root / "mail"), ("ARTIFACT_ROOT", self.root),
                            ("DISPATCH_LOCK", self.root / "dispatch.lock")):
            p = patch.object(d, name, value); p.start(); self.addCleanup(p.stop)
        self.source = self.root / "source.md"; self.source.write_text("fixture request")
        self.identity = dict(recipient="architect", thread=1, wave_id="fixture", scope="a" * 64)

    def emit(self, **extra):
        return d.emit(**{**self.identity, "number": 1, "status": "AWAITING-ARCHITECT", "source": self.source, **extra})

    def round_read(self, **extra):
        return d.round_was_read(**{**self.identity, 'number':1, 'status':'AWAITING-ARCHITECT', 'source':self.source, **extra})

    def test_consumed_round_is_closed_across_source_only_edits(self):
        path=self.emit();self.assertFalse(self.round_read())
        d.acknowledge(path,**self.identity);self.source.write_text('recipient adds status and fixes a timestamp')
        self.assertTrue(self.round_read())
        self.assertFalse(self.round_read(number=2))
        self.assertFalse(self.round_read(status='REDIRECT'))
        self.assertFalse(self.round_read(scope='b'*64))
        self.assertFalse(self.round_read(recipient='coordinator'))

    def test_round_suppression_requires_exact_valid_read_receipt(self):
        path=self.emit();ack=d.acknowledge(path,**self.identity)
        a=json.loads(ack.read_text());a['source_sha256']='b'*64;ack.write_text(json.dumps(a))
        with self.assertRaisesRegex(ValueError,'acknowledgement'):self.round_read()

    def test_concurrent_repeated_delivery_is_one_unread_event(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            paths = list(pool.map(lambda _: self.emit(), range(20)))
        self.assertEqual(len(set(paths)), 1)
        self.assertEqual(len(d.pending(**self.identity)), 1)
        self.assertFalse(paths[0].with_suffix(".read.json").exists())

    def test_explicit_ack_is_read_only_and_survives_later_channel_changes(self):
        path = self.emit()
        d.acknowledge(path, **self.identity)
        d.acknowledge(path, **self.identity)
        self.assertEqual(json.loads(path.with_suffix(".read.json").read_text())["state"], "read")
        self.source.write_text("architect verdict now written")
        self.assertEqual(d.pending(**self.identity), [])

    def test_stale_unread_cannot_be_acknowledged(self):
        path = self.emit(); self.source.write_text("changed")
        with self.assertRaisesRegex(ValueError, "stale"):
            d.acknowledge(path, **self.identity)
        self.assertFalse(path.with_suffix(".read.json").exists())

    def test_recipient_and_scope_mismatch_fail(self):
        path = self.emit()
        for key, value in (("recipient", "coordinator"), ("thread", 2), ("wave_id", "foreign"), ("scope", "b" * 64)):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "mismatch"):
                d.load(path, **{**self.identity, key: value})

    def test_modified_event_and_ack_refused(self):
        path = self.emit(); raw = json.loads(path.read_text()); raw["round"] = 99
        path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(ValueError, "identity/content"):
            d.load(path, **self.identity)
        path.unlink(); path = self.emit(); ack = d.acknowledge(path, **self.identity)
        raw = json.loads(ack.read_text()); raw["state"] = "accepted"; ack.write_text(json.dumps(raw))
        with self.assertRaisesRegex(ValueError, "acknowledgement"):
            d.pending(**self.identity)

    def test_symlink_traversal_and_immutable_write_conflict(self):
        link = self.root / "linked.md"; link.symlink_to(self.source)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.emit(source=link)
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.emit(source=self.root / ".." / "outside")
        path = self.emit()
        with self.assertRaisesRegex(ValueError, "differs"):
            d.write_once(path, {"altered": True})
        outside = self.root / "outside.json"; outside.write_text("{}")
        path.unlink(); path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink"):
            d.load(path, **self.identity)

    def test_bounded_wait_and_pending_never_ack(self):
        args = ["--recipient", "architect", "--thread", "1", "--wave", "fixture", "--scope", "a" * 64]
        with redirect_stdout(io.StringIO()):
            self.assertEqual(d.main(["wait", *args, "--timeout", "0"]), 124)
            self.assertEqual(d.main(["wait", *args, "--timeout", "31"]), 2)
            self.emit()
            self.assertEqual(d.main(["pending", *args]), 0)
        self.assertEqual(len(d.pending(**self.identity)), 1)

    def test_current_wave_binding_and_boundary_only(self):
        w = fixture_wave(); sprint = w['sprints'][0]
        r = {"round": 2, "checkpoint": "conflict", "wave_id": "fixture", "scope_sha256": d.scope_sha(w, sprint)}
        self.assertIsNotNone(bridge.scoped_round(1, w, r))
        for changed in ({"wave_id": "foreign"}, {"scope_sha256": "b" * 64}, {"checkpoint": "pre-dispatch"}):
            self.assertIsNone(bridge.scoped_round(1, w, {**r, **changed}))
        w["status"] = "paused"
        self.assertIsNone(bridge.scoped_round(1, w, r))

    def test_direct_invocation_requires_both_gates(self):
        with patch.object(bridge, "_auto_enabled", return_value=True):
            self.assertIn("refused", architect.invoke(1, dry_run=False)["launch"])
        with patch.object(trigger, "_json", return_value={"auto_launch": "authorized"}):
            self.assertIn("refused", trigger.invoke(1, {}, fixture_wave(), dry_run=False)["launch"])

    def test_live_architect_queues_without_launch(self):
        w = fixture_wave(); self.source.rename(self.root / "thread1.md")
        with patch.object(bridge, "CHANNEL_DIR", str(self.root)), \
             patch.object(bridge, "_gates_open", return_value=True), \
             patch.object(wave, "active_wave", return_value=w), \
             patch.object(bridge, "scan", return_value=[{"thread": 1, "latest": {
                 "round": 1, "checkpoint": "conflict", "status": bridge.AWAITING, "bootstrap_wave": "fixture"}}]), \
             patch.object(bridge, "_load_cursor", return_value={}), patch.object(bridge, "_save_cursor"), \
             patch.object(d, "foreign_controller_conflict"), patch.object(d, "active_architect", return_value="live"), \
             patch.object(architect, "invoke") as invoke, redirect_stdout(io.StringIO()):
            result = bridge.auto_invoke_owed(True)
            self.assertIn("read acknowledgement pending", result[0]["skipped"])
            invoke.assert_not_called()

    def test_permission_uncertainty_blocks_actor_and_other_controllers(self):
        run = self.root / "actor"; run.mkdir(); (run / "coordinator.pid").write_text("123")
        with patch.object(d.os, "kill", side_effect=PermissionError):
            self.assertTrue(d.run_live(run))
        with patch.object(d, "HERE", self.root):
            marker = self.root / "var/sprint-loop/old/controller.pid"
            marker.parent.mkdir(parents=True); marker.write_text("123")
            with patch.object(d.os, "kill", side_effect=PermissionError), self.assertRaises(PermissionError):
                d.foreign_controller_conflict()

    def test_guard_is_reentrant_but_refuses_another_thread(self):
        with d.dispatch_guard():
            with d.dispatch_guard(): pass
            def competing():
                try:
                    with d.dispatch_guard(): return "wrong"
                except BlockingIOError: return "blocked"
            with ThreadPoolExecutor(max_workers=1) as pool:
                self.assertEqual(pool.submit(competing).result(), "blocked")

    def test_scope_prompts_and_explicit_profile_wiring(self):
        w = fixture_wave(); reason = {"trigger": "verdict", "round": {"round": 1, "status": "ALIGNED"}}
        with patch.object(trigger, "_json", return_value={"claude_profile": "alternate"}), \
             patch.object(trigger._sprint, "load", return_value={"executor": "claude", "model": "opus"}), \
             patch.object(trigger._vl, "launch_visible", return_value={}) as launch:
            record = trigger.invoke(1, reason, w, dry_run=True)
            self.assertEqual(launch.call_args.kwargs["claude_profile_dir"], trigger._vl.CLAUDE_PROFILES["alternate"])
            self.assertIn("channel_delivery.py", record["prompt"])
            self.assertNotIn("ALIGN before every dispatch", record["prompt"])
        self.assertNotIn("PRE-DISPATCH check", architect.boot_prompt(1, {"round": 1, "checkpoint": "conflict"}))

    def test_manual_and_wave_architect_entry_paths_share_single_flight(self):
        with patch.object(d, "foreign_controller_conflict"), \
             patch.object(d, "active_architect", return_value="existing"), \
             patch.object(architect._vl, "launch_visible") as launch:
            result = architect._launch_architect(self.root / "run", "claude-architect-manual", [], dry_run=False)
            self.assertIn("refused", result)
            launch.assert_not_called()

    def test_preview_has_no_delivery_side_effect(self):
        row = {"thread": 1, "latest": {"round": 1, "checkpoint": "conflict", "status": bridge.AWAITING}}
        with patch.object(bridge, "_gates_open", return_value=False), \
             patch.object(bridge, "scan", return_value=[row]), patch.object(bridge, "_load_cursor", return_value={}), \
             patch.object(architect, "invoke", return_value={"thread": 1, "round": row['latest'], "launch": {}}), \
             patch.object(d, "emit") as emit, redirect_stdout(io.StringIO()):
            bridge.auto_invoke_owed(False)
            emit.assert_not_called()
        self.assertFalse(d.MAILBOX_ROOT.exists())

    def test_multiple_thread_requests_queue_to_one_existing_architect(self):
        w = fixture_wave()
        rows = []
        for n in (1, 2):
            (self.root / f"thread{n}.md").write_text("fixture")
            rows.append({"thread": n, "latest": {"round": 1, "checkpoint": "conflict",
                        "status": bridge.AWAITING, "bootstrap_wave": "fixture"}})
        with patch.object(bridge, "CHANNEL_DIR", str(self.root)), \
             patch.object(bridge, "_gates_open", return_value=True), patch.object(wave, "active_wave", return_value=w), \
             patch.object(bridge, "scan", return_value=rows), patch.object(bridge, "_load_cursor", return_value={}), \
             patch.object(bridge, "_save_cursor"), patch.object(d, "foreign_controller_conflict"), \
             patch.object(d, "active_architect", return_value="same-owner"), \
             patch.object(architect, "invoke") as invoke, redirect_stdout(io.StringIO()):
            self.assertEqual(len(bridge.auto_invoke_owed(True)), 2)
            invoke.assert_not_called()
        self.assertEqual(len(list(d.MAILBOX_ROOT.rglob("*.json"))), 2)


# Harmless local process roles: they perform the file protocol, no AI CLI or product commands.
FIXTURE = r'''
import json,os,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1]); import channel_delivery as d
root=Path(sys.argv[2]); role=sys.argv[3]; scope=sys.argv[4]
d.ARTIFACT_ROOT=root; d.MAILBOX_ROOT=root/'mail'
channel=root/'channels/thread1.md'
identity=dict(recipient=role,thread=1,wave_id='fixture',scope=scope)
if role=='coordinator':
 channel.write_text('<!-- round:1 checkpoint:conflict status:AWAITING-ARCHITECT bootstrap:wave:fixture wave:fixture scope:'+scope+' -->\nFixture ownership question.\n')
 (root/'coordinator.ready').write_text(str(os.getpid()))
deadline=time.monotonic()+8
while time.monotonic()<deadline:
 events=d.pending(**identity)
 if events:
  d.acknowledge(events[0]['path'],**identity)
  old='AWAITING-ARCHITECT' if role=='architect' else 'ALIGNED'
  new='ALIGNED' if role=='architect' else 'GREEN'
  channel.write_text(channel.read_text().replace('status:'+old,'status:'+new))
  (root/(role+'.acted')).write_text(json.dumps({'pid':os.getpid(),'read_event':events[0]['id'],'status':new}))
  break
 time.sleep(.01)
else: raise SystemExit('fixture delivery timed out')
'''


class ProcessRoundTrip(unittest.TestCase):
    def test_existing_bridge_to_same_live_coordinator_no_duplicate(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary).resolve(); here = root / "automation"
            stack.enter_context(patch.object(owner_sessions, 'OWNERS', root / 'owners'))
            (root / "channels").mkdir(); (here / "var").mkdir(parents=True); (here / "config").mkdir()
            for name, value in (("architect_bridge.json", {"auto_writeback": "authorized"}),
                                ("coordinator_launch.json", {"auto_launch": "authorized", "claude_profile": "alternate"})):
                (here / "config" / name).write_text(json.dumps(value))
            w = fixture_wave(); scope = d.scope_sha(w, w["sprints"][0])
            actor = root / "actor.py"; actor.write_text(FIXTURE)
            coordinator = subprocess.Popen([sys.executable, str(actor), str(d.HERE), str(root), "coordinator", scope],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stack.callback(lambda: coordinator.poll() is None and coordinator.kill())
            until = time.monotonic() + 5
            while not (root / "coordinator.ready").exists():
                if time.monotonic() >= until: self.fail("fixture coordinator did not become ready")
                time.sleep(.01)
            coordinator_pid = int((root / "coordinator.ready").read_text())
            launched = []
            def local_actor(run_dir, executor, argv, **kwargs):
                launched.append(executor)
                self.assertEqual(executor, "claude-architect")
                self.assertIn("--print", argv)  # automatic role turn exits; no idle TUI lockout
                run_dir.mkdir(parents=True, exist_ok=True)
                result = subprocess.run([sys.executable, str(actor), str(Path(__file__).resolve().parent.parent),
                                         str(root), "architect", scope], capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                return {"window_id": "LOCAL-FIXTURE"}
            patches = [(d, "HERE", here), (d, "MAILBOX_ROOT", root / "mail"), (d, "ARTIFACT_ROOT", root),
                       (d, "DISPATCH_LOCK", here / "var/.coordinator-launch.lock"),
                       (bridge, "HERE", str(here)), (bridge, "VAR_DIR", str(here / "var")),
                       (bridge, "CHANNEL_DIR", str(root / "channels")),
                       (bridge, "AUTO_CURSOR", str(here / "var/architect.cursor.json")),
                       (architect, "RUNS_DIR", str(here / "var/architect-runs")),
                       (trigger, "LAUNCH_CFG", str(here / "config/coordinator_launch.json")),
                       (trigger, "CURSOR_PATH", str(here / "var/coordinator.cursor.json"))]
            for obj, name, value in patches: stack.enter_context(patch.object(obj, name, value))
            stack.enter_context(patch.object(wave, "active_wave", return_value=w))
            stack.enter_context(patch.object(trigger, "live_coordinator_run", side_effect=lambda n:
                "same-fixture-coordinator" if n == 1 and coordinator.poll() is None else None))
            stack.enter_context(patch.object(trigger._d, "write_status"))
            stack.enter_context(patch.object(architect._vl, "launch_visible", side_effect=local_actor))
            with redirect_stdout(io.StringIO()):
                bridge.auto_invoke_owed(True)
                bridge.auto_invoke_owed(True)  # response already written: no new architect
                result = trigger.tick(True)  # deliver to existing coordinator, never launch it
                trigger._print(result)
            self.assertIn("notification queued", result["results"][0]["skipped"])
            out, err = coordinator.communicate(timeout=10)
            self.assertEqual(coordinator.returncode, 0, err)
            self.assertEqual(json.loads((root / "coordinator.acted").read_text())["pid"], coordinator_pid)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(trigger.tick(True)["results"], [])  # GREEN cannot relaunch
            self.assertEqual(launched, ["claude-architect"])
            self.assertEqual(bridge._latest_round(str(root / "channels/thread1.md"))["status"], "GREEN")
            self.assertEqual(len(list((root / "mail").rglob("*.read.json"))), 2)
            report = {"proof": "existing bridge/request -> architect read+ALIGNED -> same coordinator read+GREEN",
                      "environment": "isolated local Python fixture actors; no AI/Terminal/product launch",
                      "architect_fixture_launches": 1, "coordinator_replacements": 0,
                      "coordinator_pid_preserved": True, "read_acks": 2, "final_status": "GREEN",
                      "architect_action": json.loads((root / "architect.acted").read_text()),
                      "coordinator_action": json.loads((root / "coordinator.acted").read_text()),
                      "read_receipts": [json.loads(p.read_text()) for p in sorted((root / "mail").rglob("*.read.json"))],
                      "final_channel_sha256": d.sha(root / "channels/thread1.md")}
            self.__class__.last_report = report


if __name__ == "__main__":
    unittest.main()
