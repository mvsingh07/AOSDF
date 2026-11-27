#!/usr/bin/env python3
"""architect_invoke.py — invoke the Solution Architect to write an ARCHITECT block.

This is roadmap step 2 of the coordinator<->architect channel (see
`coordinator-architect/README.md` "Auto Mode" and the main `README.md` roadmap): the
architect write-back that `architect_bridge.py` *detects-and-triggers* when a coordinator
posts an `AWAITING-ARCHITECT` round. The founder's trigger is exactly that channel write:
one lead coordinator adding its `COORDINATOR -> ARCHITECT` round (status AWAITING-ARCHITECT)
is the event that calls the Solution Architect.

Separation of concerns (same shape as the worker path):
  * visible_launch.py  = the launch MECHANISM (a visible, watchable Terminal window).
  * architect_invoke.py = builds the architect's boot prompt + the launch, dry-run previewable.
  * architect_bridge.py --auto = the GATE that decides WHETHER this may run live.

Like `supervisor.py --dispatch` and `--pilot-real`, the live path is dual-gated and off by
default; `dry_run=True` (the default for preview) opens nothing and returns the exact prompt
and command that WOULD run. This module never writes into the channel itself — only the
launched architect session writes the ARCHITECT block, by hand, under its own role rules.
It grants no authorization: the architect it launches still cannot cross a hard gate
(it ESCALATEs instead). Status authority stays `execution_plan.md`; the Solution Architect stays sole writer.

Usage (normally called by architect_bridge, but runnable directly for preview/pilot):
    python3 architect_invoke.py --preview 2            # build+print the prompt/command, launch nothing
    python3 architect_invoke.py --invoke 2             # live launch (refused unless the bridge dual-gate is set)
    python3 architect_invoke.py --preview 2 --model opus
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path
import channel_delivery as _delivery

import architect_bridge as _bridge
import visible_launch as _vl
import wave as _wave

HERE = os.path.dirname(os.path.abspath(__file__))
VAR_DIR = os.path.join(HERE, "var")
RUNS_DIR = os.path.join(VAR_DIR, "architect-runs")

# Workspace root (holds AGENTS.md) — up 6 from automation/.
from layout import PROJECT_ROOT
REPO_ROOT = str(PROJECT_ROOT)
# 05_AI_Agent_System dir — up 2 from automation/.
AGENT_SYS_DIR = str(Path(HERE).parent)
# coordination-threads dir — up 1 from automation/ (holds SPRINT-TRACKER.md).
from layout import THREADS
THREADS_DIR = str(THREADS)
SPRINT_TRACKER = os.path.join(THREADS_DIR, "SPRINT-TRACKER.md")
# documents/ dir — up 3 from automation/ (holds 06_Execution_Plan/).
DOCS_DOCUMENTS_DIR = str(Path(HERE).parent)
EXEC_PLAN = os.path.join(DOCS_DOCUMENTS_DIR, "06_Execution_Plan", "execution_plan.md")

DEFAULT_MODEL = "opus"  # planning/verification role -> frontier model


# Existing-owner transport only. No server/thread creation or permission changes.
class NativeControl:
    MAX_FRAME = 256 * 1024

    def __init__(self, endpoint, owner, timeout):
        import socket, stat, time
        if not 1 <= timeout <= 60:
            raise ValueError('native delivery timeout must be 1..60 seconds')
        endpoint = Path(endpoint)
        if not endpoint.is_absolute() or '..' in endpoint.parts:
            raise ValueError('absolute private control socket required')
        for part in (endpoint, *endpoint.parents):
            if part.is_symlink():
                raise ValueError('symlink control socket path refused')
        info, parent = endpoint.stat(), endpoint.parent.stat()
        if not (stat.S_ISSOCK(info.st_mode) and info.st_uid == os.getuid() and
                info.st_mode & 0o777 == 0o600 and parent.st_uid == os.getuid() and
                stat.S_ISDIR(parent.st_mode) and parent.st_mode & 0o777 == 0o700):
            raise ValueError('control endpoint must be private same-user socket/directory')
        self.deadline = time.monotonic() + timeout
        self.buffer = b''
        self.started = set()
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self._timeout(); self.sock.connect(str(endpoint))
            import struct
            if sys.platform == 'darwin':
                pid = struct.unpack('i', self.sock.getsockopt(0, 2, 4))[0]  # LOCAL_PEERPID
            elif sys.platform.startswith('linux'):
                pid, uid, _ = struct.unpack('3i', self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                if uid != os.getuid():
                    raise ValueError('control peer uid mismatch')
            else:
                raise ValueError('OS peer PID verification unsupported')
            import owner_sessions
            if pid != owner['pid'] or owner_sessions.fingerprint(pid) != owner['process_fingerprint']:
                raise ValueError('control peer PID/fingerprint mismatch')
            self.peer_pid = pid
            self._upgrade()
        except BaseException:
            self.sock.close()
            raise

    def _timeout(self):
        import time
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('native delivery deadline expired')
        self.sock.settimeout(remaining)

    def _read(self, size):
        while len(self.buffer) < size:
            self._timeout()
            data = self.sock.recv(min(4096, size - len(self.buffer)))
            if not data:
                raise ConnectionError('control connection closed')
            self.buffer += data
        result, self.buffer = self.buffer[:size], self.buffer[size:]
        return result

    def _upgrade(self):
        import base64, hashlib
        key = base64.b64encode(os.urandom(16)).decode()
        request = ('GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\n'
                   'Connection: Upgrade\r\nSec-WebSocket-Key: ' + key + '\r\n'
                   'Sec-WebSocket-Version: 13\r\n\r\n')
        self._timeout(); self.sock.sendall(request.encode())
        while b'\r\n\r\n' not in self.buffer:
            self._timeout(); data = self.sock.recv(4096)
            if not data:
                raise ConnectionError('closed during WebSocket upgrade')
            self.buffer += data
            if len(self.buffer) > 16384:
                raise ValueError('oversize WebSocket upgrade')
        header, self.buffer = self.buffer.split(b'\r\n\r\n', 1)
        lines = header.decode('ascii').split('\r\n')
        if lines[0].split()[:2] != ['HTTP/1.1', '101']:
            raise ValueError('WebSocket upgrade refused')
        headers = {}
        for line in lines[1:]:
            key_name, value = line.split(':', 1)
            key_name = key_name.strip().lower()
            if key_name in headers:
                raise ValueError('duplicate WebSocket upgrade header')
            headers[key_name] = value.strip()
        expected = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
        if (headers.get('sec-websocket-accept') != expected or headers.get('upgrade', '').lower() != 'websocket'
                or 'upgrade' not in [v.strip().lower() for v in headers.get('connection', '').split(',')]
                or 'sec-websocket-extensions' in headers):
            raise ValueError('invalid or compressed WebSocket upgrade')

    def send(self, value, opcode=1):
        import struct
        body = json.dumps(value, separators=(',', ':')).encode() if opcode == 1 else value
        if len(body) > self.MAX_FRAME:
            raise ValueError('native frame too large')
        mask = os.urandom(4); size = len(body)
        length = bytes([size | 128]) if size < 126 else bytes([126 | 128]) + struct.pack('!H', size) if size <= 65535 else bytes([127 | 128]) + struct.pack('!Q', size)
        frame = bytes([128 | opcode]) + length + mask + bytes(v ^ mask[i % 4] for i, v in enumerate(body))
        self._timeout(); self.sock.sendall(frame)

    def receive(self):
        import struct
        for _ in range(512):
            first, second = self._read(2)
            if not first & 128 or first & 112 or second & 128:
                raise ValueError('fragmented/compressed/masked server frame refused')
            opcode, size = first & 15, second & 127
            if size == 126:
                size = struct.unpack('!H', self._read(2))[0]
            elif size == 127:
                size = struct.unpack('!Q', self._read(8))[0]
            if size > self.MAX_FRAME or (opcode >= 8 and size > 125):
                raise ValueError('oversize native frame')
            body = self._read(size)
            if opcode == 9:
                self.send(body, 10); continue
            if opcode == 10:
                continue
            if opcode != 1:
                raise ConnectionError('closed or unsupported native frame')
            message = json.loads(body)
            if not isinstance(message, dict):
                raise ValueError('invalid native JSON message')
            if 'method' in message and 'id' in message:
                raise ValueError('native server request requires human/client handling; no approval sent')
            if message.get('method') == 'turn/started':
                params = message.get('params', {})
                if not isinstance(params, dict) or not isinstance(params.get('turn'), dict):
                    raise ValueError('malformed native turn notification')
                self.started.add((params.get('threadId'), params.get('turn', {}).get('id')))
            return message
        raise ValueError('native control-frame bound exceeded')

    def rpc(self, method, params, request_id):
        if method not in ('initialize', 'thread/read', 'turn/start', 'thread/turns/list'):
            raise ValueError('native RPC outside fixed delivery allowlist')
        self.send({'id': request_id, 'method': method, 'params': params})
        for _ in range(512):
            message = self.receive()
            if message.get('id') == request_id:
                if 'error' in message:
                    raise ValueError('native RPC rejected: ' + str(message['error'].get('message', 'unknown'))[:192])
                return message['result']
        raise ValueError('native notification bound exceeded')

    def latest_completion(self, thread_id, turn_id, request_id=100):
        result = self.rpc('thread/turns/list', {'threadId': thread_id, 'limit': 1,
                         'sortDirection': 'desc', 'itemsView': 'notLoaded'}, request_id)
        turns = result.get('data')
        if not isinstance(turns, list) or len(turns) > 1:
            raise ValueError('invalid bounded turn metadata response')
        if not turns or not isinstance(turns[0], dict) or turns[0].get('id') != turn_id:
            return {'turn_id': turn_id, 'status': 'unknown', 'reason': 'newest-turn-mismatch-or-absent',
                    'observation': 'bounded-metadata-readback', 'new_turn_started_observed': False}
        status = turns[0].get('status')
        if status not in ('inProgress', 'completed', 'failed', 'interrupted'):
            raise ValueError('unknown native turn status')
        return {'turn_id': turn_id, 'status': status, 'observation': 'bounded-metadata-readback',
                'new_turn_started_observed': (thread_id, turn_id) in self.started}

    def completed(self, thread_id, turn_id):
        import time
        for index in range(60):
            result = self.latest_completion(thread_id, turn_id, 100 + index)
            if result['status'] != 'inProgress':
                return result
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('original completion deadline expired')
            time.sleep(min(1, remaining))
        raise TimeoutError('native metadata poll bound exceeded')

    def close(self):
        self.sock.close()


def _native_record(path, value, *, create=False):
    import tempfile
    path = _delivery.safe_path(Path(RUNS_DIR), Path(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    if create:
        with path.open('x') as handle:
            json.dump(value, handle, indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        return
    descriptor, temporary = tempfile.mkstemp(prefix='.native-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as handle:
            json.dump(value, handle, indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _native_envelope():
    current = _wave.active_wave()
    if not current or current.get('delivery_only') is not True or current.get('autonomous') is not False:
        raise ValueError('authorized delivery-only/non-autonomous envelope required')
    for relative, expected in current.get('source_sha256', {}).items():
        source = Path(os.path.abspath(Path(THREADS_DIR) / relative))
        _delivery.safe_path(Path(THREADS_DIR).parent, source)
        if _delivery.sha(source) != expected:
            raise ValueError('native delivery wave source pin changed')
    return current


def _native_event(notification, owner, current):
    import hashlib, uuid
    notification = Path(notification).absolute()
    if '..' in notification.parts:
        raise ValueError('invalid native event path')
    # Standard queue events retain their ordinary scoped-round verification.
    if notification.is_relative_to(_delivery.MAILBOX_ROOT / 'architect'):
        _delivery.safe_path(_delivery.MAILBOX_ROOT, notification)
        raw = json.loads(notification.read_text())
        scoped = _wave.verified_thread_sprint(current, raw['thread'])
        if not scoped:
            raise ValueError('unverified native event scope')
        event = _delivery.load(notification, recipient='architect', thread=raw['thread'],
                               wave_id=current['wave_id'], scope=_delivery.scope_sha(current, scoped))
        latest = owed_round(event['thread'])
        if not latest or latest['round'] != event['round'] or not _bridge.scoped_round(event['thread'], current, latest):
            raise ValueError('native round no longer owed')
        source = Path(_thread_channel_path(event['thread'])).absolute()
        if source != Path(THREADS_DIR) / event['source']:
            raise ValueError('native event source is not the thread channel')
        return event['id'], source, event['source_sha256']
    _delivery.safe_path(Path(RUNS_DIR), notification)
    event = json.loads(notification.read_text())
    required = {'schema_version', 'kind', 'created_utc', 'source', 'source_sha256', 'target_session_id',
                'target_binding_id', 'sender_role', 'sender_session_id', 'actor_launch_authority', 'auto_activation', 'event_id'}
    if set(event) != required or event['schema_version'] != 1 or event['kind'] != 'bounded-tooling-native-handoff':
        raise ValueError('invalid native tooling event')
    if (event['target_session_id'] != owner['session_id'] or event['target_binding_id'] != owner['binding_id']
            or event['sender_role'] != 'bounded-tooling-repair-owner' or event['actor_launch_authority'] is not False
            or event['auto_activation'] is not False):
        raise ValueError('native tooling owner/authority mismatch')
    uuid.UUID(event['sender_session_id'])
    if hashlib.sha256(_delivery.canonical({k:v for k,v in event.items() if k != 'event_id'}).encode()).hexdigest() != event['event_id']:
        raise ValueError('native tooling event digest mismatch')
    source = _delivery.safe_path(Path(THREADS_DIR), Path(event['source']))
    if source.suffix != '.md' or source.parent != Path(THREADS_DIR) or source.stat().st_size > 256 * 1024 or _delivery.sha(source) != event['source_sha256']:
        raise ValueError('native tooling source mismatch/path/size')
    return event['event_id'], source, event['source_sha256']


def deliver_existing_native(notification, endpoint, expected_binding, timeout=45, *, wake_window=None):
    """One existing-owner turn, never a daemon arm/new actor/ACK or retry."""
    import owner_sessions as owners
    import time
    if not 1 <= timeout <= 60:
        raise ValueError('native delivery timeout must be 1..60 seconds')
    deadline = min(time.monotonic() + timeout, wake_window.deadline_mono) if wake_window else time.monotonic() + timeout
    client = None; attempt = None; path = None
    try:
        with _delivery.dispatch_guard():
            current = _native_envelope(); owner = owners.binding('architect')
            if not owner or owner.get('state') != 'bound' or owner.get('executor') != 'codex' or owner.get('binding_id') != expected_binding:
                raise ValueError('exact existing Codex architect binding required')
            event_id, source, digest = _native_event(notification, owner, current)
            path = Path(RUNS_DIR) / 'native-deliveries' / (event_id + '.json')
            _delivery.safe_path(Path(RUNS_DIR), path)
            if path.exists():
                return {'state': 'already-attempted', 'attempt': json.loads(path.read_text()), 'resent': False}
            # Keep the shared dispatch-lock phase brief even if a socket stalls.
            client = NativeControl(endpoint, owner, min(timeout, 5))
            client.deadline = min(client.deadline, deadline)
            client.rpc('initialize', {'clientInfo': {'name': 'comms_existing_architect_bridge', 'version': '1.0'}}, 1)
            client.send({'method': 'initialized'})
            thread = client.rpc('thread/read', {'threadId': owner['session_id'], 'includeTurns': False}, 2)['thread']
            if thread.get('id') != owner['session_id'] or Path(thread.get('cwd', '')).resolve() != Path(REPO_ROOT).resolve():
                raise ValueError('control thread identity/repository mismatch')
            if thread.get('status', {}).get('type') != 'idle':
                return {'state': 'queued-owner-not-idle', 'sent': False}
            # Recheck every authority/source pin immediately before reservation/write.
            if owners.binding('architect') != owner or _native_envelope() != current or _native_event(notification, owner, current) != (event_id, source, digest):
                raise ValueError('native delivery selection changed')
            prompt = (f'Bounded coordination event for your existing architect session {owner["session_id"]}, binding {expected_binding}. '
                      f'Read exact event {Path(notification).absolute()} and source {source}. Source SHA256 {digest}. '
                      'Authenticate your bound identity. Supply your OWN read ACK/response as requested by that source; '
                      'do not replay peers or change owners/profiles/Auto/product gates. This came from the existing Python bridge.')
            if len(prompt.encode()) > 1000:
                raise ValueError('native coordination prompt exceeds bound')
            attempt = dict(schema_version=1, event_id=event_id, source_sha256=digest,
                           target_session_id=owner['session_id'], target_binding_id=expected_binding,
                           socket_peer_pid=client.peer_pid, idle_before_submission=True,
                           state='reserved', created_utc=_utc(), read_acknowledged=False, accepted=False)
            if wake_window:
                wake_window.reserve(event_id, notification, digest, owner, current)
                attempt['wake_window_id'] = wake_window.manifest['window_id']
            _native_record(path, attempt, create=True)
            if wake_window:
                wake_window.pre_submit(event_id, notification, digest, owner, current)
            # This single write may have taken effect even if its reply is lost.
            result = client.rpc('turn/start', {'threadId': owner['session_id'], 'input': [{'type':'text', 'text':prompt}]}, 3)
            turn_id = result['turn']['id']
            attempt.update(state='submitted', turn_id=turn_id, submitted_utc=_utc())
            _native_record(path, attempt)
            client.deadline = deadline
        # Do not hold the shared dispatch lock while the architect works.
        completion = client.completed(owner['session_id'], turn_id)
        attempt.update(state='native-completed' if completion['status'] == 'completed' else 'completion-needs-reconciliation',
                       completion=completion, ended_utc=_utc())
        if owners.binding('architect') != owner:
            attempt['state'] = 'owner-changed-after-submit'
        with _delivery.dispatch_guard():
            _native_record(path, attempt)
        return attempt
    except (OSError, ValueError, KeyError, TypeError, ConnectionError) as error:
        if attempt is None:
            raise
        attempt.update(state='submitted-uncertain' if attempt.get('turn_id') else 'write-outcome-uncertain',
                       error=str(error)[:256], ended_utc=_utc(), automatic_retry=False)
        with _delivery.dispatch_guard():
            _native_record(path, attempt)
        return attempt
    finally:
        if client:
            client.close()


def reconcile_existing_native(notification, endpoint, expected_binding, timeout=5):
    """One metadata-only observation of an existing attempt; never re-submit."""
    import owner_sessions as owners
    client = None
    try:
        with _delivery.dispatch_guard():
            current = _native_envelope(); owner = owners.binding('architect')
            if not owner or owner.get('state') != 'bound' or owner.get('executor') != 'codex' or owner.get('binding_id') != expected_binding:
                raise ValueError('exact existing Codex architect binding required')
            event_id, source, digest = _native_event(notification, owner, current)
            attempt_path = _delivery.safe_path(Path(RUNS_DIR), Path(RUNS_DIR) / 'native-deliveries' / (event_id + '.json'))
            before = attempt_path.read_bytes(); attempt = json.loads(before)
            if (attempt.get('event_id') != event_id or attempt.get('target_session_id') != owner['session_id']
                    or attempt.get('target_binding_id') != expected_binding or attempt.get('source_sha256') != digest
                    or not isinstance(attempt.get('turn_id'), str) or not 1 <= len(attempt['turn_id']) <= 128):
                raise ValueError('readback requires exact stored target/event/submitted turn')
            result_path = attempt_path.with_suffix('.readback.json')
            _delivery.safe_path(Path(RUNS_DIR), result_path)
            if result_path.exists():
                return {'state': 'already-reconciled', 'observation': json.loads(result_path.read_text()), 'resent': False}
            client = NativeControl(endpoint, owner, min(timeout, 5))
            client.rpc('initialize', {'clientInfo': {'name': 'comms_existing_architect_readback', 'version': '1.0'}}, 1)
            client.send({'method': 'initialized'})
            thread = client.rpc('thread/read', {'threadId': owner['session_id'], 'includeTurns': False}, 2)['thread']
            if thread.get('id') != owner['session_id'] or Path(thread.get('cwd', '')).resolve() != Path(REPO_ROOT).resolve():
                raise ValueError('readback thread identity/repository mismatch')
            if owners.binding('architect') != owner or _native_envelope() != current or _native_event(notification, owner, current) != (event_id, source, digest):
                raise ValueError('readback identity/source selection changed')
            completion = client.latest_completion(owner['session_id'], attempt['turn_id'])
            if attempt_path.read_bytes() != before:
                raise ValueError('attempt changed while reconciling')
            result = dict(schema_version=1, event_id=event_id, target_session_id=owner['session_id'],
                          target_binding_id=expected_binding, source_sha256=digest, turn_id=attempt['turn_id'],
                          state='reconciled-native-completed' if completion['status'] == 'completed' else 'reconciliation-unknown',
                          completion=completion, observation_utc=_utc(), original_attempt_preserved=True,
                          payload_submitted=False, read_acknowledged=False, accepted=False)
            _native_record(result_path, result, create=True)
            return result
    finally:
        if client:
            client.close()


def _launch_architect(*args, thread_n=None, expected_round=None, notification=None, **kwargs):
    if kwargs.get("dry_run", False):
        return _vl.launch_visible(*args, **kwargs)
    with _delivery.dispatch_guard():
        import coordinator_trigger as trigger
        _delivery.foreign_controller_conflict()
        if _delivery.active_architect():
            return {"refused": "an architect is already active; notification stays pending"}
        wave = _wave.active_wave()
        if thread_n is not None:
            current = owed_round(thread_n)
            scoped = _bridge.scoped_round(thread_n, wave, current)
            if current != expected_round or not scoped:
                return {"refused": "architect request changed before launch"}
            _delivery.load(notification, recipient="architect", thread=thread_n,
                           wave_id=wave["wave_id"], scope=_delivery.scope_sha(wave, scoped))
        for n in (1, 2, 3):
            if trigger.live_coordinator_run(n):
                latest = _bridge._latest_round(_thread_channel_path(n))
                if thread_n is None or not _bridge._owed(latest) or not _bridge.scoped_round(n, wave, latest):
                    return {"refused": "a coordinator is active outside a verified architect-wait boundary"}
        return _vl.launch_visible(*args, record_pid=True, **kwargs)


def _utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _thread_channel_path(thread_n: int) -> str:
    return os.path.join(_bridge.CHANNEL_DIR, f"thread{thread_n}.md")


def owed_round(thread_n: int):
    """Return the thread's latest round dict iff it currently owes the architect, else None."""
    latest = _bridge._latest_round(_thread_channel_path(thread_n))
    return latest if _bridge._owed(latest) else None


