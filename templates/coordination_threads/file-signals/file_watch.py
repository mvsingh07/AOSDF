#!/usr/bin/env python3
"""Local file-change notifications. Never executes or launches an agent or command."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import time


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def atomic(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    os.chmod(temp, 0o600)
    temp.replace(path)


def validate(root, names):
    paths = []
    for name in names:
        raw = root / name
        resolved = raw.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("watch path escapes workspace")
        parts = resolved.relative_to(root).parts
        if any(re.search(r"(^\.env|secret|credential|pgpass|token|\.pem$|\.key$|tfstate|tfvars)", p, re.I) for p in parts):
            raise ValueError("credential-bearing watch path refused")
        if raw.is_symlink() or any(parent.is_symlink() for parent in raw.parents if parent != root and parent.is_relative_to(root)):
            raise ValueError("symlink watch path refused")
        paths.append(resolved)
    return paths


def snapshot(root, paths):
    result = {}
    for path in paths:
        # Revalidate on each tick, including symlink replacement after startup.
        validate(root, [str(path.relative_to(root))])
        name = str(path.relative_to(root))
        if not path.exists():
            result[name] = None
        elif not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("watch source is not a bounded regular control file")
        else:
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--path", action="append", required=True)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--mode", choices=["wait", "watch", "receive"], default="wait")
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=50)
    parser.add_argument("--until", help="UTC deadline, ISO8601")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.actor):
        raise ValueError("invalid actor identity")
    if not args.until:
        raise ValueError("explicit UTC deadline required")
    root = args.root.resolve()
    if not root.is_dir() or args.interval < 0.05 or args.timeout <= 0:
        raise ValueError("invalid root, interval or timeout")
    paths = validate(root, args.path)
    state = args.state_dir.resolve()
    if not state.is_relative_to(root) or any(state == p or state in p.parents for p in paths):
        raise ValueError("state must be local and outside watched sources")
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    suffix = ".receive" if args.mode == "receive" else ""
    lock = (state / (args.actor + suffix + ".lock")).open("a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(json.dumps({"event": "already-running", "actor": args.actor}), flush=True)
        return 3
    stop = False

    def request_stop(*_):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    cursor_file = state / (args.actor + ".cursor.json")
    heartbeat = state / (args.actor + suffix + ".status.json")
    delivered_file = state / (args.actor + ".delivered.json")
    try:
        previous = json.loads(cursor_file.read_text())["snapshot"]
    except (OSError, ValueError, KeyError):
        previous = snapshot(root, paths)
        atomic(cursor_file, {"snapshot": previous, "at": utc()})
    expires = time.monotonic() + args.timeout
    until = dt.datetime.fromisoformat(args.until.replace("Z", "+00:00")) if args.until else None
    if until is not None and until.tzinfo is None:
        raise ValueError("deadline must include a timezone")
    outcome = "waiting"
    try:
        while not stop:
            if until and dt.datetime.now(dt.timezone.utc) >= until:
                outcome = "deadline"
                break
            if args.mode == "receive":
                try:
                    event = json.loads((state / (args.actor + ".event.json")).read_text())
                    delivered = json.loads(delivered_file.read_text()) if delivered_file.exists() else {}
                except (OSError, ValueError):
                    event, delivered = {}, {}
                if event and event.get("actor") == args.actor and event != delivered:
                    message = dict(event)
                    before, after = delivered.get("snapshot", {}), event.get("snapshot", {})
                    message["paths"] = sorted(p for p in set(before) | set(after)
                                              if before.get(p) != after.get(p))
                    atomic(delivered_file, event)
                    print(json.dumps(message), flush=True)
                    outcome = "delivered"
                    return 0
                atomic(heartbeat, {"actor": args.actor, "pid": os.getpid(), "at": utc(),
                                   "state": "waiting-for-notification", "authority": "notification-only"})
                remaining = expires - time.monotonic()
                if remaining <= 0:
                    outcome = "timeout"
                    break
                time.sleep(min(args.interval, remaining))
                continue
            current = snapshot(root, paths)
            changed = sorted(p for p in set(previous) | set(current) if previous.get(p) != current.get(p))
            if changed:
                event = {"event": "changed", "actor": args.actor, "at": utc(), "paths": changed,
                         "snapshot": current, "pid": os.getpid(), "authority": "notification-only"}
                atomic(state / (args.actor + ".event.json"), event)
                # A changed event is observed, not accepted or approved by any actor.
                atomic(cursor_file, {"snapshot": current, "at": event["at"]})
                print(json.dumps(event), flush=True)
                previous = current
                if args.mode == "wait":
                    outcome = "changed"
                    return 0
            atomic(heartbeat, {"actor": args.actor, "pid": os.getpid(), "at": utc(),
                               "state": "watching", "mode": args.mode, "authority": "notification-only",
                               "source_count": len(paths), "until": args.until})
            remaining = expires - time.monotonic()
            if remaining <= 0:
                outcome = "timeout"
                break
            time.sleep(min(args.interval, remaining))
        if stop:
            outcome = "stopped"
        print(json.dumps({"event": outcome, "actor": args.actor, "at": utc()}), flush=True)
        return 0 if stop else 2
    finally:
        atomic(heartbeat, {"actor": args.actor, "pid": os.getpid(), "at": utc(),
                           "state": outcome, "authority": "notification-only"})


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        # Exception text is bounded metadata, never source-file content.
        print(json.dumps({"event": "refused", "reason": str(error)[:160]}), file=sys.stderr)
        raise SystemExit(1)
