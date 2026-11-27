#!/usr/bin/env python3
"""Baseline capture of required uncommitted dependencies across repos (P0-5).

A fresh automated worktree would omit the required UNCOMMITTED files the current multi-repo
tree depends on. This captures them into an isolated destination by COPY (never move, never
`git reset`/`stash`), so the source tree's dirty files are preserved, and records a provenance
manifest (repo id + per-file sha256 + size + source relpath). Secret-bearing paths are NEVER
copied — they are recorded by name only, so no secret is captured into the baseline.

No git invocation is required for the testable core; a `repo_id` is supplied (or defaults to
the source folder name). Full `git diff` provenance is a later refinement; the manifest's
per-file hashes already tie each captured file to its source bytes.
"""
from __future__ import annotations
import fnmatch, hashlib, json, shutil, datetime
from pathlib import Path

DEFAULT_SECRET_DENYLIST = [
    ".env", ".env.*", "*.pem", "*.key", "*secret*", "*credential*", "*.p12", "*.pfx",
    "id_rsa", "id_rsa.*", ".npmrc", ".netrc",
]


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_secret(relpath: str, denylist: list[str]) -> bool:
    name = Path(relpath).name
    return any(fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(relpath, pat) for pat in denylist)


def capture_baseline(repo_root, required_dirty: list[str], dest, repo_id: str | None = None,
                     secret_denylist: list[str] | None = None) -> dict:
    """Copy each required dirty file into `dest`, skipping secrets. Returns a provenance
    manifest. The source tree is only read, never modified."""
    repo_root = Path(repo_root)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    denylist = secret_denylist or DEFAULT_SECRET_DENYLIST
    rid = repo_id or repo_root.name
    manifest = {"repo_id": rid, "repo_root": str(repo_root), "captured_utc": _utc(),
                "files": [], "skipped_secrets": [], "missing": []}

    for rel in required_dirty:
        src = repo_root / rel
        if _is_secret(rel, denylist):
            manifest["skipped_secrets"].append(rel)       # name only — no contents captured
            continue
        if not src.is_file():
            manifest["missing"].append(rel)
            continue
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(out))                   # copy, never move
        manifest["files"].append({"path": rel, "sha256": _sha256(src), "size": src.stat().st_size})

    (dest / "baseline-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_baseline(dest, manifest: dict) -> tuple[bool, list[str]]:
    """Re-hash the copied files and confirm they match the manifest (no loss/corruption)."""
    dest = Path(dest)
    problems = []
    for f in manifest.get("files", []):
        out = dest / f["path"]
        if not out.is_file():
            problems.append(f"missing in baseline: {f['path']}")
        elif _sha256(out) != f["sha256"]:
            problems.append(f"hash mismatch: {f['path']}")
    return (not problems), problems