def boot_prompt(thread_n: int, round_rec: dict) -> str:
    """The single boot line that points the launched Solution Architect at its files.

    Behaviour lives in the files, not the prompt (founder directive 2026-10-23): the prompt
    only names what to read and the one bounded thing to do.
    """
    agents_md = os.path.join(REPO_ROOT, "AGENTS.md")
    channel_readme = os.path.join(_bridge.CHANNEL_DIR, "README.md")
    role_def = os.path.join(AGENT_SYS_DIR, "agents", "solution_architect_agent.md")
    thread_md = _thread_channel_path(thread_n)
    k = round_rec.get("round")
    checkpoint = round_rec.get("checkpoint")
    wave_text = _wave.boot_addendum(_wave.active_wave())
    return (
        f"You are the Solution Architect for the Supagram coordination system. You were "
        f"auto-invoked because the Thread {thread_n} coordinator opened alignment round {k} "
        f"(checkpoint: {checkpoint}, status AWAITING-ARCHITECT). "
        f"Read, in order: {agents_md}; {role_def}; {channel_readme}; then the open round in "
        f"{thread_md}. Read anything else you need to judge it — the canonical execution_plan.md, "
        f"the milestone acceptance criteria, the governing ADRs, identified_gaps.md, the manual-action "
        f"tracker, live code/contracts/migrations, and the other threads' channel files — you are not "
        f"limited to the channel file. Your remit is narrow: confirm the proposed next scope/partition is "
        f"correct and that tasks are divided across threads with no overlap or conflict. "
        f"Handle sprint completion, actual cross-thread conflicts and ownership ambiguity only. "
        f"Coordinators proceed autonomously within their reviewed sprint; do not introduce an architect "
        f"approval before each dispatch or re-review an accepted source slice. "
        f"Write ONLY the `ARCHITECT -> COORDINATOR` block for round {k} in {thread_md}, set that round's "
        f"machine-comment status token to your verdict (ALIGNED | REDIRECT | HOLD | ESCALATE), and stop. "
        f"Do NOT write code, a worker task.md, execution_plan.md status, or implementation_prompts plans, "
        f"and do NOT cross or grant any hard gate (push/deploy/publish, DNS, live-send, spend, secrets, "
        f"live-data deletion, Class-B/C) — for anything requiring a founder decision, use ESCALATE and name "
        f"exactly what the founder must decide and why. Apply the architect autonomy policy in your role "
        f"definition: decide and proceed within your remit; do not ask routine questions. When the block is "
        f"written, print one line: 'Thread {thread_n} round {k} -> <verdict>'. "
        + _wave.OWNERSHIP_ARCHITECT
        + wave_text
    )


