#!/usr/bin/env python3
"""owner_wake.py — model-independent wake relay for EXISTING bound owners (SA + coordinators).

Why: delivery-only daemons queue files, but an idle agent session never reads them. This relay
tells an existing, bound owner session — Codex app, Codex terminal or Claude Code — that it has
unread coordination input, using that runtime's own supported entry point:

  codex-app    Codex app-server control socket `turn/start` (session hosted by the app; idle only)
  codex-queue  `codex queue --thread <session> --message ...` (any Codex session, incl. terminal TUI;
               the session itself picks the message up when ready)
  claude       `claude agents --json` for state. A running Claude session is woken by its own native
               background wait / Stop hook (nothing can be typed into it); a STOPPED session may be
               resumed with `claude --bg --resume` only when config allows it (claude_bg_resume).

Input it wakes for: unread scoped/peer notifications, the latest channel round owed to the owner
(even when its queued notification went stale because the channel file changed), and unconsumed
worker results newer than the wave.

It is communication only. It never launches a new actor, never ACKs/answers for the owner, never
writes channels/trackers/sprints, never retries an event, and grants no scope, review, runtime or
protected-operation authority.

Gate: config/owner_wake.json (enabled, wave_id == active architect-verified wave, expires_utc).
Records: var/owners/wake/<binding_id>/  (one exclusive file per event key + state.json).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import channel_delivery as delivery  # noqa: E402
import owner_sessions as owners  # noqa: E402
import wave as _wave  # noqa: E402

CONFIG = HERE / 'config' / 'owner_wake.json'
WAKE_ROOT = owners.OWNERS / 'wake'
from layout import THREADS as THREADS_DIR
CHANNEL_DIR = THREADS_DIR / 'coordinator-architect'
MAX_PROMPT_BYTES = 1500
ROLES = ('architect', 'coordinator1', 'coordinator2', 'coordinator3')
ADAPTERS = ('auto', 'codex-app', 'codex-queue', 'claude')
NOTICE_ROOT = owners.OWNERS / 'notices'
MAX_NOTICE_CHARS = 400
IDLE_AFTER_SECONDS = 900   # all threads quiet this long, nothing owed, no worker running -> ask the SA once
BUSY_WORKER_STATES = {'ready', 'claimed', 'running', 'acknowledged', 'in_progress'}
OWED_STATUS = {'architect': {'AWAITING-ARCHITECT'}, 'coordinator': {'ALIGNED', 'REDIRECT'}}


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _date(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timezone-aware timestamp required')
    return parsed


# ----------------------------------------------------------------------------- config / envelope

def load_config(path: Path = CONFIG) -> dict:
    cfg = json.loads(path.read_text())
    required = {'schema_version', 'enabled', 'wave_id', 'founder_auth_ref', 'expires_utc', 'socket_link',
                'owners', 'max_wakes_per_owner', 'min_gap_seconds', 'communication_only'}
    if not required <= set(cfg):
        raise ValueError('owner_wake config missing: ' + ', '.join(sorted(required - set(cfg))))
    if cfg['schema_version'] != 1 or cfg['communication_only'] is not True:
        raise ValueError('owner_wake config must be schema 1 and communication_only')
    if not isinstance(cfg['owners'], list) or not cfg['owners'] or any(o not in ROLES for o in cfg['owners']):
        raise ValueError('owners must be a non-empty subset of ' + ', '.join(ROLES))
    if type(cfg['max_wakes_per_owner']) is not int or not 1 <= cfg['max_wakes_per_owner'] <= 96:
        raise ValueError('max_wakes_per_owner must be 1..96')
    if type(cfg['min_gap_seconds']) is not int or not 30 <= cfg['min_gap_seconds'] <= 3600:
        raise ValueError('min_gap_seconds must be 30..3600')
    adapters = cfg.get('adapters', {})
    if not isinstance(adapters, dict) or any(k not in ROLES or v not in ADAPTERS for k, v in adapters.items()):
        raise ValueError('adapters must map owner roles to one of ' + ', '.join(ADAPTERS))
    idle = cfg.get('idle_after_seconds', IDLE_AFTER_SECONDS)
    if type(idle) is not int or not 300 <= idle <= 7200:
        raise ValueError('idle_after_seconds must be 300..7200')
    tail = cfg.get('tail_quiet_seconds', TAIL_QUIET_SECONDS)
    if type(tail) is not int or not 60 <= tail <= 3600:
        raise ValueError('tail_quiet_seconds must be 60..3600')
    if not isinstance(cfg.get('claude_bg_resume', False), bool):
        raise ValueError('claude_bg_resume must be boolean')
    return cfg


def envelope(cfg: dict) -> tuple[dict, dt.datetime]:
    """Return (wave, hard_deadline) or raise; fail closed on any mismatch."""
    if cfg.get('enabled') is not True:
        raise ValueError('owner wake disabled in config')
    current = _wave.active_wave()
    if not current or current.get('wave_id') != cfg['wave_id']:
        raise ValueError('config wave_id is not the active wave')
    if current.get('verified_by_architect') is not True:
        raise ValueError('active wave not verified by architect')
    deadline = min(_date(cfg['expires_utc']), _date(current['operating_deadline_utc']))
    if now() >= deadline:
        raise ValueError('wake window expired; no automatic renewal')
    return current, deadline


def socket_target(cfg: dict) -> str:
    link = Path(os.path.expanduser(cfg['socket_link']))
    target = Path(os.path.realpath(link))
    if not target.is_absolute() or '..' in target.parts:
        raise ValueError('invalid control socket target')
    return str(target)


def binding_for(role: str) -> dict | None:
    if role == 'architect':
        return owners.binding('architect')
    return owners.binding('coordinator', int(role[-1]))


def rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(THREADS_DIR))
    except ValueError:
        return str(path)


# ----------------------------------------------------------------------------- input detection
# An input is (key, label). Keys dedupe forever per binding; labels go into the prompt.

def _file_input(path: Path) -> tuple[str, str]:
    path = Path(path)
    return hashlib.sha256((str(path) + ':' + delivery.sha(path)).encode()).hexdigest(), rel(path)


def latest_round(thread: int) -> dict | None:
    """Latest round; an unmarked one inherits the wave of the nearest earlier marked round.

    Coordinators sometimes append a round without the `wave:` / `scope:` tokens. The delivery
    watchers then (correctly) refuse to queue it, and without this the relay stayed silent too,
    so an answered round sat unread. The inherited wave is flagged so the prompt asks for repair.
    """
    import architect_bridge as bridge
    path = CHANNEL_DIR / f'thread{thread}.md'
    latest = bridge._latest_round(str(path))
    if not latest or latest.get('wave_id'):
        return latest
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        return latest
    prior = None
    for m in bridge._ROUND_RE.finditer(text):
        if int(m.group(1)) >= latest['round']:
            continue
        end = text.find('-->', m.end())
        marker = re.search(r'(?<!\S)wave:([A-Za-z0-9_-]+)(?=\s|$)', text[m.start():end]) if end != -1 else None
        if marker and (prior is None or int(m.group(1)) > prior[0]):
            prior = (int(m.group(1)), marker.group(1))
    if prior:
        latest = dict(latest, wave_id=prior[1], wave_inferred=True)
    return latest


def _round_consumed(thread: int, rnd: int, recipient: str) -> bool:
    folder = delivery.MAILBOX_ROOT / recipient / f'thread{thread}'
    for path in folder.glob('*.json'):
        if path.name.endswith('.read.json'):
            continue
        try:
            raw = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if int(raw.get('round', -1)) == rnd and path.with_suffix('.read.json').exists():
            return True
    return False


def channel_inputs(role: str, current: dict) -> list[tuple[str, str]]:
    """Latest channel round still owed to this owner in the current wave.

    Independent of the queued notification's whole-file hash: any later append to the channel
    makes that notification 'stale', which previously hid owed rounds (notably from the SA).
    """
    kind = 'architect' if role == 'architect' else 'coordinator'
    threads = (1, 2, 3) if kind == 'architect' else (int(role[-1]),)
    found = []
    for n in threads:
        latest = latest_round(n)
        if not latest or latest.get('status') not in OWED_STATUS[kind]:
            continue
        if latest.get('wave_id') != current['wave_id']:
            continue  # rounds from earlier waves never wake anyone
        if kind == 'coordinator' and _round_consumed(n, latest['round'], 'coordinator'):
            continue
        key = hashlib.sha256(f"channel:{current['wave_id']}:{n}:{latest['round']}:{latest['status']}".encode()).hexdigest()
        label = f"coordinator-architect/thread{n}.md Round {latest['round']} {latest['status']}"
        if latest.get('wave_inferred'):
            label += ' (header lacks wave:/scope: tokens, so watchers skipped it; owner adds them)'
        found.append((key, label))
    return found


def coordinator_inputs(record: dict, current: dict) -> list[tuple[str, str]]:
    import coordinator_continuation as cc
    inputs = []
    try:
        inputs += [_file_input(Path(e['path'])) for e in cc.pending_events(record) if e.get('path')]
    except (OSError, ValueError, KeyError, TypeError):
        pass  # a stale queued notification must not hide the channel round or worker results
    created = _date(current['created_utc'])
    folder = THREADS_DIR / f"thread{record['thread']}"
    for state_path in sorted(folder.glob('agent*/state.json')):
        try:
            state = json.loads(state_path.read_text())
            location = state.get('result_location')
            if not location:
                continue
            result = delivery.safe_path(state_path.parent, state_path.parent / location)
            if not result.is_file() or (result.parent / 'coordinator-consumption.json').exists():
                continue
            if dt.datetime.fromtimestamp(result.stat().st_mtime, dt.timezone.utc) < created:
                continue  # historical unconsumed run; not this wave's work
            inputs.append(_file_input(result))
        except (OSError, ValueError, TypeError):
            continue
    return inputs


def post_notice(roles: list[str], text: str, wave_id: str) -> Path:
    """Founder notice for named owners; delivered by the relay with all its normal guards."""
    text = ' '.join(text.split())
    if not text or len(text) > MAX_NOTICE_CHARS:
        raise ValueError(f'notice must be 1..{MAX_NOTICE_CHARS} characters')
    if not roles or any(r not in ROLES for r in roles):
        raise ValueError(f'roles must be from {ROLES}')
    body = {'schema_version': 1, 'wave_id': wave_id, 'roles': sorted(set(roles)), 'text': text, 'utc': now().isoformat()}
    nid = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    path = NOTICE_ROOT / f'{nid}.json'
    _write_json(path, dict(body, id=nid), exclusive=True)
    return path


def notice_inputs(role: str, current: dict) -> list[tuple[str, str]]:
    found = []
    for path in sorted(NOTICE_ROOT.glob('*.json')):
        try:
            raw = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if raw.get('wave_id') != current['wave_id'] or role not in raw.get('roles', []):
            continue
        key = hashlib.sha256(f"notice:{raw['id']}:{role}".encode()).hexdigest()
        found.append((key, f"FOUNDER NOTICE: {raw['text']}"))
    return found


def _newest_mtime(paths) -> float:
    newest = 0.0
    for path in paths:
        try:
            newest = max(newest, path.stat().st_mtime)
        except OSError:
            continue
    return newest


def activity_paths() -> list[Path]:
    """Files whose change means some thread, worker or message is still moving."""
    paths = [CHANNEL_DIR / f'thread{n}.md' for n in (1, 2, 3)]
    for n in (1, 2, 3):
        folder = THREADS_DIR / f'thread{n}'
        paths += [folder / 'sprint.json'] + list((folder / 'instructions').glob('*.md'))
        for agent in folder.glob('agent*'):
            paths += [agent / 'state.json', agent / 'task.md']
            runs = sorted((agent / 'runs').glob('[0-9]*'))
            if runs:
                paths += [runs[-1]] + list(runs[-1].glob('*'))
    for recipient in ('coordinator', 'architect', 'peer'):
        for box in (delivery.MAILBOX_ROOT / recipient).glob('thread*'):
            paths += list(box.glob('*.json'))
    return paths


def busy_workers() -> list[str]:
    busy = []
    for state_path in THREADS_DIR.glob('thread[123]/agent*/state.json'):
        try:
            status = json.loads(state_path.read_text()).get('status')
        except (OSError, ValueError):
            continue
        if status in BUSY_WORKER_STATES:
            busy.append(f'{state_path.parent.name}:{status}')
    return busy


def drained_input(current: dict, idle_after: int = IDLE_AFTER_SECONDS) -> list[tuple[str, str]]:
    """All threads drained: nothing owed to anyone, no worker busy, no change for `idle_after` seconds.

    Wakes the SA once per quiet period (the key carries the last-activity time), so the SA either
    assigns next work or names the exact founder gates. It never re-fires while nothing changes.
    """
    rounds = []
    for n in (1, 2, 3):
        latest = latest_round(n)
        if latest and latest.get('status') == 'AWAITING-ARCHITECT':
            return []  # the normal owed-round wake covers this
        rounds.append(f"T{n} R{latest['round']} {latest['status']}" if latest else f'T{n} none')
    if busy_workers():
        return []
    for role in ('coordinator1', 'coordinator2', 'coordinator3'):
        record = binding_for(role)
        if record and [k for k, _ in owner_inputs(role, record, current)
                       if not (WAKE_ROOT / record['binding_id'] / (k + '.json')).exists()]:
            return []  # a coordinator still has unread input; let it act first
    last = _newest_mtime(activity_paths())
    quiet = now().timestamp() - last
    if not last or quiet < idle_after:
        return []
    key = hashlib.sha256(f"drained:{current['wave_id']}:{int(last)}".encode()).hexdigest()
    return [(key, f"ALL THREADS DRAINED (no change for {int(quiet // 60)} min; {', '.join(rounds)}; no worker running, "
                  "nothing owed). For each idle thread either open its next tagged assignment round, or record "
                  "HOLD/ESCALATE naming the exact founder gate; end your reply with one consolidated founder-gate list")]


TAIL_QUIET_SECONDS = 300
_VERDICT_RE = re.compile(r'<!-- verdict:([A-Z-]+) by:solution-architect')
_BOOKKEEPING_RE = re.compile(r'^#{2,4} .*\b(ACK|launch)\b', re.IGNORECASE)


def tail_after_verdict_input(current: dict, quiet_after: int = TAIL_QUIET_SECONDS,
                             busy: list[str] | None = None) -> list[tuple[str, str]]:
    """Coordinator wrote under an already-answered round instead of opening a new one.

    On 24Nov T1 appended its D135 intake ("Please reconcile canonical status") under the ALIGNED
    Round 92. Nothing was owed to the SA, so only the 15-minute all-threads-drained wake could
    reach it, and any activity on another thread kept postponing that. This wakes the SA once per
    distinct tail, after that thread's own worker is idle and its channel is quiet `quiet_after` s.
    """
    import architect_bridge as bridge
    busy = busy_workers() if busy is None else busy
    out = []
    for n in (1, 2, 3):
        latest = latest_round(n)
        if not latest or latest.get('status') == 'AWAITING-ARCHITECT':
            continue
        if latest.get('wave_id') != current['wave_id']:
            continue
        if any(b.startswith(f'agent{n}-') for b in busy):
            continue
        path = CHANNEL_DIR / f'thread{n}.md'
        try:
            text = path.read_text(encoding='utf-8')
            quiet = now().timestamp() - path.stat().st_mtime
        except OSError:
            continue
        headers = list(bridge._ROUND_RE.finditer(text))
        verdicts = list(_VERDICT_RE.finditer(text))
        if not headers or not verdicts or verdicts[-1].start() < headers[-1].start():
            continue
        end = text.find('-->', verdicts[-1].end())
        tail = text[end + 3:].strip() if end != -1 else ''
        # Read-ACKs and launch receipts are bookkeeping, not questions for the SA.
        sections = [sec.strip() for sec in re.split(r'(?m)^(?=#{2,4} )', tail) if sec.strip()]
        asks = [sec for sec in sections if not _BOOKKEEPING_RE.search(sec.splitlines()[0])]
        if not asks or quiet < quiet_after:
            continue
        heading = asks[-1].splitlines()[0].strip()[:80]
        key = hashlib.sha256(f"tail:{current['wave_id']}:{n}:{tail}".encode()).hexdigest()
        out.append((key, f"coordinator-architect/thread{n}.md Round {latest['round']} {latest['status']}: coordinator "
                         f"appended after your verdict without opening a new round (last: '{heading}'); act on any "
                         "request in it and remind the coordinator to open a tagged AWAITING-ARCHITECT round"))
    return out


def owner_inputs(role: str, record: dict, current: dict) -> list[tuple[str, str]]:
    inputs = notice_inputs(role, current) + channel_inputs(role, current)
    if role != 'architect':
        inputs += coordinator_inputs(record, current)
    seen, unique = set(), []
    for key, label in inputs:
        if key not in seen:
            seen.add(key)
            unique.append((key, label))
    return unique


def build_prompt(role: str, record: dict, wave_id: str, labels: list[str]) -> str:
    if role == 'architect':
        who, action = 'Solution Architect', ('read each owed round and give your verdict (ALIGNED/REDIRECT/HOLD/'
                                              'ESCALATE) per solution-architect.md; resolve the stuck/conflict point')
    else:
        who, action = (f"Thread {record['thread']} coordinator",
                       ('per coordinator-definition C15 read and ACK it yourself, answer/consume, then continue your armed sprint; '
                        'implementation still goes to your workers via the per-task state machine '
                        '(task.md, then supervisor.py --assign), never in the coordinator session'))
    head = (f"Wake relay (founder-authorized, communication only) for your EXISTING {who} session, "
            f"binding {record['binding_id'][:8]}, wave {wave_id}. Unread input under coordination-threads/: ")
    tail = (f'. Please {action}. STRICT: every new round header must carry wave:{wave_id} scope:<thread scope sha>; '
            'get the exact line from `python3 automation/automode.py header`. '
            f'If you need a founder decision, run `python3 automation/automode.py ask --from {role} --question ...` '
            'before you stop; never stop silently. '
            'End each round and reply with a plain-language **Summary:** line (what, why, next). '
            'C17 OUTCOME FIRST: deliver the next goal row; defer refinement to deferred-to-hardening.md; no extra reviews, rechecks, probes, migrations or docs. '
            'This wake grants no scope, review, runtime or gate authority; do not reply to the relay.')
    shown = list(labels)
    while True:
        more = f' (+{len(labels) - len(shown)} more)' if len(shown) < len(labels) else ''
        prompt = head + '; '.join(shown) + more + tail
        if len(prompt.encode()) <= MAX_PROMPT_BYTES or len(shown) <= 1:
            break
        shown.pop()
    if len(prompt.encode()) > MAX_PROMPT_BYTES:
        raise ValueError('wake prompt exceeds bound')
    return prompt


# ----------------------------------------------------------------------------- adapters
# Each adapter: precheck(ctx) -> None to proceed, or a result dict to stop (no reservation);
# deliver(ctx, prompt) -> dict(state=..., [turn_id]) after inputs are reserved.

def _codex_home(record: dict, cfg: dict) -> str:
    if cfg.get('codex_home'):
        return os.path.expanduser(cfg['codex_home'])
    try:  # inherit the owner's own CODEX_HOME so the message reaches its own session store
        env = subprocess.run(['ps', '-E', '-o', 'command=', '-p', str(record['pid'])],
                             capture_output=True, text=True, timeout=5).stdout
        for token in env.split():
            if token.startswith('CODEX_HOME='):
                return token.split('=', 1)[1]
    except (OSError, subprocess.SubprocessError, KeyError):
        pass
    return os.path.expanduser('~/.codex')


class CodexApp:
    name = 'codex-app'

    def __init__(self, record, cfg, endpoint, control_cls=None):
        if control_cls is None:
            import architect_invoke
            control_cls = architect_invoke.NativeControl
        self.record, self.client = record, control_cls(endpoint, record, 5)  # peer PID/fingerprint == binding

    def precheck(self):
        c = self.client
        c.rpc('initialize', {'clientInfo': {'name': 'aosdf_owner_wake_relay', 'version': '2.0'}}, 1)
        c.send({'method': 'initialized'})
        thread = c.rpc('thread/read', {'threadId': self.record['session_id'], 'includeTurns': False}, 2)['thread']
        if thread.get('id') != self.record['session_id'] or Path(thread.get('cwd', '')).resolve() != owners.REPO.resolve():
            return {'state': 'skip-thread-identity-mismatch'}
        kind = thread.get('status', {}).get('type')
        if kind == 'active':
            return {'state': 'owner-busy'}
        if kind != 'idle':  # e.g. systemError (a turn ended by a provider error): report it, never call it busy
            return {'state': 'owner-error', 'status': str(kind)[:40]}
        return None

    def deliver(self, prompt):
        result = self.client.rpc('turn/start', {'threadId': self.record['session_id'],
                                                'input': [{'type': 'text', 'text': prompt}]}, 3)
        return {'state': 'submitted', 'turn_id': result['turn']['id']}

    def close(self):
        self.client.close()


class CodexQueue:
    name = 'codex-queue'

    def __init__(self, record, cfg, runner=subprocess.run):
        self.record, self.cfg, self.run = record, cfg, runner
        self.home = _codex_home(record, cfg)
        self.bin = cfg.get('codex_bin') or shutil.which('codex') or 'codex'

    def precheck(self):
        db = Path(self.home) / 'queue_1.sqlite'
        if db.exists():
            try:
                con = sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=2)
                try:
                    waiting = con.execute('select count(*) from queued_items where thread_id = ?',
                                          (self.record['session_id'],)).fetchone()[0]
                finally:
                    con.close()
                if waiting:
                    return {'state': 'already-queued', 'queued_items': waiting}
            except sqlite3.Error:
                pass  # unreadable queue store: let `codex queue` itself decide
        return None

    def deliver(self, prompt):
        env = dict(os.environ, CODEX_HOME=self.home)
        out = self.run([self.bin, 'queue', '--thread', self.record['session_id'], '--message', prompt],
                       capture_output=True, text=True, timeout=30, env=env, cwd=str(owners.REPO))
        if out.returncode != 0:
            return {'state': 'queue-failed', 'error': (out.stderr or out.stdout)[-200:]}
        return {'state': 'queued', 'codex_home': self.home}

    def close(self):
        pass


class Claude:
    name = 'claude'

    def __init__(self, record, cfg, runner=subprocess.run):
        self.record, self.cfg, self.run = record, cfg, runner
        self.bin = cfg.get('claude_bin') or shutil.which('claude') or 'claude'
        self.session = None

    def precheck(self):
        out = self.run([self.bin, 'agents', '--json'], capture_output=True, text=True, timeout=20)
        if out.returncode != 0:
            return {'state': 'claude-status-unavailable', 'error': (out.stderr or out.stdout)[-200:]}
        sessions = json.loads(out.stdout or '[]')
        self.session = next((s for s in sessions if s.get('sessionId') == self.record['session_id']), None)
        if self.session:
            if self.session.get('status') == 'busy':
                return {'state': 'owner-busy'}
            # Nothing can be typed into a running interactive Claude session from outside; its own
            # native background waiter / Stop hook (coordinator_continuation.py) is the wake path.
            return {'state': 'claude-running-use-native-wait'}
        if not self.cfg.get('claude_bg_resume'):
            return {'state': 'claude-stopped-resume-disabled'}
        return None

    def deliver(self, prompt):
        out = self.run([self.bin, '--bg', '--resume', self.record['session_id'], prompt],
                       capture_output=True, text=True, timeout=60, cwd=str(owners.REPO))
        if out.returncode != 0:
            return {'state': 'claude-resume-failed', 'error': (out.stderr or out.stdout)[-200:]}
        return {'state': 'resumed-background', 'detail': out.stdout.strip()[-200:]}

    def close(self):
        pass


def make_adapter(role: str, record: dict, cfg: dict, endpoint: str, *, control_cls=None, runner=subprocess.run):
    forced = cfg.get('adapters', {}).get(role, 'auto')
    executor = record.get('executor')
    if forced == 'claude' or (forced == 'auto' and executor == 'claude'):
        return Claude(record, cfg, runner)
    if forced == 'codex-queue':
        return CodexQueue(record, cfg, runner)
    if forced == 'codex-app':
        return CodexApp(record, cfg, endpoint, control_cls)
    if executor == 'codex':
        try:
            return CodexApp(record, cfg, endpoint, control_cls)
        except (OSError, ValueError, ConnectionError, TimeoutError):
            # Not hosted by the app-server (e.g. terminal TUI) or socket unavailable.
            return CodexQueue(record, cfg, runner)
    raise ValueError(f'unsupported executor {executor!r}')


# ----------------------------------------------------------------------------- wake

def _state_path(record: dict) -> Path:
    return delivery.safe_path(WAKE_ROOT, WAKE_ROOT / record['binding_id'] / 'state.json')


def _read_state(record: dict) -> dict:
    path = _state_path(record)
    return json.loads(path.read_text()) if path.exists() else {'submissions': []}


def _write_json(path: Path, value: dict, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = (json.dumps(value, indent=2) + '\n').encode()
    if exclusive:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
        return
    tmp = path.with_suffix('.tmp')
    tmp.write_bytes(data)
    os.replace(tmp, path)


def wake_one(role: str, cfg: dict, current: dict, endpoint: str, *, dry_run: bool,
             control_cls=None, runner=subprocess.run, inputs_fn=None) -> dict:
    record = binding_for(role)
    if not record or record.get('state') != 'bound':
        return {'role': role, 'state': 'skip-no-bound-owner'}
    inputs = (inputs_fn or owner_inputs)(role, record, current)
    if role == 'architect' and inputs_fn is None:
        inputs = (inputs + tail_after_verdict_input(current, cfg.get('tail_quiet_seconds', TAIL_QUIET_SECONDS))
                  + drained_input(current, cfg.get('idle_after_seconds', IDLE_AFTER_SECONDS)))
    folder = WAKE_ROOT / record['binding_id']
    fresh = [(k, label) for k, label in inputs if not (folder / (k + '.json')).exists()]
    if not fresh:
        return {'role': role, 'state': 'no-new-input'}
    state = _read_state(record)
    subs = [s for s in state['submissions'] if s.get('wave_id') == current['wave_id']]
    if len(subs) >= cfg['max_wakes_per_owner']:
        return {'role': role, 'state': 'budget-exhausted', 'pending': [label for _, label in fresh]}
    if subs and (now() - _date(subs[-1]['utc'])).total_seconds() < cfg['min_gap_seconds']:
        return {'role': role, 'state': 'min-gap-wait', 'pending': len(fresh)}
    prompt = build_prompt(role, record, current['wave_id'], [label for _, label in fresh])
    if dry_run:
        return {'role': role, 'state': 'would-wake', 'events': [label for _, label in fresh],
                'prompt_bytes': len(prompt.encode())}
    adapter = make_adapter(role, record, cfg, endpoint, control_cls=control_cls, runner=runner)
    try:
        stop = adapter.precheck()
        if stop:
            return {'role': role, 'adapter': adapter.name, 'pending': len(fresh), **stop}
        if binding_for(role) != record:
            return {'role': role, 'state': 'skip-binding-changed'}
        # Reserve every input key BEFORE the single write: a lost reply must never cause a resend.
        reserved = []
        for key, label in fresh:
            try:
                _write_json(folder / (key + '.json'), {'schema_version': 1, 'event': label, 'utc': now().isoformat(),
                                                       'wave_id': current['wave_id'], 'state': 'reserved'}, exclusive=True)
                reserved.append(label)
            except FileExistsError:
                continue
        if not reserved:
            return {'role': role, 'state': 'no-new-input'}
        submission = {'utc': now().isoformat(), 'wave_id': current['wave_id'], 'adapter': adapter.name,
                      'events': reserved, 'turn_id': None, 'state': 'submitting', 'automatic_retry': False}
        state['submissions'].append(submission)
        _write_json(_state_path(record), state)
        try:
            submission.update(adapter.deliver(prompt))
        except (OSError, ValueError, KeyError, TypeError, ConnectionError, subprocess.SubprocessError) as error:
            submission.update(state='submit-uncertain', error=str(error)[:200])
        _write_json(_state_path(record), state)
        return {'role': role, **submission}
    finally:
        adapter.close()


def tick(*, dry_run: bool = False, control_cls=None, runner=subprocess.run, config_path: Path = CONFIG,
         only: str | None = None, inputs_fn=None) -> dict:
    try:
        cfg = load_config(config_path)
        current, deadline = envelope(cfg)
        endpoint = socket_target(cfg)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {'state': 'inactive', 'reason': str(error)}
    results = []
    for role in cfg['owners']:
        if only and role != only:
            continue
        try:
            with delivery.dispatch_guard():
                results.append(wake_one(role, cfg, current, endpoint, dry_run=dry_run, control_cls=control_cls,
                                        runner=runner, inputs_fn=inputs_fn))
        except BlockingIOError:
            results.append({'role': role, 'state': 'skip-dispatch-busy'})
        except (OSError, ValueError, KeyError, TypeError, ConnectionError, TimeoutError,
                subprocess.SubprocessError) as error:
            results.append({'role': role, 'state': 'error', 'error': str(error)[:200]})
    return {'state': 'active', 'deadline_utc': deadline.isoformat(), 'dry_run': dry_run, 'owners': results}


def status() -> dict:
    try:
        cfg = load_config()
    except (OSError, ValueError) as error:
        return {'config': str(error)}
    out = {'enabled': cfg['enabled'], 'wave_id': cfg['wave_id'], 'expires_utc': cfg['expires_utc'], 'owners': {}}
    for role in cfg['owners']:
        rec = binding_for(role)
        out['owners'][role] = ({'executor': rec.get('executor'), 'adapter': cfg.get('adapters', {}).get(role, 'auto'),
                                'recent': _read_state(rec)['submissions'][-3:],
                                'used': sum(1 for x in _read_state(rec)['submissions'] if x.get('wave_id') == cfg['wave_id']),
                                'budget': cfg['max_wakes_per_owner']} if rec else 'unbound')
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('tick', help='one pass')
    t.add_argument('--dry-run', action='store_true')
    t.add_argument('--owner', choices=ROLES)
    r = sub.add_parser('run', help='loop until the wake window ends')
    r.add_argument('--dry-run', action='store_true')
    r.add_argument('--interval', type=int, default=30)
    sub.add_parser('status', help='show config and per-owner submissions')
    a = p.parse_args()
    if a.cmd == 'tick':
        print(json.dumps(tick(dry_run=a.dry_run, only=a.owner), indent=2))
        return 0
    if a.cmd == 'status':
        print(json.dumps(status(), indent=2))
        return 0
    import daemon as _d
    interval = max(15, min(a.interval, 600))
    while True:
        result = tick(dry_run=a.dry_run)
        if not a.dry_run and result.get('state') == 'active':
            try:  # founder decisions: record ESCALATE/founder HOLD rounds, remind hourly; never blocks the relay
                import founder_inbox
                live_cfg = load_config()
                current_wave = envelope(live_cfg)[0]
                founder_inbox.reconcile(current_wave, live_cfg)
                founder_inbox.scan_channels(current_wave)
                founder_inbox.budget_alerts(live_cfg, current_wave)
                founder_inbox.owner_health(result.get('owners', []), current_wave)
                founder_inbox.remind_open()
            except (OSError, ValueError, KeyError, TypeError) as error:
                print(json.dumps({'founder_inbox_error': str(error)[:200]}))
        woke = [o['role'] for o in result.get('owners', [])
                if o.get('state') in ('submitted', 'queued', 'resumed-background', 'would-wake')]
        _d.write_status('owner_wake', mode='dry-run' if a.dry_run else 'live',
                        summary=(result.get('reason') or f"woke {','.join(woke) or 'none'}" + ''.join(
                            f"; {o['role']} {o['state']}" for o in result.get('owners', [])
                            if o.get('state') in ('owner-busy', 'owner-error', 'min-gap-wait', 'budget-exhausted')))[:160])
        if result['state'] == 'inactive' and 'expired' in result.get('reason', ''):
            print(json.dumps(result))
            return 0
        time.sleep(interval)


if __name__ == '__main__':
    sys.exit(main())
