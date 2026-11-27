#!/usr/bin/env python3
"""Durable file notifications/read receipts for the existing coordination flow.

No scheduler, actor launcher or authorization decisions. A queued file is not a
read receipt, and a read receipt is not a channel verdict or task acceptance.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import uuid

HERE = Path(__file__).resolve().parent
MAILBOX_ROOT = HERE / "var/delivery"
from layout import THREADS as ARTIFACT_ROOT
DISPATCH_LOCK = HERE / "var/.coordinator-launch.lock"
_mutex = threading.RLock()
_local = threading.local()
_ID = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")
FIELDS = {"schema_version", "id", "wave_id", "scope_sha256", "thread", "recipient",
          "round", "status", "source", "source_sha256"}

# Peer mail is communication only. It deliberately has no wave/dispatch authority.
PEER_FIELDS = {'schema_version', 'id', 'kind', 'from_thread', 'to_thread',
               'sender_binding', 'sender_session', 'receiver_binding', 'receiver_session',
               'sender_sprint', 'source', 'source_sha256', 'snapshot', 'reply_to'}
MAX_PEER_BYTES = 256 * 1024


def peer_owner(thread, *, authenticate=False):
    import owner_sessions as owners
    if type(thread) is not int or thread not in (1, 2, 3):
        raise ValueError('invalid peer thread')
    record = owners.binding('coordinator', thread)
    if not record or record.get('state') != 'bound':
        raise ValueError(f'Thread{thread} owner is not bound; reconcile existing owner, never replace it')
    if authenticate:
        owners.authenticate(record)
    return record


def peer_folder(thread):
    return safe_path(MAILBOX_ROOT, MAILBOX_ROOT / 'peer' / f'thread{thread}')


def peer_validate(event, *, verify_owners=True):
    if set(event) != PEER_FIELDS or event.get('schema_version') != 2:
        raise ValueError('invalid peer schema/fields')
    if event['kind'] not in ('question', 'answer', 'notice'):
        raise ValueError('invalid peer kind')
    for key in ('id', 'source_sha256'):
        if not isinstance(event[key], str) or not _ID.fullmatch(event[key]):
            raise ValueError('invalid peer digest')
    for key in ('sender_binding', 'sender_session', 'receiver_binding', 'receiver_session'):
        if not isinstance(event[key], str):
            raise ValueError('invalid peer owner identity')
        uuid.UUID(event[key])
    if event['from_thread'] == event['to_thread']:
        raise ValueError('peer sender and recipient must differ')
    for prefix, thread in (('sender', event['from_thread']), ('receiver', event['to_thread'])):
        if type(thread) is not int or thread not in (1, 2, 3):
            raise ValueError('invalid peer thread')
        if verify_owners:
            owner = peer_owner(thread)
            if owner['binding_id'] != event[prefix + '_binding'] or owner['session_id'] != event[prefix + '_session']:
                raise ValueError('peer owner changed; explicitly reconcile, do not retarget history')
    if not isinstance(event['sender_sprint'], str) or not event['sender_sprint']:
        raise ValueError('peer sprint provenance missing')
    relative = Path(event['source'])
    if relative.is_absolute() or '..' in relative.parts or relative.suffix != '.md':
        raise ValueError('invalid peer source')
    parts = relative.parts
    if not (parts and parts[0] == f"thread{event['from_thread']}" and
            (len(parts) == 2 or (len(parts) == 3 and parts[1] in PEER_SOURCE_DIRS))):
        raise ValueError('peer source must be sender-owned handoff or guide')
    expected_snapshot = f"peer/objects/{event['source_sha256']}.json"
    if event['snapshot'] != expected_snapshot:
        raise ValueError('invalid peer snapshot path')
    obj = json.loads(safe_path(MAILBOX_ROOT, MAILBOX_ROOT / expected_snapshot).read_text())
    if set(obj) != {'body', 'sha256'} or not isinstance(obj['body'], str):
        raise ValueError('invalid peer snapshot')
    body = obj['body'].encode('utf-8')
    if len(body) > MAX_PEER_BYTES or hashlib.sha256(body).hexdigest() != event['source_sha256'] or obj['sha256'] != event['source_sha256']:
        raise ValueError('peer snapshot digest/size mismatch')
    if (event['kind'] == 'answer') != (isinstance(event['reply_to'], str) and bool(_ID.fullmatch(event['reply_to']))):
        raise ValueError('answer requires exact question id; other kinds must have no reply')
    if event['kind'] != 'answer' and event['reply_to'] is not None:
        raise ValueError('unexpected peer reply link')
    if hashlib.sha256(canonical({k: v for k, v in event.items() if k != 'id'}).encode()).hexdigest() != event['id']:
        raise ValueError('peer identity/content mismatch')
    return event


def peer_load(path, record, *, verify_owners=True):
    path = safe_path(MAILBOX_ROOT, Path(path).absolute())
    event = peer_validate(json.loads(path.read_text()), verify_owners=verify_owners)
    if path != peer_folder(record['thread']) / (event['id'] + '.json') or event['to_thread'] != record['thread']:
        raise ValueError('peer notification outside recipient mailbox')
    if verify_owners and (event['receiver_binding'] != record['binding_id'] or event['receiver_session'] != record['session_id']):
        raise ValueError('peer recipient identity mismatch')
    return event


def peer_read_receipt(event):
    return {k: event[k] for k in ('schema_version', 'id', 'to_thread', 'receiver_binding', 'receiver_session', 'source_sha256')} | {'state': 'read'}


def peer_pending(record):
    result = []
    for path in sorted(peer_folder(record['thread']).glob('*.json')):
        if path.name.endswith('.read.json'):
            continue
        ack = path.with_suffix('.read.json')
        event = peer_load(path, record, verify_owners=not ack.exists())
        if ack.exists():
            safe_path(MAILBOX_ROOT, ack)
            if json.loads(ack.read_text()) != peer_read_receipt(event):
                raise ValueError('invalid peer read receipt')
        else:
            result.append({'path': str(path), **event})
    return result


def peer_ack(path, thread):
    record = peer_owner(thread, authenticate=True)
    with dispatch_guard():
        event = peer_load(path, record)
        return write_once(Path(path).absolute().with_suffix('.read.json'), peer_read_receipt(event))


def peer_send(sender, receiver, kind, source, reply_to=None):
    # Recheck both bindings under the same guard used for owner registration.
    with dispatch_guard():
        if kind not in ('question', 'answer', 'notice') or (kind != 'answer' and reply_to is not None):
            raise ValueError('invalid peer kind/reply link')
        author = peer_owner(sender, authenticate=True)
        target = peer_owner(receiver)
        source = safe_path(ARTIFACT_ROOT, Path(source).absolute())
        relative = source.relative_to(ARTIFACT_ROOT)
        if not (relative.parts and relative.parts[0] == f'thread{sender}' and source.suffix == '.md' and
                (len(relative.parts) == 2 or (len(relative.parts) == 3 and relative.parts[1] in PEER_SOURCE_DIRS))):
            raise ValueError('peer source must be sender-owned handoff or guide')
        if source.stat().st_size > MAX_PEER_BYTES:
            raise ValueError('peer source exceeds size bound')
        body = source.read_bytes()
        if len(body) > MAX_PEER_BYTES:
            raise ValueError('peer source exceeds size bound')
        decoded = body.decode('utf-8')
        digest = hashlib.sha256(body).hexdigest()
        if kind == 'answer':
            if not isinstance(reply_to, str) or not _ID.fullmatch(reply_to):
                raise ValueError('answer requires exact question id')
            question_path = peer_folder(sender) / (reply_to + '.json')
            question = peer_load(question_path, author)
            if question['kind'] != 'question' or question['from_thread'] != receiver:
                raise ValueError('reply must answer a question from the target')
            ack = safe_path(MAILBOX_ROOT, question_path.with_suffix('.read.json'))
            if not ack.exists() or json.loads(ack.read_text()) != peer_read_receipt(question):
                raise ValueError('read and ACK question before answering')
        sprint = json.loads(safe_path(ARTIFACT_ROOT, ARTIFACT_ROOT / f'thread{sender}/sprint.json').read_text())
        snapshot = f'peer/objects/{digest}.json'
        write_once(MAILBOX_ROOT / snapshot, {'body': decoded, 'sha256': digest})
        event = dict(schema_version=2, kind=kind, from_thread=sender, to_thread=receiver,
                     sender_binding=author['binding_id'], sender_session=author['session_id'],
                     receiver_binding=target['binding_id'], receiver_session=target['session_id'],
                     sender_sprint=sprint.get('sprint_id'), source=str(relative), source_sha256=digest,
                     snapshot=snapshot, reply_to=reply_to)
        event['id'] = hashlib.sha256(canonical(event).encode()).hexdigest()
        peer_validate(event)
        return write_once(peer_folder(receiver) / (event['id'] + '.json'), event)


def peer_cli(argv):
    parser = argparse.ArgumentParser(description='Same-owner peer communication; grants no task/runtime authority.')
    commands = parser.add_subparsers(dest='command', required=True)
    send = commands.add_parser('send-peer')
    send.add_argument('--from-thread', type=int, required=True)
    send.add_argument('--to-thread', type=int, required=True)
    send.add_argument('--kind', choices=('question', 'answer', 'notice'), required=True)
    send.add_argument('--source', type=Path, required=True)
    send.add_argument('--reply-to')
    for name in ('peer-pending', 'peer-ack'):
        command = commands.add_parser(name)
        command.add_argument('--thread', type=int, required=True)
        if name == 'peer-ack':
            command.add_argument('--notification', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'send-peer':
        print(peer_send(args.from_thread, args.to_thread, args.kind, args.source, args.reply_to))
    elif args.command == 'peer-ack':
        print(peer_ack(args.notification, args.thread))
    else:
        print(json.dumps(peer_pending(peer_owner(args.thread, authenticate=True)), indent=2))
    return 0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def scope_sha(wave, sprint):
    return hashlib.sha256(canonical({"wave_id": wave["wave_id"], "sprint": {
        k: sprint.get(k) for k in ("id", "thread", "task_ids", "scope_review_ref", "model_policy",
                                  "target_tier", "founder_auth_ref", "opening_round")}}).encode()).hexdigest()


# Peer messages live in threadN/instructions/ (24Nov); root and guides/ stay valid for existing events.
PEER_SOURCE_DIRS = ('guides', 'instructions')


def safe_path(root, path):
    root, path = Path(root).absolute(), Path(path).absolute()
    if ".." in path.parts or ".." in root.parts or not path.is_relative_to(root):
        raise ValueError("delivery path escapes its declared root")
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError("symlink delivery/artifact path refused")
    return path


def write_once(path, value):
    path = safe_path(MAILBOX_ROOT, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Complete bytes are published atomically: a competing reader sees all or none.
    import tempfile
    fd, temporary = tempfile.mkstemp(prefix=".delivery-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(canonical(value) + "\n")
            handle.flush(); os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            safe_path(MAILBOX_ROOT, path)
            if json.loads(path.read_text()) != value:
                raise ValueError("existing immutable delivery/ack differs")
    finally:
        Path(temporary).unlink(missing_ok=True)
    return path


def emit(*, wave_id, scope, thread, recipient, number, status, source, expected_source_sha=None):
    source = safe_path(ARTIFACT_ROOT, source)
    event = {"schema_version": 1, "wave_id": wave_id, "scope_sha256": scope,
             "thread": thread, "recipient": recipient, "round": number, "status": status,
             "source": str(source.relative_to(ARTIFACT_ROOT)), "source_sha256": sha(source)}
    if expected_source_sha is not None and event['source_sha256'] != expected_source_sha:
        raise ValueError('channel changed during delivery selection')
    event["id"] = hashlib.sha256(canonical(event).encode()).hexdigest()
    validate_event(event)
    folder = MAILBOX_ROOT / recipient / f"thread{thread}"
    return write_once(folder / (event["id"] + ".json"), event)


def validate_event(event, *, verify_source=True):
    if set(event) != FIELDS or event["schema_version"] != 1:
        raise ValueError("unknown delivery schema/fields")
    if not isinstance(event["wave_id"], str) or not _NAME.fullmatch(event["wave_id"]):
        raise ValueError("invalid wave identity")
    if any(not isinstance(event[k], str) or not _ID.fullmatch(event[k]) for k in ("id", "scope_sha256", "source_sha256")):
        raise ValueError("invalid delivery digest")
    if type(event["thread"]) is not int or event["thread"] not in (1, 2, 3):
        raise ValueError("invalid recipient thread")
    if type(event["round"]) is not int or event["round"] < 1:
        raise ValueError("invalid round")
    allowed = {"architect": {"AWAITING-ARCHITECT"}, "coordinator": {"ALIGNED", "REDIRECT"}}
    if event["recipient"] not in allowed or event["status"] not in allowed[event["recipient"]]:
        raise ValueError("invalid recipient/event status")
    original = {k: v for k, v in event.items() if k != "id"}
    if hashlib.sha256(canonical(original).encode()).hexdigest() != event["id"]:
        raise ValueError("delivery identity/content mismatch")
    if not isinstance(event["source"], str) or Path(event["source"]).is_absolute() or ".." in Path(event["source"]).parts:
        raise ValueError("invalid artifact path")
    source = safe_path(ARTIFACT_ROOT, ARTIFACT_ROOT / event["source"])
    if verify_source and sha(source) != event["source_sha256"]:
        raise ValueError("stale delivery source; reconcile current channel")
    return event


def load(path, *, recipient, thread, wave_id, scope):
    path = safe_path(MAILBOX_ROOT, path)
    event = validate_event(json.loads(path.read_text()))
    if path.name != event["id"] + ".json" or any(event[k] != v for k, v in
            (("recipient", recipient), ("thread", thread), ("wave_id", wave_id), ("scope_sha256", scope))):
        raise ValueError("notification recipient/scope/path mismatch")
    expected = MAILBOX_ROOT / recipient / f"thread{thread}" / path.name
    if path != expected.absolute():
        raise ValueError("notification outside recipient mailbox")
    return event


def acknowledge(path, **identity):
    event = load(path, **identity)
    ack = {"schema_version": 1, "id": event["id"], "recipient": event["recipient"],
           "thread": event["thread"], "wave_id": event["wave_id"], "scope_sha256": event["scope_sha256"],
           "source_sha256": event["source_sha256"], "state": "read"}
    return write_once(Path(path).with_suffix(".read.json"), ack)


def pending(*, recipient, thread, wave_id, scope):
    result = []
    folder = safe_path(MAILBOX_ROOT, MAILBOX_ROOT / recipient / f"thread{thread}")
    for path in sorted(folder.glob("*.json")):
        if path.name.endswith(".read.json"):
            continue
        raw = json.loads(path.read_text())
        if raw.get("wave_id") != wave_id or raw.get("scope_sha256") != scope:
            continue
        ack_path = path.with_suffix(".read.json")
        if ack_path.exists():
            event = validate_event(raw, verify_source=False)
            if event['recipient'] != recipient or event['thread'] != thread or path.name != event['id'] + '.json':
                raise ValueError("notification recipient/path mismatch")
            expected = {"schema_version": 1, "id": event["id"], "recipient": recipient, "thread": thread,
                        "wave_id": wave_id, "scope_sha256": scope,
                        "source_sha256": event["source_sha256"], "state": "read"}
            safe_path(MAILBOX_ROOT, ack_path)
            if json.loads(ack_path.read_text()) != expected:
                raise ValueError("invalid read acknowledgement")
        else:
            event = load(path, recipient=recipient, thread=thread, wave_id=wave_id, scope=scope)
            result.append({"path": str(path), **event})
    return result


@contextmanager
def dispatch_guard():
    """Shared, process-and-thread single-flight; nested existing entry paths are safe."""
    if not _mutex.acquire(blocking=False):
        raise BlockingIOError("another role dispatch is running")
    try:
        depth = getattr(_local, "depth", 0)
        if depth:
            _local.depth += 1
            try:
                yield
            finally:
                _local.depth -= 1
        else:
            DISPATCH_LOCK.parent.mkdir(parents=True, exist_ok=True)
            with DISPATCH_LOCK.open("a+") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                _local.depth = 1
                try:
                    yield
                finally:
                    _local.depth = 0
                    fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        _mutex.release()


def run_live(folder):
    marker = folder / "coordinator.pid"
    if marker.exists():
        try:
            pid = int(marker.read_text().strip())
            if pid <= 1: return True
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except (PermissionError, ValueError):
            return True
    launch = json.loads((folder / "launch.json").read_text())
    if launch.get("dry_run") and not (folder / ".launcher-once").exists():
        return False
    if not launch.get("window_id"):
        return (folder / ".launcher-once").exists()
    proc = subprocess.run(["ps", "-axo", "command="], capture_output=True, text=True, check=True, timeout=5)
    if str(folder / "terminal.log") in proc.stdout:
        return True
    try:
        created = dt.datetime.fromisoformat(launch["created_utc"].replace("Z", "+00:00"))
        return (dt.datetime.now(dt.timezone.utc) - created).total_seconds() < 120
    except (KeyError, ValueError, TypeError):
        return True


def active_architect():
    import owner_sessions
    external = owner_sessions.blocking_owner('architect')
    if external:
        return external
    for launch in (HERE / "var/architect-runs").rglob("launch.json"):
        if run_live(launch.parent):
            return str(launch.parent)
    return None


def round_was_read(*, wave_id, scope, thread, recipient, number, status, source):
    """A receiver's verified ACK closes this routing round, not just one hash."""
    folder = safe_path(MAILBOX_ROOT, MAILBOX_ROOT / recipient / f'thread{thread}')
    relative = str(safe_path(ARTIFACT_ROOT, source).relative_to(ARTIFACT_ROOT))
    for path in sorted(folder.glob('*.json')):
        if path.name.endswith('.read.json'):
            continue
        raw = json.loads(path.read_text())
        identity = dict(wave_id=wave_id, scope_sha256=scope, thread=thread, recipient=recipient,
                        round=number, status=status, source=relative)
        if any(raw.get(k) != v for k, v in identity.items()):
            continue
        ack = path.with_suffix('.read.json')
        if not ack.exists():
            continue
        safe_path(MAILBOX_ROOT, path); safe_path(MAILBOX_ROOT, ack)
        event = validate_event(raw, verify_source=False)
        if path.name != event['id'] + '.json':
            raise ValueError('notification recipient/path mismatch')
        expected = dict(schema_version=1, id=event['id'], recipient=recipient, thread=thread,
                        wave_id=wave_id, scope_sha256=scope, source_sha256=event['source_sha256'], state='read')
        if json.loads(ack.read_text()) != expected:
            raise ValueError('invalid read acknowledgement')
        return True
    return False


