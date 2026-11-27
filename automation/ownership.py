#!/usr/bin/env python3
"""Filesystem/schema ownership leases + migration reservation + resource namespace (P0-4).

Arbitrates exclusive write ownership so concurrent agents cannot collide. Pure functions
operate on a registry dict (easy to test); `with_registry(path)` persists it under a meta-
lock. This module never edits the owned files/migrations itself — it only grants/denies the
right to, so unrelated dirty changes are left untouched (capturing/isolating them is
baseline.py's job).

Rules:
  - A path lease is exclusive: a second owner requesting an overlapping path is REFUSED
    (the two coordinators must serialize via a handoff), but disjoint paths both succeed.
  - A migration number is reserved by exactly one owner; `next_migration` hands out the
    smallest free number so two workers cannot pick the same one.
  - A local resource namespace (docker project / DB schema / build dir) is owned by one
    agent at a time.
"""
from __future__ import annotations
import json, os, time, datetime
from pathlib import Path

LOCK = ".ownership.lock"


class OwnershipConflict(RuntimeError):
    pass


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def empty_registry() -> dict:
    return {"paths": {}, "migrations": {}, "namespaces": {}}


def _norm(p: str) -> str:
    return p.split("**")[0].split("*")[0].strip().rstrip("/")


def _path_overlap(a: str, b: str) -> bool:
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return False
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def acquire_paths(reg: dict, owner: str, fence: int, paths: list[str]) -> dict:
    """Grant exclusive leases on `paths` to (owner, fence). Refuse if any overlaps a lease
    held by a different owner. Idempotent for the same owner."""
    held = reg.setdefault("paths", {})
    for req in paths:
        for existing, info in held.items():
            if info["owner"] != owner and _path_overlap(req, existing):
                raise OwnershipConflict(
                    f"{owner} requested {req!r} overlapping {existing!r} held by {info['owner']}")
    for req in paths:
        held[req] = {"owner": owner, "fence": fence, "acquired_utc": _utc()}
    return reg


def reserve_migration(reg: dict, owner: str, number: int) -> dict:
    migs = reg.setdefault("migrations", {})
    cur = migs.get(str(number))
    if cur is not None and cur["owner"] != owner:
        raise OwnershipConflict(f"migration {number} already reserved by {cur['owner']}")
    migs[str(number)] = {"owner": owner, "reserved_utc": _utc()}
    return reg


def next_migration(reg: dict, start: int) -> int:
    """Smallest free migration number >= start (does not reserve it)."""
    migs = reg.get("migrations", {})
    n = start
    while str(n) in migs:
        n += 1
    return n


def acquire_namespace(reg: dict, owner: str, name: str) -> dict:
    ns = reg.setdefault("namespaces", {})
    cur = ns.get(name)
    if cur is not None and cur["owner"] != owner:
        raise OwnershipConflict(f"namespace {name!r} owned by {cur['owner']}")
    ns[name] = {"owner": owner, "acquired_utc": _utc()}
    return reg


def release_owner(reg: dict, owner: str) -> dict:
    reg["paths"] = {k: v for k, v in reg.get("paths", {}).items() if v["owner"] != owner}
    reg["migrations"] = {k: v for k, v in reg.get("migrations", {}).items() if v["owner"] != owner}
    reg["namespaces"] = {k: v for k, v in reg.get("namespaces", {}).items() if v["owner"] != owner}
    return reg


# --- persistence under a meta-lock --------------------------------------------------------

class with_registry:
    """Context manager: load the registry at `path` under a lock, yield it for mutation, save
    on clean exit. Usage: `with with_registry(p) as reg: ownership.acquire_paths(reg, ...)`."""

    def __init__(self, path, timeout: float = 5.0):
        self.path = Path(path)
        self.timeout = timeout
        self._lock = self.path.parent / LOCK

    def __enter__(self) -> dict:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + self.timeout
        while True:
            try:
                fd = os.open(str(self._lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd); break
            except FileExistsError:
                if time.time() > deadline:
                    raise OwnershipConflict("ownership registry lock busy")
                time.sleep(0.01)
        try:
            self.reg = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.reg = empty_registry()
        return self.reg

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                tmp = self.path.with_suffix(self.path.suffix + ".tmp")
                tmp.write_text(json.dumps(self.reg, indent=2) + "\n", encoding="utf-8")
                os.replace(str(tmp), str(self.path))
        finally:
            try:
                self._lock.unlink()
            except OSError:
                pass
        return False
