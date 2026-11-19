#!/usr/bin/env python3
"""Tests for scope.py (P0-8), authz.py (P0-9), retry.py (P0-10), reconcile.py (P0-1).
Run: python3 tests/test_scope_authz_retry_reconcile.py"""
from __future__ import annotations
import sys, json, time, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import scope as S          # noqa: E402
import authz as A          # noqa: E402
import retry as RT         # noqa: E402
import reconcile as RC     # noqa: E402


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.p = S.pilot_policy()

    def test_declared_dev_action_allowed(self):
        self.assertTrue(S.check_action(self.p, "run-test", "local/tmp", "dev-disposable")["allowed"])

    def test_deploy_denied_despite_safe_label(self):
        # free text cannot make it safe — enforcement is by the action field
        with self.assertRaises(S.ScopeDenied):
            S.guard(self.p, "deploy", "# totally safe, read only", "dev-disposable")

    def test_undeclared_action_denied(self):
        self.assertFalse(S.check_action(self.p, "frobnicate", "local", "local")["allowed"])

    def test_shared_db_and_keychain_denied(self):
        self.assertFalse(S.check_action(self.p, "dev-api-smoke", "db.abc.supabase.co", "local")["allowed"])
        self.assertFalse(S.check_action(self.p, "read-file", "login.keychain", "local")["allowed"])

    def test_prod_env_denied(self):
        self.assertFalse(S.check_action(self.p, "run-test", "local", "production")["allowed"])


class AuthzTests(unittest.TestCase):
    def test_read_record_does_not_authorize_mutate(self):
        recs = [A.authorize("apply-migration", "dev-disposable", "mig:0049", "read", "founder")]
        self.assertFalse(A.is_authorized(recs, {"action": "apply-migration",
            "environment": "dev-disposable", "target": "mig:0049", "effect": "mutate"}))

    def test_exact_match_authorized(self):
        recs = [A.authorize("apply-migration", "dev-disposable", "mig:0049", "mutate", "founder")]
        self.assertTrue(A.is_authorized(recs, {"action": "apply-migration",
            "environment": "dev-disposable", "target": "mig:0049", "effect": "mutate"}))

    def test_stage_flag_cannot_authorize_mutation(self):
        with self.assertRaises(A.NotAuthorized):
            A.execute_guard([], {"action": "x", "environment": "dev", "target": "t", "effect": "mutate"},
                            stage_authorized=True)

    def test_target_mismatch_denied(self):
        recs = [A.authorize("send", "prod", "tenantA", "send", "founder")]
        self.assertFalse(A.is_authorized(recs, {"action": "send", "environment": "prod",
            "target": "tenantB", "effect": "send"}))

    def test_redact_scrubs_secrets(self):
        red = A.redact("API_KEY=ce_live_abcd1234 and Authorization: Bearer xyz.token.here")
        self.assertNotIn("ce_live_abcd1234", red)
        self.assertIn("[REDACTED]", red)


class RetryTests(unittest.TestCase):
    def test_two_corrections_stop(self):
        led = RT.empty_ledger()
        RT.record_attempt(led, "fail", "h1")
        RT.record_attempt(led, "fail", "h2")
        ok, reason = RT.can_retry(led)
        self.assertFalse(ok); self.assertIn("corrections", reason)

    def test_analysis_only_no_new_evidence_stops(self):
        led = RT.empty_ledger()
        RT.record_attempt(led, "fail", "same")
        RT.record_attempt(led, "fail", "same")  # also trips corrections; test single-correction case below
        led2 = RT.empty_ledger()
        RT.record_attempt(led2, "fail", "same")
        RT.record_attempt(led2, "pass", "same")  # 1 correction, but no new evidence
        ok, reason = RT.can_retry(led2)
        self.assertFalse(ok); self.assertIn("no new evidence", reason)

    def test_new_evidence_within_budget_allowed(self):
        led = RT.empty_ledger()
        RT.record_attempt(led, "fail", "h1")
        ok, _ = RT.can_retry(led)
        self.assertTrue(ok)

    def test_budget_exhausted_stops(self):
        led = RT.empty_ledger()
        for i in range(5):
            RT.record_attempt(led, "pass", f"h{i}")
        ok, reason = RT.can_retry(led, max_corrections=99, budget=5)
        self.assertFalse(ok); self.assertIn("budget", reason)


class ReconcileTests(unittest.TestCase):
    def _setup(self, tmp):
        root = Path(tmp)
        folder = root / "thread1" / "agent1-1"
        folder.mkdir(parents=True)
        (folder / "task.md").write_text("# current task SEQ-17\n")
        state = {"agent": "agent1-1", "thread": 1, "model": "claude", "dispatch_sequence": 1,
                 "task_digest": "OLDDIGEST", "status": "completed",
                 "updated_utc": "2026-10-20T00:00:00+00:00"}
        (folder / "state.json").write_text(json.dumps(state))
        # make task.md clearly newer than the seeded state
        import os
        future = time.time() + 10
        os.utime(folder / "task.md", (future, future))
        return root

    def test_proposal_only_never_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._setup(tmp)
            sf = root / "thread1" / "agent1-1" / "state.json"
            before = sf.read_text()
            cfg = {"threads": [{"thread": 1, "agents": [{"agent": "agent1-1"}]}]}
            out = RC.propose_reconciliation(cfg, root)
            self.assertFalse(out["writes_performed"])
            self.assertEqual(sf.read_text(), before, "reconcile must not touch state.json")
            a = out["agents"][0]
            self.assertTrue(a["stale"])
            self.assertFalse(a["ack"])
            self.assertEqual(a["proposal"], "reconcile-needed")
            self.assertIn("do-not-redispatch", a["guard"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