def delivery_only_tick(recipient):
    """Queue existing scoped rounds. No actor launch, ACK, verdict or cursor mutation."""
    import architect_bridge as bridge
    import wave
    if recipient not in ('architect', 'coordinator'):
        raise ValueError('invalid delivery recipient')
    current = wave.active_wave()
    if not current or current.get('delivery_only') is not True:
        return {'state': 'inactive', 'events': [], 'reason': 'no authorized delivery-only envelope'}
    for relative, expected in current.get('source_sha256', {}).items():
        source = Path(os.path.abspath(ARTIFACT_ROOT / relative))
        safe_path(ARTIFACT_ROOT.parent, source)
        if sha(source) != expected:
            raise ValueError('delivery envelope source changed; explicit reconciliation required')
    events = []
    # These writers only publish disjoint immutable notifications, never actors or
    # shared cursors. Atomic write_once is sufficient; do not starve one watcher
    # by taking the actor-dispatch lock on every simultaneous queue-only tick.
    for row in bridge.scan():
        latest = row['latest']
        scoped = bridge.scoped_round(row['thread'], current, latest)
        allowed = {'AWAITING-ARCHITECT'} if recipient == 'architect' else {'ALIGNED', 'REDIRECT'}
        if not scoped or latest.get('status') not in allowed:
            continue
        source = Path(bridge.CHANNEL_DIR) / row['file']
        selected_sha = sha(source)
        if round_was_read(wave_id=current['wave_id'], scope=scope_sha(current, scoped),
                          thread=row['thread'], recipient=recipient, number=latest['round'],
                          status=latest['status'], source=source):
            continue
        if bridge._latest_round(str(source)) != latest:
            continue
        path = emit(wave_id=current['wave_id'], scope=scope_sha(current, scoped), thread=row['thread'],
                    recipient=recipient, number=latest['round'], status=latest['status'],
                    source=source, expected_source_sha=selected_sha)
        events.append(str(path))
    return {'state': 'delivery-only', 'events': events, 'actors_launched': 0, 'read_acknowledged': False}