def manual_boot_prompt(topic: str | None) -> str:
    """Boot line for a founder-initiated, interactive architect session (not tied to a round).

    Request (founder 2026-10-28): "a manual thread of the Solution Architect can be called by the
    founder to address changes in model selection or anything required."
    """
    agents_md = os.path.join(REPO_ROOT, "AGENTS.md")
    role_def = os.path.join(AGENT_SYS_DIR, "agents", "solution_architect_agent.md")
    channel_readme = os.path.join(_bridge.CHANNEL_DIR, "README.md")
    focus = (f"The founder wants to discuss: {topic}. " if topic
             else "The founder will tell you what to address (e.g. model selection, a scope or "
                  "partition question, a wave change). ")
    return (
        f"You are the Solution Architect for the Supagram coordination system, launched MANUALLY and "
        f"INTERACTIVELY by the founder (not auto-invoked by a channel round). {focus}"
        f"Read, as needed: {agents_md}; {role_def}; {channel_readme}; and the canonical sources. "
        f"This is a conversation: discuss, decide and act within your remit and the architect autonomy "
        f"policy in your role definition. You MAY update the automation wave (config/wave.json via "
        f"wave.py), the architect/coordinator model choices, and alignment rounds. Do NOT cross or grant "
        f"any hard gate (push/deploy/publish, DNS, live-send, spend, secrets, live-delete, Class-B/C) — "
        f"name those for the founder to decide. "
        + _wave.OWNERSHIP_ARCHITECT
    )


