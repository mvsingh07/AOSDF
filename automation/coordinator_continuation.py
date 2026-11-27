#!/usr/bin/env python3
"""Opt-in continuation for the SAME bound coordinator; never launch an agent."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import uuid

import channel_delivery as delivery
import owner_sessions as owners
import wave

MAX_BLOCKS = 6
MAX_SECONDS = 900


def work(record):
    value = owners.read(owners.work_path(record))
    if value.get('binding_id') != record['binding_id'] or value.get('session_id') != record['session_id']:
        raise ValueError('continuation identity mismatch')
    sprint = json.loads((delivery.ARTIFACT_ROOT / f"thread{record['thread']}/sprint.json").read_text())
    if owners.sprint_authority(sprint, value['tasks']) != value['authority']:
        raise ValueError('sprint authority changed; reconcile and re-arm explicitly')
    source = delivery.safe_path(delivery.ARTIFACT_ROOT, Path(value['assignment']))
    if delivery.sha(source) != value['assignment_sha256']:
        raise ValueError('assignment source changed; reconcile')
    return value, sprint


def pending_events(record):
    # Peer snapshots are independent of the mutable architect channel. Do not
    # let an obsolete v1 digest prevent its recipient reading supplier mail.
    peers = delivery.peer_pending(record)
    if peers:
        return peers
    current = wave.active_wave()
    scope = wave.verified_thread_sprint(current, record['thread'])
    rounds = delivery.pending(recipient='coordinator', thread=record['thread'],
                              wave_id=current['wave_id'], scope=delivery.scope_sha(current, scope)) if scope else []
    return rounds


def mailbox_authority(record):
    import hashlib
    identity = {k: record[k] for k in ('binding_id', 'session_id', 'repository', 'thread')}
    return dict(authority=hashlib.sha256(delivery.canonical(identity).encode()).hexdigest(), sprint_id=None)


def mail_context(record):
    current = wave.active_wave()
    selected = wave.verified_thread_sprint(current, record['thread'])
    if not selected:
        raise ValueError('current verified communication wave/thread required')
    deadline = dt.datetime.fromisoformat(current['operating_deadline_utc'])
    if deadline.tzinfo is None or dt.datetime.now(dt.timezone.utc) >= deadline:
        raise ValueError('communication wave expired; no automatic renewal')
    for relative, expected in current.get('source_sha256', {}).items():
        source = delivery.safe_path(delivery.ARTIFACT_ROOT, delivery.ARTIFACT_ROOT / relative)
        if delivery.sha(source) != expected:
            raise ValueError('communication source pin changed')
    return current, delivery.scope_sha(current, selected), deadline


def mail_receipt_path(record):
    return owners.OWNERS / 'hooks' / (record['binding_id'] + '-mail.json')


def arm_mail(thread, timeout=900, max_blocks=6, as_architect=False):
    if type(timeout) is not int or not 1 <= timeout <= 3600 or type(max_blocks) is not int or not 1 <= max_blocks <= 24:
        raise ValueError('mail grant requires timeout1..3600 and blocks1..24')
    with delivery.dispatch_guard():
        record = owners.binding('coordinator', thread)
        if not record or record.get('state') != 'bound':
            raise ValueError('current bound recipient required')
        author = owners.binding('architect') if as_architect else record
        if not author or author.get('state') != 'bound':
            raise ValueError('bound grant author required')
        owners.authenticate(author)
        if owners.fingerprint(record['pid']) != record['process_fingerprint']:
            raise ValueError('recipient process identity changed')
        if owners.work_path(record).exists() and owners.read(owners.work_path(record)).get('state') in ('paused', 'continuation-exhausted'):
            raise ValueError('explicit paused/exhausted work must be reconciled; no work reset')
        current, scope, end = mail_context(record)
        import hashlib
        key = hashlib.sha256(delivery.canonical(dict(wave_id=current['wave_id'], scope=scope,
                                                     binding_id=record['binding_id'])).encode()).hexdigest()
        target = owners.OWNERS / 'hooks' / 'mail-grants' / (key + '.json')
        delivery.safe_path(owners.OWNERS, target)
        if target.exists():
            raise ValueError('mail grant already used for this wave/scope/binding; no reset/replay')
        path = mail_receipt_path(record)
        raw = path.read_bytes() if path.exists() else b''
        now = dt.datetime.now(dt.timezone.utc)
        deadline = min(end, now + dt.timedelta(seconds=timeout)).isoformat()
        grant = dict(schema_version=1, grant_id=key, wave_id=current['wave_id'], scope=scope,
                     source_sha256=current.get('source_sha256', {}), created_utc=now.isoformat(),
                     deadline_utc=deadline, max_seconds=timeout, max_blocks=max_blocks,
                     binding_id=record['binding_id'], session_id=record['session_id'], thread=thread,
                     author={k: author[k] for k in ('role', 'binding_id', 'session_id')},
                     prior_receipt_utf8=raw.decode('utf-8'), prior_receipt_sha256=hashlib.sha256(raw).hexdigest(),
                     communication_only=True, work_rearmed=False)
        # Both authority checks and create-only publication stay under dispatch lock.
        owners.authenticate(author)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('x') as handle:
            json.dump(grant, handle, sort_keys=True, indent=2)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        owners.write(path, dict(**mailbox_authority(record), binding_id=record['binding_id'],
                     session_id=record['session_id'], blocks=0, started_utc=None, state='explicitly-armed',
                     grant_id=key, grant_path=str(target), deadline_utc=deadline,
                     max_seconds=timeout, max_blocks=max_blocks, utc=owners.now()))
        return grant


def mail_limits(record, receipt):
    if not receipt.get('grant_id'):
        return MAX_BLOCKS, MAX_SECONDS, None
    grant = owners.read(Path(receipt['grant_path']))
    current, scope, end = mail_context(record)
    for key in ('binding_id', 'session_id', 'grant_id', 'deadline_utc', 'max_seconds', 'max_blocks'):
        if grant.get(key) != receipt.get(key):
            raise ValueError('explicit mail grant/receipt mismatch')
    if any(grant.get(k) != record[k] for k in ('binding_id', 'session_id', 'thread')):
        raise ValueError('mail grant target changed')
    if grant['wave_id'] != current['wave_id'] or grant['scope'] != scope or grant['source_sha256'] != current.get('source_sha256', {}):
        raise ValueError('mail grant wave/scope/source changed')
    if not grant.get('communication_only') or grant.get('work_rearmed') is not False:
        raise ValueError('invalid communication grant')
    if not 1 <= grant['max_blocks'] <= 24 or not 1 <= grant['max_seconds'] <= 3600:
        raise ValueError('invalid explicit mail bounds')
    deadline = dt.datetime.fromisoformat(grant['deadline_utc'])
    if deadline > end or deadline > dt.datetime.fromisoformat(grant['created_utc']) + dt.timedelta(seconds=grant['max_seconds']):
        raise ValueError('mail deadline exceeds original bounds')
    if owners.fingerprint(record['pid']) != record['process_fingerprint']:
        raise ValueError('mail recipient process changed')
    return grant['max_blocks'], grant['max_seconds'], deadline


def check_mail_wait(record):
    path = mail_receipt_path(record)
    if not path.exists():
        return None
    receipt = owners.read(path)
    if receipt.get('state') == 'continuation-exhausted':
        raise ValueError('mail response budget exhausted; explicit bounded arm-mail required')
    _, _, deadline = mail_limits(record, receipt)
    if deadline and dt.datetime.now(dt.timezone.utc) >= deadline:
        raise ValueError('explicit mail grant expired; no automatic rearm')
    return deadline


def mail_hook(record, payload, *, parked_state=None):
    """Communication does not require (or arm) an implementation sprint."""
    events = pending_events(record)
    value = mailbox_authority(record)
    waiting = native_waiter(record, value, payload)
    if parked_state in ('paused', 'continuation-exhausted'):
        return {'systemMessage': f'Work remains {parked_state}; {len(events)} unread messages. No automatic continuation or gate release.'}
    path = mail_receipt_path(record)
    previous = owners.read(path) if path.exists() else dict(**value, blocks=0, started_utc=None)
    if previous.get('authority') != value['authority']:
        raise ValueError('mailbox continuation identity changed')
    max_blocks, max_seconds, hard_deadline = mail_limits(record, previous)
    if hard_deadline and dt.datetime.now(dt.timezone.utc) >= hard_deadline:
        owners.write(path, dict(previous, state='continuation-exhausted', utc=owners.now()))
        return {'systemMessage': 'Explicit mailbox communication window expired; checkpoint. No automatic renewal.'}
    if not events and not waiting:
        return {'systemMessage': 'No unread coordinator mail or armed bounded work; continuation is not active.'}
    receipt = dict(previous, binding_id=record['binding_id'], session_id=record['session_id'],
                   utc=owners.now(), hook_seen=True, pending_notifications=len(events))
    if previous.get('state') == 'continuation-exhausted':
        return {'systemMessage': 'Mailbox continuation budget exhausted; checkpoint unread messages. No automatic rearm or replay.'}
    if waiting and not events:
        receipt.update(state='native-wait-armed', native_task_id=waiting)
        owners.write(path, receipt)
        return {}
    if previous['started_utc'] is None:
        receipt['started_utc'] = owners.now()
    age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(receipt['started_utc'])).total_seconds()
    if previous['blocks'] >= max_blocks or age >= max_seconds:
        receipt['state'] = 'continuation-exhausted'
        owners.write(path, receipt)
        return {'systemMessage': 'Mailbox continuation budget exhausted; checkpoint unread messages. No automatic rearm or replay.'}
    receipt.update(state='continued', blocks=previous['blocks'] + 1)
    owners.write(path, receipt)
    return {'decision': 'block', 'reason':
            'Read the exact pending coordinator messages in THIS bound session. For peer mail read its immutable '
            'snapshot and run channel_delivery.py peer-ack as yourself, then publish a linked answer or a concrete '
            'scoped blocker. For architect mail use its existing scoped ACK protocol and mark the actual current round token GREEN yourself after consumption. '
            'At the next safe wait, use THIS session native background Bash mailbox-only waiter per FILE-COORDINATION.md; do not detach or launch another actor. No new sprint, worker, task '
            'acceptance or runtime authority comes from a message. Preserve founder/paused/runtime gates; do not '
            'rerun accepted suites. Pending event paths: ' + ', '.join(e['path'] for e in events)}


def watched_workers(record, sprint, tasks):
    result = []
    agents = {t.get('agent') for t in sprint.get('tasks', []) if t.get('id') in tasks}
    for agent in agents:
        if not isinstance(agent, str) or agent not in (f"agent{record['thread']}-1", f"agent{record['thread']}-2"):
            raise ValueError('worker outside bound thread')
        folder = delivery.ARTIFACT_ROOT / f"thread{record['thread']}" / agent
        state_path = delivery.safe_path(delivery.ARTIFACT_ROOT, folder / 'state.json')
        state = json.loads(state_path.read_text())
        if state.get('status') in ('idle', 'consumed', 'completed'):
            continue
        location = state.get('result_location')
        if not location or not state.get('task_digest'):
            raise ValueError('worker result identity not pinned')
        target = delivery.safe_path(folder, folder / location)
        result.append(dict(agent=agent, state_path=str(state_path), result=str(target),
                           task_digest=state['task_digest'], dispatch_sequence=state.get('dispatch_sequence')))
    return result


def wait_path(record, wait_id):
    uuid.UUID(wait_id)
    return owners.OWNERS / 'waiters' / record['binding_id'] / (wait_id + '.json')


def native_waiter(record, work_value, payload):
    """Only the exact live native background command can justify yielding."""
    for task in payload.get('background_tasks', []):
        if task.get('type') != 'shell' or task.get('status') != 'running' or not task.get('id'):
            continue
        try:
            args = shlex.split(task.get('command', ''))
            mailbox_only = '--mailbox-only' in args
            if mailbox_only:
                if args.count('--mailbox-only') != 1 or args[-1] != '--mailbox-only':
                    continue
                args = args[:-1]
            if len(args) not in (7, 9) or Path(args[0]).name not in ('python3', 'python'):
                continue
            if Path(args[1]).absolute() != Path(__file__).absolute() or args[2:5] != ['wait', '--thread', str(record['thread'])] or args[5] != '--wait-id':
                continue
            if len(args) == 9 and (args[7] != '--timeout' or not 0 < int(args[8]) <= 3600):
                continue
            receipt = owners.read(wait_path(record, args[6]))
            if mailbox_only != (receipt.get('mode') == 'mailbox-only'):
                continue
            if receipt.get('state') != 'waiting' or receipt.get('binding_id') != record['binding_id'] or receipt.get('authority') != work_value['authority']:
                continue
            if receipt.get('sprint_id') != work_value['sprint_id'] or receipt.get('session_id') != record['session_id']:
                continue
            if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(receipt['deadline_utc']):
                continue
            if owners.fingerprint(receipt['pid']) != receipt['process_fingerprint']:
                continue
            return task['id']
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            continue
    return None


def hook(payload):
    if payload.get('hook_event_name') != 'Stop' or payload.get('agent_id'):
        return {}
    try:
        cwd = Path(payload.get('cwd', '')).resolve()
        if not cwd.is_relative_to(owners.REPO):
            return {}
        record = next((r for n in (1, 2, 3) if (r := owners.binding('coordinator', n)) and r.get('state') == 'bound'
                       and r.get('executor') == 'claude' and r.get('session_id') == payload.get('session_id')), None)
        if not record:
            return {}
        owners.authenticate(record)
        path = owners.work_path(record)
        if not path.exists():
            with delivery.dispatch_guard():
                return mail_hook(record, payload)
        with delivery.dispatch_guard():
            # Mail is communication even if an older sprint/source pin needs
            # reconciliation. It never inherits that sprint's dispatch authority.
            if pending_events(record):
                parked = owners.read(path).get('state')
                return mail_hook(record, payload, parked_state=parked)
            value, sprint = work(record)
            if value['state'] != 'active':
                if not pending_events(record) and not native_waiter(record, mailbox_authority(record), payload):
                    return {}
                return mail_hook(record, payload, parked_state=value['state'])
            events = pending_events(record)
            workers = watched_workers(record, sprint, value['tasks'])
            completed_results = [w['result'] for w in workers if Path(w['result']).is_file()]
            waiting = native_waiter(record, value, payload)
            age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(value['started_utc'])).total_seconds()
            receipt = dict(binding_id=record['binding_id'], session_id=record['session_id'], utc=owners.now(),
                           hook_seen=True, pending_notifications=len(events), available_results=completed_results)
            if waiting and not events and not completed_results:
                receipt.update(state='native-wait-armed', native_task_id=waiting)
                owners.write(owners.OWNERS / 'hooks' / (record['binding_id'] + '.json'), receipt)
                return {}
            if value['blocks'] >= MAX_BLOCKS or age >= MAX_SECONDS:
                value.update(state='continuation-exhausted', exhausted_utc=owners.now())
                owners.write(path, value)
                receipt['state'] = 'continuation-exhausted'
                owners.write(owners.OWNERS / 'hooks' / (record['binding_id'] + '.json'), receipt)
                return {'systemMessage': 'Continuation budget exhausted with unresolved work; checkpoint and report the exact blocker. No automatic rearm or replay.'}
            value['blocks'] += 1
            owners.write(path, value)
            receipt.update(state='continued', block=value['blocks'])
            owners.write(owners.OWNERS / 'hooks' / (record['binding_id'] + '.json'), receipt)
            reason = ('Your bounded assigned sprint is not at a recorded terminal boundary. Continue in THIS coordinator session: '
                      'plan-ready/next-action prose is intermediate. Dispatch authorized ready work, wait for workers, administratively '
                      'consume results, arrange required review, and advance. Do not rerun accepted suites. '
                      'Read/ack exact pending scoped notifications BEFORE editing their source. '
                      'When waiting, launch coordinator_continuation.py wait as your native background Bash task so completion '
                      'returns to this conversation. Do not detach with nohup/& or launch a replacement. '
                      'If genuinely blocked, at a founder gate, paused or complete, write concrete evidence and record '
                      'owner_sessions.py boundary. Preserve all source/runtime/security gates; do not manufacture approval.')
            if events:
                reason += ' Pending event paths: ' + ', '.join(event['path'] for event in events)
            if completed_results:
                reason += ' Result files available, NOT accepted: ' + ', '.join(completed_results)
            return {'decision': 'block', 'reason': reason}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, BlockingIOError) as error:
        return {'systemMessage': 'Continuation needs reconciliation; no new authority or launch: ' + str(error)}


def wait_for_work(thread, wait_id, timeout=3600, mailbox_only=False):
    if not 0 < timeout <= 3600:
        raise ValueError('wait timeout must be 1..3600 seconds')
    record = owners.binding('coordinator', thread)
    if not record or record.get('state') != 'bound':
        raise ValueError('existing bound coordinator required')
    owners.authenticate(record)
    if mailbox_only:
        mail_deadline = check_mail_wait(record)
        if mail_deadline:
            timeout = min(timeout, (mail_deadline - dt.datetime.now(dt.timezone.utc)).total_seconds())
            if timeout <= 0:
                raise ValueError('mail grant expired')
        value, workers = mailbox_authority(record), []
        if owners.work_path(record).exists():
            parked = owners.read(owners.work_path(record))
            if parked.get('state') in ('paused', 'continuation-exhausted'):
                raise ValueError('explicit pause/exhausted work must be reconciled before waiting')
    else:
        value, sprint = work(record)
        if value.get('state') != 'active':
            raise ValueError('arm current bounded work first')
        workers = watched_workers(record, sprint, value['tasks'])
    current = wave.active_wave()
    if not mailbox_only and not workers and not wave.verified_thread_sprint(current, thread):
        raise ValueError('no pinned worker or verified mailbox to wait for')
    path = wait_path(record, wait_id)
    with delivery.dispatch_guard():
        if path.exists():
            raise ValueError('wait ID already used; no replay')
        receipt_deadline = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=timeout)
        if mailbox_only and mail_deadline:
            receipt_deadline = min(receipt_deadline, mail_deadline)
        receipt = dict(binding_id=record['binding_id'], session_id=record['session_id'],
                       authority=value['authority'], sprint_id=value['sprint_id'], workers=workers,
                       pid=os.getpid(), process_fingerprint=owners.fingerprint(os.getpid()),
                       deadline_utc=receipt_deadline.isoformat(), state='waiting')
        if mailbox_only:
            receipt['mode'] = 'mailbox-only'
        owners.write(path, receipt)
    deadline = time.monotonic() + timeout
    state, detail = 'timeout', 'No event; checkpoint before explicitly rearming.'
    try:
        while time.monotonic() < deadline:
            if mailbox_only:
                check_mail_wait(record)
            actual_owner = owners.binding('coordinator', thread)
            if not actual_owner or actual_owner.get('state') != 'bound' or any(actual_owner.get(k) != record.get(k) for k in ('binding_id', 'session_id')):
                state, detail = 'owner-changed', 'Owner binding changed; do not resume or replace.'
                break
            if owners.fingerprint(record['pid']) != record['process_fingerprint']:
                state, detail = 'owner-changed', 'Owner process changed; do not resume or replace.'
                break
            if not mailbox_only:
                current_work, _ = work(record)
                if current_work.get('state') != 'active':
                    state, detail = 'boundary', 'Bound work was parked/completed; no automatic continuation.'
                    break
            elif owners.work_path(record).exists():
                parked = owners.read(owners.work_path(record))
                if parked.get('state') in ('paused', 'continuation-exhausted'):
                    state, detail = 'boundary', 'Explicit pause/exhaustion; no automatic continuation.'
                    break
            for worker in workers:
                actual = json.loads(Path(worker['state_path']).read_text())
                if actual.get('task_digest') != worker['task_digest'] or actual.get('dispatch_sequence') != worker['dispatch_sequence']:
                    raise ValueError('watched worker identity changed')
                target = delivery.safe_path(Path(worker['state_path']).parent, Path(worker['result']))
                if target.is_file():
                    state, detail = 'worker-result', str(target) + ' available; verify identity and consume administratively. Not accepted by watcher.'
                    break
            if state == 'worker-result':
                break
            events = pending_events(record)
            if events:
                state, detail = 'notification', ', '.join(event['path'] for event in events) + ' queued; read/ack before editing source.'
                break
            time.sleep(min(1, max(0, deadline - time.monotonic())))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        state, detail = 'reconcile', str(error)
    finally:
        receipt.update(state=state, detail=detail, ended_utc=owners.now())
        with delivery.dispatch_guard():
            owners.write(path, receipt)
    print(json.dumps({'state': state, 'detail': detail, 'read_acknowledged': False, 'accepted': False}))
    return 0 if state in ('worker-result', 'notification') else 124


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('hook')
    arm = sub.add_parser('arm-mail')
    arm.add_argument('--thread', type=int, required=True, choices=(1, 2, 3))
    arm.add_argument('--timeout', type=int, default=900)
    arm.add_argument('--max-blocks', type=int, default=6)
    arm.add_argument('--as-architect', action='store_true')
    wait = sub.add_parser('wait'); wait.add_argument('--thread', type=int, required=True)
    wait.add_argument('--wait-id', required=True); wait.add_argument('--timeout', type=int, default=3600)
    wait.add_argument('--mailbox-only', action='store_true')
    args = parser.parse_args()
    if args.action == 'arm-mail':
        print(json.dumps(arm_mail(args.thread, args.timeout, args.max_blocks, args.as_architect)))
        return 0
    if args.action == 'hook':
        print(json.dumps(hook(json.load(sys.stdin))))
        return 0
    return wait_for_work(args.thread, args.wait_id, args.timeout, args.mailbox_only)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        raise SystemExit('Continuation refused: ' + str(error))