def watch_delivery(recipient, interval):
    import daemon
    name = 'architect_bridge' if recipient == 'architect' else 'coordinator_trigger'
    while True:
        try:
            result = delivery_only_tick(recipient)
            summary = f"{result['state']}: {len(result['events'])} event(s) queued; read not inferred"
        except (OSError, ValueError, KeyError, TypeError, BlockingIOError) as error:
            summary = 'delivery blocked: ' + str(error)
        daemon.write_status(name, state='running', path_mode='delivery-only', live=False, summary=summary)
        print(summary, flush=True)
        time.sleep(max(5, interval))


def foreign_controller_conflict():
    var = HERE / "var"
    lock = var / ".bounded-job.lock"
    if lock.exists():
        with lock.open("a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle, fcntl.LOCK_UN)
    for base in (var / "bounded-jobs", var / "sprint-loop"):
        for launch in base.rglob("launch.json"):
            if run_live(launch.parent):
                raise ValueError("another controller's actor is active/uncertain")
    for marker in (var / "sprint-loop").glob("*/controller.pid"):
        try:
            pid = int(marker.read_text())
            if pid <= 1: raise ValueError("uncertain controller PID")
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        raise ValueError("another controller active/uncertain")


def polling_text(role, thread, wave_id, scope):
    command = f"python3 {HERE / 'channel_delivery.py'}"
    identity = f"--recipient {role} --thread {thread} --wave {wave_id} --scope {scope}"
    return (f" Cooperative file delivery: use `{command} pending {identity}` at safe checkpoints; "
            f"at a genuine communication wait use `{command} wait {identity} --timeout 30` and recheck "
            "your current channel/authority. After reading an exact valid notification, explicitly run "
            f"`{command} ack {identity} --notification <its-path>` BEFORE modifying the source channel. "
            "A read acknowledgement proves reading only; ordinary verdict/GREEN and accepted results prove action. "
            "Do not acknowledge unseen/stale files. A watcher cannot inject into this chat; pending without "
            "an owner read ack is not delivered conversation input. Continue this same coordinator/session; "
            "do not spawn replacement coordinators or architect sessions while waiting.")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ('send-peer', 'peer-pending', 'peer-ack'):
        try:
            return peer_cli(argv)
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            print('Peer communication needs reconciliation: ' + str(exc)); return 2
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("pending", "wait", "ack"))
    p.add_argument("--recipient", choices=("architect", "coordinator"), required=True)
    p.add_argument("--thread", type=int, choices=(1, 2, 3), required=True)
    p.add_argument("--wave", required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--notification", type=Path)
    p.add_argument("--timeout", type=float, default=30)
    args = p.parse_args(argv)
    identity = dict(recipient=args.recipient, thread=args.thread, wave_id=args.wave, scope=args.scope)
    try:
        if not _NAME.fullmatch(args.wave) or not _ID.fullmatch(args.scope):
            raise ValueError("invalid wave/scope identity")
        if args.command == "ack":
            if not args.notification: raise ValueError("exact --notification path required")
            print(acknowledge(args.notification, **identity)); return 0
        if not 0 <= args.timeout <= 30: raise ValueError("wait timeout must be 0..30 seconds")
        deadline = time.monotonic() + args.timeout
        while True:
            events = pending(**identity)
            if events or args.command == "pending":
                print(json.dumps(events, indent=2)); return 0
            if time.monotonic() >= deadline: return 124
            time.sleep(min(.2, max(0, deadline - time.monotonic())))
    except (OSError, ValueError) as exc:
        print(str(exc)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