def wave_boot_prompt(wave: dict) -> str:
    """Boot line for a wave BEGIN/CONTINUE launch from initiate_automation.py's single command.

    The founder has just chosen (interactively) to start or continue this wave, so this is a
    founder-initiated launch, not the unattended auto-daemon path. The architect maps the wave's
    sprints to the canonical plan + tracker, confirms partitions, and opens the first alignment
    round per thread so the coordinators can proceed. The wave autonomy (no per-sprint approval)
    is carried by the wave addendum; hard gates still stop it via ESCALATE.
    """
    agents_md = os.path.join(REPO_ROOT, "AGENTS.md")
    role_def = os.path.join(AGENT_SYS_DIR, "agents", "solution_architect_agent.md")
    channel_readme = os.path.join(_bridge.CHANNEL_DIR, "README.md")
    threads = ", ".join(sorted({str(s.get("thread")) for s in wave.get("sprints", [])}))
    return (
        f"You are the Solution Architect for the Supagram coordination system, launched by the founder "
        f"to BEGIN/CONTINUE automation wave {wave.get('wave_id')} ('{wave.get('title','')}'). "
        f"Read, in order: {agents_md}; {role_def}; {channel_readme}; the canonical plan {EXEC_PLAN}; and "
        f"the sprint view {SPRINT_TRACKER}. Also read whatever you need to judge scope — the milestone "
        f"acceptance criteria, governing ADRs, identified_gaps.md, the manual-action tracker, and live "
        f"code/contracts/migrations. "
        f"For each sprint in this wave: map its execution_plan.md tasks onto SPRINT-TRACKER.md and mark "
        f"them 'mapped'; confirm the thread partition (threads {threads}) is correct and non-overlapping. "
        f"Before any coordinator launch, record exact ordered task_ids, scope_review_ref, model_policy, "
        f"target_tier and founder_auth_ref "
        f"and the new opening_round number for each sprint in config/wave.json; set "
        f"verified_by_architect=true only after objective, hold, tier and ownership checks pass. "
        f"For a founder-approved wave only, open the numbered "
        f"bootstrap alignment round (bootstrap:wave:<id>) for each thread's coordinator in "
        f"{os.path.join(_bridge.CHANNEL_DIR, 'thread<N>.md')} (write your ARCHITECT verdict ALIGNED with the "
        f"next bounded scope so the coordinator_trigger can launch it). Advance the wave's sprints without "
        f"returning to the founder between sprints. When a sprint's acceptance passes, mark its tasks "
        f"'completed' in the tracker and reconcile that into execution_plan.md. "
        + _wave.OWNERSHIP_ARCHITECT
        + _wave.boot_addendum(wave)
    )


