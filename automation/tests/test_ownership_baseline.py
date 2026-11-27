#!/usr/bin/env python3
"""Tests for ownership.py (P0-4) and baseline.py (P0-5).
Run: python3 tests/test_ownership_baseline.py"""
from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ownership as O     # noqa: E402
import baseline as B      # noqa: E402


class OwnershipTests(unittest.TestCase):

    def test_disjoint_paths_both_granted(self):
        reg = O.empty_registry()
        O.acquire_paths(reg, "a1-1", 1, ["services/feedback/**"])
        O.acquire_paths(reg, "a2-2", 1, ["services/dns/**"])  # disjoint -> ok
        self.assertEqual(len(reg["paths"]), 2)

    def test_overlapping_paths_serialize(self):
        reg = O.empty_registry()
        O.acquire_paths(reg, "a1-1", 1, ["services/cal/send"])
        with self.assertRaises(O.OwnershipConflict):
            O.acquire_paths(reg, "a1-2", 1, ["services/cal/send/resolver.ts"])  # child overlap

    def test_same_owner_idempotent(self):
        reg = O.empty_registry()
        O.acquire_paths(reg, "a1-1", 1, ["services/x"])
        O.acquire_paths(reg, "a1-1", 1, ["services/x"])  # no conflict with self

    def test_migration_reservation_unique(self):
        reg = O.empty_registry()
        O.reserve_migration(reg, "a1-1", 48)
        with self.assertRaises(O.OwnershipConflict):
            O.reserve_migration(reg, "a1-2", 48)
        self.assertEqual(O.next_migration(reg, 48), 49)

    def test_namespace_exclusive(self):
        reg = O.empty_registry()
        O.acquire_namespace(reg, "a1-1", "docker:comms-dev")
        with self.assertRaises(O.OwnershipConflict):
            O.acquire_namespace(reg, "a1-2", "docker:comms-dev")

    def test_release_frees_everything(self):
        reg = O.empty_registry()
        O.acquire_paths(reg, "a1-1", 1, ["services/x"]); O.reserve_migration(reg, "a1-1", 50)
        O.release_owner(reg, "a1-1")
        self.assertEqual(reg["paths"], {})
        self.assertEqual(reg["migrations"], {})

    def test_persisted_registry_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "var" / "ownership.json"
            with O.with_registry(p) as reg:
                O.acquire_paths(reg, "a1-1", 1, ["services/x"])
            with O.with_registry(p) as reg:
                with self.assertRaises(O.OwnershipConflict):
                    O.acquire_paths(reg, "a1-2", 1, ["services/x"])


class BaselineTests(unittest.TestCase):

    def _repo(self, tmp):
        root = Path(tmp) / "repo"
        (root / "src").mkdir(parents=True)
        (root / "src" / "dirty.ts").write_text("export const x = 1;  // uncommitted\n")
        (root / ".env").write_text("SECRET_KEY=shhh\n")
        return root

    def test_captures_dirty_skips_secret_preserves_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            dest = Path(tmp) / "baseline"
            man = B.capture_baseline(root, ["src/dirty.ts", ".env"], dest, repo_id="comms-service")
            self.assertEqual([f["path"] for f in man["files"]], ["src/dirty.ts"])
            self.assertIn(".env", man["skipped_secrets"])
            # secret never copied
            self.assertFalse((dest / ".env").exists())
            # dirty file captured with provenance
            self.assertTrue((dest / "src" / "dirty.ts").exists())
            self.assertEqual(man["repo_id"], "comms-service")
            # source preserved (copy, not move)
            self.assertTrue((root / "src" / "dirty.ts").exists())
            self.assertTrue((root / ".env").exists())

    def test_verify_detects_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            dest = Path(tmp) / "baseline"
            man = B.capture_baseline(root, ["src/dirty.ts"], dest)
            ok, problems = B.verify_baseline(dest, man)
            self.assertTrue(ok, problems)
            (dest / "src" / "dirty.ts").write_text("TAMPERED\n")
            ok2, problems2 = B.verify_baseline(dest, man)
            self.assertFalse(ok2)
            self.assertTrue(any("hash mismatch" in p for p in problems2))

    def test_missing_required_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            man = B.capture_baseline(root, ["src/does-not-exist.ts"], Path(tmp) / "b")
            self.assertIn("src/does-not-exist.ts", man["missing"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
