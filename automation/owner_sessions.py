#!/usr/bin/env python3
"""Explicit bindings for existing owners. Never launch, resume or replace an agent."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

import channel_delivery as delivery

HERE = Path(__file__).resolve().parent
from layout import PROJECT_ROOT as REPO
OWNERS = HERE / 'var/owners'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read(path):
    delivery.safe_path(OWNERS, path)
    return json.loads(path.read_text())


def write(path, value):
    delivery.safe_path(OWNERS, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    delivery.safe_path(OWNERS, temporary)
    with temporary.open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write('\n')
    os.replace(temporary, path)


def owner_path(role, thread=0):
    if role not in ('architect', 'coordinator') or (role == 'architect' and thread != 0) or (role == 'coordinator' and thread not in (1, 2, 3)):
        raise ValueError('invalid owner role/thread')
    return OWNERS / (role + (str(thread) if thread else '') + '.json')


def fingerprint(pid):
    if not isinstance(pid, int) or pid <= 1:
        raise ValueError('invalid owner PID')
    proc = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'comm='],
                          capture_output=True, text=True, check=True, timeout=5)
    value = proc.stdout.strip()
    if not value:
        raise ValueError('owner process absent')
    return hashlib.sha256(value.encode()).hexdigest()


def ancestor(executor):
    pid = os.getppid()
    for _ in range(20):
        proc = subprocess.run(['ps', '-p', str(pid), '-o', 'ppid=', '-o', 'comm='],
                              capture_output=True, text=True, check=True, timeout=5)
        fields = proc.stdout.strip().split(None, 1)
        if len(fields) != 2:
            break
        if Path(fields[1]).name == executor:
            return pid
        pid = int(fields[0])
        if pid <= 1:
            break
    raise ValueError('register from inside the existing ' + executor + ' owner session')


def identity(executor, profile=None, session_id=None):
    pid = ancestor(executor)
    if executor == 'claude':
        profile = Path(profile or os.environ.get('CLAUDE_CONFIG_DIR', str(Path.home() / '.claude'))).absolute()
        delivery.safe_path(Path.home(), profile)
        if not profile.is_dir():
            raise ValueError('existing profile directory required')
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(profile))
        result = subprocess.run(['claude', 'agents', '--json'], env=env, text=True,
                                capture_output=True, check=True, timeout=15)
        sessions = json.loads(result.stdout)
        matches = [s for s in sessions if s.get('pid') == pid and Path(s.get('cwd', '')).resolve().is_relative_to(REPO)]
        if len(matches) != 1:
            raise ValueError('Claude session PID/profile/repository not uniquely verified')
        actual = matches[0]['sessionId']
        if session_id and session_id != actual:
            raise ValueError('session identity mismatch')
        session_id = actual
    elif executor == 'codex':
        actual = os.environ.get('CODEX_THREAD_ID')
        if not actual or (session_id and session_id != actual):
            raise ValueError('current Codex thread identity required')
        session_id, profile = actual, None
    else:
        raise ValueError('unsupported executor')
    uuid.UUID(session_id)
    return dict(executor=executor, session_id=session_id, profile=str(profile) if profile else None,
                pid=pid, process_fingerprint=fingerprint(pid), repository=str(REPO))


def validate(record, role, thread):
    if record.get('schema_version') != 1 or record.get('role') != role or record.get('thread') != thread or record.get('repository') != str(REPO):
        raise ValueError('invalid owner binding')
    if record.get('state') not in ('reserved', 'bound', 'released'):
        raise ValueError('invalid owner state')
    if record['state'] == 'bound':
        uuid.UUID(record['binding_id']); uuid.UUID(record['session_id'])
        if record.get('executor') not in ('claude', 'codex') or not record.get('process_fingerprint'):
            raise ValueError('invalid bound owner identity')
    return record


def binding(role, thread=0):
    path = owner_path(role, thread)
    if not path.exists() and not path.is_symlink():
        return None
    return validate(read(path), role, thread)


def blocking_owner(role, thread=0):
    """Reservations, dead and uncertain owners block; no implicit takeover."""
    path = owner_path(role, thread)
    try:
        record = binding(role, thread)
        if record is None or record['state'] == 'released':
            return None
        state = record['state']
        if state == 'bound':
            try:
                state = 'live' if fingerprint(record['pid']) == record['process_fingerprint'] else 'PID-reused'
            except (OSError, ValueError, subprocess.SubprocessError):
                state = 'unverified/dead'
        return str(path) + ' (' + state + '; explicit owner resolution required)'
    except (OSError, ValueError, KeyError, TypeError):
        return str(path) + ' (invalid; fail closed)'


def reserve(role, thread=0):
    with delivery.dispatch_guard():
        if binding(role, thread) is None:
            write(owner_path(role, thread), dict(schema_version=1, role=role, thread=thread,
                  repository=str(REPO), state='reserved', created_utc=now(),
                  reason='existing assigned owner; no replacement while identity is unbound'))
    return owner_path(role, thread)


def register(role, thread, executor, profile=None, session_id=None):
    who = identity(executor, profile, session_id)
    with delivery.dispatch_guard():
        old = binding(role, thread)
        if old and old['state'] == 'bound':
            stable = ('executor', 'session_id', 'profile', 'repository')
            if any(old.get(k) != who[k] for k in stable) or (executor == 'claude' and any(old.get(k) != v for k, v in who.items())):
                raise ValueError('different owner already bound; no takeover')
            if executor == 'codex' and any(old.get(k) != v for k, v in who.items()):
                # Same app thread can execute later turns in another host process.
                # Refresh only its own environment-attested identity, never another thread.
                old.update(**who, refreshed_utc=now())
                write(OWNERS / 'history' / (str(uuid.uuid4()) + '-refresh.json'), old)
                write(owner_path(role, thread), old)
            return old
        if old and old['state'] == 'released':
            raise ValueError('released slot requires explicit new assignment; no automatic rebind')
        record = dict(schema_version=1, role=role, thread=thread, state='bound',
                      binding_id=str(uuid.uuid4()), adopted_utc=now(), **who)
        write(owner_path(role, thread), record)
        history = OWNERS / 'history' / (record['binding_id'] + '.json')
        write(history, record)
        return record


def authenticate(record):
    who = identity(record['executor'], record.get('profile'), record['session_id'])
    fields = who if record['executor'] == 'claude' else ('executor', 'session_id', 'profile', 'repository')
    if any(record.get(k) != who[k] for k in fields):
        raise ValueError('only the bound owner may change its state')


def sprint_authority(sprint, tasks):
    selected = [t for t in sprint.get('tasks', []) if t.get('id') in tasks]
    if len(selected) != len(tasks) or not tasks:
        raise ValueError('tasks must exist in the current owner sprint')
    value = {k: sprint.get(k) for k in ('sprint_id', 'thread', 'executor', 'model')}
    value['tasks'] = [{k: t.get(k) for k in ('id', 'agent')} for t in selected]
    return hashlib.sha256(delivery.canonical(value).encode()).hexdigest()


def work_path(record):
    return OWNERS / 'work' / (record['binding_id'] + '.json')


def arm(thread, tasks, assignment):
    record = binding('coordinator', thread)
    if not record or record['state'] != 'bound':
        raise ValueError('self-register coordinator first')
    authenticate(record)
    source = delivery.safe_path(delivery.ARTIFACT_ROOT, Path(assignment).absolute())
    sprint = json.loads((delivery.ARTIFACT_ROOT / f'thread{thread}/sprint.json').read_text())
    if sprint.get('status') != 'active':
        raise ValueError('active bounded owner sprint required')
    value = dict(binding_id=record['binding_id'], session_id=record['session_id'], thread=thread,
                 sprint_id=sprint['sprint_id'], tasks=tasks, authority=sprint_authority(sprint, tasks),
                 assignment=str(source), assignment_sha256=delivery.sha(source),
                 state='active', started_utc=now(), blocks=0)
    with delivery.dispatch_guard():
        path = work_path(record)
        if path.exists():
            previous = read(path)
            if previous.get('state') == 'active':
                raise ValueError('work already active; do not reset continuation budget')
            write(OWNERS / 'history' / (str(uuid.uuid4()) + '-work.json'), previous)
        write(path, value)
    return value


def boundary(thread, state, evidence):
    if state not in ('completed', 'founder-gate', 'blocked', 'paused'):
        raise ValueError('invalid terminal boundary')
    record = binding('coordinator', thread)
    authenticate(record)
    evidence = delivery.safe_path(delivery.ARTIFACT_ROOT, Path(evidence).absolute())
    if not evidence.is_file():
        raise ValueError('existing concrete evidence required')
    with delivery.dispatch_guard():
        value = read(work_path(record))
        if state == 'completed':
            sprint = json.loads((delivery.ARTIFACT_ROOT / f'thread{thread}/sprint.json').read_text())
            if sprint_authority(sprint, value['tasks']) != value['authority'] or any(t.get('status') != 'done' for t in sprint['tasks'] if t.get('id') in value['tasks']):
                raise ValueError('selected tasks are not complete')
        value.update(state=state, boundary_evidence=str(evidence), boundary_sha256=delivery.sha(evidence), boundary_utc=now())
        write(work_path(record), value)
    return value


def release(role, thread):
    with delivery.dispatch_guard():
        record = binding(role, thread)
        if not record or record['state'] != 'bound':
            raise ValueError('only an existing bound owner may release')
        authenticate(record)
        record.update(state='released', released_utc=now())
        write(OWNERS / 'history' / (str(uuid.uuid4()) + '-release.json'), record)
        write(owner_path(role, thread), record)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    reg = commands.add_parser('register')
    reg.add_argument('--role', choices=('architect', 'coordinator'), required=True)
    reg.add_argument('--thread', type=int, default=0)
    reg.add_argument('--executor', choices=('claude', 'codex'), required=True)
    reg.add_argument('--profile'); reg.add_argument('--session-id')
    ar = commands.add_parser('arm')
    ar.add_argument('--thread', type=int, required=True); ar.add_argument('--tasks', nargs='+', required=True)
    ar.add_argument('--assignment', required=True)
    end = commands.add_parser('boundary')
    end.add_argument('--thread', type=int, required=True)
    end.add_argument('--state', choices=('completed', 'founder-gate', 'blocked', 'paused'), required=True)
    end.add_argument('--evidence', required=True)
    rel = commands.add_parser('release')
    rel.add_argument('--role', choices=('architect', 'coordinator'), required=True)
    rel.add_argument('--thread', type=int, default=0)
    commands.add_parser('status')
    args = parser.parse_args(argv)
    if args.action == 'register':
        result = register(args.role, args.thread, args.executor, args.profile, args.session_id)
    elif args.action == 'arm':
        result = arm(args.thread, args.tasks, args.assignment)
    elif args.action == 'boundary':
        result = boundary(args.thread, args.state, args.evidence)
    elif args.action == 'release':
        result = release(args.role, args.thread)
    else:
        result = {f'{role}{n or ""}': blocking_owner(role, n) for role, n in [('architect', 0), *[('coordinator', n) for n in (1, 2, 3)]]}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        raise SystemExit('Owner operation refused: ' + str(error))