def _architect_argv(prompt, model, claude_bin, *, automatic=False):
    from pathlib import Path
    executor, model = _vl.execution_choice("claude", model)
    if executor == "codex":
        argv = (_vl.codex_headless_argv(Path(REPO_ROOT), prompt, full_auto=True, model=model)
                if automatic else _vl.codex_interactive_argv(Path(REPO_ROOT), prompt, model=model))
    else:
        argv = _vl.claude_argv(Path(REPO_ROOT), prompt, model=model, claude_bin=claude_bin,
                               skip_permissions=automatic, extra=["--print"] if automatic else None)
    return executor, model, argv


def invoke_wave(wave: dict, *, dry_run: bool = False, model: str = DEFAULT_MODEL,
                claude_bin: str = "claude") -> dict:
    """Open a visible Solution Architect window to begin/continue a founder-approved wave.

    Founder-initiated from initiate_automation.py (the founder just confirmed at the terminal), so
    it is NOT dual-gated the way the unattended --auto write-back is. Interactive (the founder can
    watch and intervene); the launched architect still cannot cross a hard gate (it ESCALATEs)."""
    from pathlib import Path
    rec = {"created_utc": _utc(), "mode": "wave-begin", "wave_id": wave.get("wave_id"),
           "model": model, "dry_run": dry_run}
    prompt = wave_boot_prompt(wave)
    rec["prompt"] = prompt
    executor, rec["model"], argv = _architect_argv(prompt, model, claude_bin)
    rec["executor"] = executor
    run_dir = Path(RUNS_DIR) / "wave" / f"{wave.get('wave_id','wave')}-{_dt.datetime.now().strftime('%Y%m%dT%H%M%S')}"
    title = f"Supagram — Solution Architect — WAVE {wave.get('wave_id','?')} (founder)"
    rec["launch"] = _launch_architect(run_dir, f"{executor}-architect-wave", argv, title=title, dry_run=dry_run,
                                      requested_executor="claude-architect-wave")
    return rec


def invoke_manual(topic: str | None = None, *, dry_run: bool = False, model: str = DEFAULT_MODEL,
                  claude_bin: str = "claude") -> dict:
    """Open an interactive Solution Architect window for an ad-hoc founder discussion. Founder-
    initiated and interactive (the founder approves actions in-window), so it is NOT dual-gated the
    way the automatic write-back is."""
    from pathlib import Path
    rec = {"created_utc": _utc(), "mode": "manual", "topic": topic, "model": model, "dry_run": dry_run}
    prompt = manual_boot_prompt(topic)
    rec["prompt"] = prompt
    # Interactive session (no skip-permissions / no plan-lock): the founder drives it.
    executor, rec["model"], argv = _architect_argv(prompt, model, claude_bin)
    rec["executor"] = executor
    run_dir = Path(RUNS_DIR) / "manual" / _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    title = "Supagram — Solution Architect — MANUAL (founder)"
    rec["launch"] = _launch_architect(run_dir, f"{executor}-architect-manual", argv, title=title, dry_run=dry_run,
                                      requested_executor="claude-architect-manual")
    return rec


def _run_dir(thread_n: int, round_rec: dict) -> str:
    sig = f"round{round_rec.get('round')}-{round_rec.get('status')}"
    return os.path.join(RUNS_DIR, f"thread{thread_n}", sig)


def invoke(thread_n: int, *, dry_run: bool = True, model: str = DEFAULT_MODEL,
           claude_bin: str = "claude", live_authorized: bool = False, notification=None) -> dict:
    """Invoke (or, with dry_run, preview) the Solution Architect for one owed thread round.

    Opens a visible, watchable Terminal window (reusing visible_launch), exactly like a worker,
    so the founder can watch the architect reason and write its block live. Returns a record.
    """
    round_rec = owed_round(thread_n)
    rec = {"created_utc": _utc(), "thread": thread_n, "model": model, "dry_run": dry_run}
    if not dry_run and not _bridge._gates_open(live_authorized):
        rec["launch"] = {"refused": "architect dual gate not authorized"}
        return rec
    if round_rec is None:
        rec["skipped"] = (f"Thread {thread_n} does not currently owe the architect "
                          f"(latest round is not AWAITING-ARCHITECT). Nothing to invoke.")
        return rec
    rec["round"] = round_rec
    wave = _wave.active_wave()
    if not dry_run and wave and wave.get('delivery_only'):
        rec['launch'] = {'refused': 'delivery-only envelope grants no actor launch'}
        return rec
    scoped = _bridge.scoped_round(thread_n, wave, round_rec)
    if not dry_run and not scoped:
        rec["launch"] = {"refused": "unverified/stale architect request scope"}
        return rec
    from pathlib import Path
    run_dir = Path(_run_dir(thread_n, round_rec))
    prompt = boot_prompt(thread_n, round_rec)
    if scoped:
        prompt += _delivery.polling_text("architect", thread_n, wave["wave_id"], _delivery.scope_sha(wave, scoped))
    if not dry_run and notification is None:
        notification = _delivery.emit(wave_id=wave['wave_id'], scope=_delivery.scope_sha(wave, scoped),
                thread=thread_n, recipient='architect', number=round_rec['round'], status=_bridge.AWAITING,
                source=Path(_thread_channel_path(thread_n)))
    if notification:
        prompt += f" First read and explicitly acknowledge the exact notification {notification}."
    rec["prompt"] = prompt
    executor, rec["model"], argv = _architect_argv(prompt, model, claude_bin, automatic=True)
    rec["executor"] = executor
    title = f"Supagram — Solution Architect — thread{thread_n} round{round_rec.get('round')}"
    launch = _launch_architect(run_dir, f"{executor}-architect", argv, title=title, dry_run=dry_run,
                               thread_n=thread_n, expected_round=round_rec, notification=notification,
                               requested_executor="claude-architect")
    rec["launch"] = launch
    return rec


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Invoke the Solution Architect to write an ARCHITECT block.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--preview", type=int, metavar="THREAD",
                   help="build + print the boot prompt and the command that WOULD launch; launch nothing")
    g.add_argument("--invoke", type=int, metavar="THREAD",
                   help="live launch (refused here unless the bridge dual-gate is set)")
    g.add_argument("--manual", nargs="?", const="", metavar="TOPIC",
                   help="open an INTERACTIVE architect window for a founder discussion (optional topic); "
                        "not gated — founder-initiated")
    p.add_argument("--preview-only", action="store_true", help="with --manual: build but do not open the window")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"claude model (default {DEFAULT_MODEL})")
    p.add_argument("--i-have-wired-and-authorized-architect-autowrite", dest="auto_flag", action="store_true",
                   help=argparse.SUPPRESS)
    args = p.parse_args(argv)

    if args.manual is not None:
        topic = args.manual or None
        rec = invoke_manual(topic, dry_run=args.preview_only, model=args.model)
        print(json.dumps(rec, indent=2))
        return 0

    if args.preview is not None:
        rec = invoke(args.preview, dry_run=True, model=args.model)
        print(json.dumps(rec, indent=2))
        return 0

    # --invoke: live path is gated exactly like the bridge's --auto. Do not fire live from here
    # unless the config gate is set; the bridge is the single place that owns the live decision.
    if not _bridge._gates_open(args.auto_flag):
        print("LIVE invoke REFUSED: both config authorization and the explicit live flag are required.")
        print("  config auto_writeback=authorized: " + ("set" if _bridge._auto_enabled() else "not set"))
        print("  explicit live flag: " + ("set" if args.auto_flag else "not set"))
        print("  Use `--preview`, or the authorized architect_bridge.py path.")
        return 2
    rec = invoke(args.invoke, dry_run=False, model=args.model, live_authorized=args.auto_flag)
    print(json.dumps(rec, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
