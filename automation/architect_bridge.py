#!/usr/bin/env python3
"""
architect_bridge.py — Coordinator <-> Architect channel bridge (Stage-1 safe).

Watches coordination-threads/coordinator-architect/thread<n>.md for alignment rounds and,
when a round is AWAITING-ARCHITECT, surfaces the founder-relay ping:

    Discuss Thread<n>

That is the entire job of the DEFAULT (notify) mode: detect that a coordinator owes the
architect a response, and print the one-word relay the founder carries to the architect
conversation. It writes nothing into the channel files. Its only writes are its own dedup
cursors (var/architect_bridge.cursor.json for notify pings; var/architect_bridge.auto.cursor.json
for the --auto path -- kept separate so a ping never deduplicates a later live launch, and a
preview never consumes a round), mirroring monitor.py.

The AUTO write-back path (the Solution Architect writing the ARCHITECT block itself, so a
continuously-running coordinator proceeds with no founder relay) is now WIRED to
`architect_invoke.py` but stays HARD-DISABLED behind a dual gate -- a config flag AND an
explicit authorize flag -- exactly like supervisor.py --dispatch. Wiring the invocation did
NOT enable that path: without the config gate, --auto only PREVIEWS (launches nothing), and
--preview-invoke always previews. The live launch opens a visible, watchable Terminal window
(like a worker), never a hidden process.

Usage:
    python3 architect_bridge.py                 # one-shot scan: table of each thread's latest round + status
    python3 architect_bridge.py --notify        # one-shot: emit `Discuss Thread<n>` for each AWAITING round (dedup via cursor)
    python3 architect_bridge.py --watch          # continuous notify loop (default interval 30s), Ctrl-C to stop
    python3 architect_bridge.py --watch --interval 60
    python3 architect_bridge.py --reset          # ignore prior cursor (re-emit everything owed)
    python3 architect_bridge.py --json           # raw per-thread state (for a dashboard)
    python3 architect_bridge.py --preview-invoke <n>  # show the exact architect launch for thread n; launch nothing
    python3 architect_bridge.py --auto           # invoke the architect for every owed round -- LIVE only if dual-gated, else previews
    python3 architect_bridge.py --watch --auto   # continuous: detect AWAITING-ARCHITECT and invoke (live only if gated)

No secrets are read or written. This is a channel bridge, not an authorization path; it
grants nothing. Status authority remains execution_plan.md; the Solution Architect remains sole canonical writer.
"""

import argparse
import datetime as _dt
import json
import os
import re
import sys
import time
from pathlib import Path
import channel_delivery as _delivery
import wave as _wave

HERE = os.path.dirname(os.path.abspath(__file__))
CHANNEL_DIR = os.path.normpath(os.path.join(HERE, "coordination-threads", "coordinator-architect"))
VAR_DIR = os.path.join(HERE, "var")
CURSOR = os.path.join(VAR_DIR, "architect_bridge.cursor.json")
# The --auto write-back path keeps its OWN dedup cursor, separate from the notify
# (Easy-Mode ping) cursor above, so a `Discuss Thread<n>` ping never makes a later
# live --auto think the round is already handled, and vice versa.
AUTO_CURSOR = os.path.join(VAR_DIR, "architect_bridge.auto.cursor.json")

# A round machine-comment line, e.g.:
#   <!-- round:1 checkpoint:post status:AWAITING-ARCHITECT opened:2026-10-27T05:10Z -->
_ROUND_RE = re.compile(r"<!--\s*round:(\d+)\s+checkpoint:([A-Za-z0-9_-]+)\s+status:([A-Za-z\-]+)")

AWAITING = "AWAITING-ARCHITECT"
ARCHITECT_VERDICTS = {"ALIGNED", "REDIRECT", "HOLD", "ESCALATE"}
GREEN = "GREEN"


def _now():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _thread_files():
    if not os.path.isdir(CHANNEL_DIR):
        return []
    out = []
    for name in sorted(os.listdir(CHANNEL_DIR)):
        m = re.fullmatch(r"thread(\d+)\.md", name)
        if m:
            out.append((int(m.group(1)), os.path.join(CHANNEL_DIR, name)))
    return out


def _latest_round(path):
    """Return the highest-numbered round's (round, checkpoint, status) or None."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    best = None
    for m in _ROUND_RE.finditer(text):
        rnd = int(m.group(1))
        rec = {"round": rnd, "checkpoint": m.group(2), "status": m.group(3)}
        end = text.find("-->", m.end())
        if end != -1:
            bootstrap = re.search(r"\bbootstrap:wave:([A-Za-z0-9_-]+)\b", text[m.start():end])
            if bootstrap:
                rec["bootstrap_wave"] = bootstrap.group(1)
            wave_marker = re.search(r"(?<!\S)wave:([A-Za-z0-9_-]+)(?=\s|$)", text[m.start():end])
            scope_marker = re.search(r"(?<!\S)scope:([0-9a-f]{64})(?=\s|$)", text[m.start():end])
            if wave_marker:
                rec["wave_id"] = wave_marker.group(1)
            if scope_marker:
                rec["scope_sha256"] = scope_marker.group(1)
        if best is None or rnd > best["round"]:
            best = rec
    return best


def scan():
    rows = []
    for n, path in _thread_files():
        latest = _latest_round(path)
        rows.append({"thread": n, "file": os.path.basename(path), "latest": latest})
    return rows


def _load_cursor(path=CURSOR):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _save_cursor(data, path=CURSOR):
    os.makedirs(VAR_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, path)


def _owed(latest):
    """A round owes the architect a response iff its latest round is AWAITING-ARCHITECT."""
    return bool(latest and latest.get("status") == AWAITING)


def scoped_round(thread_n, wave, latest):
    """Legacy opening bootstrap is bound by its wave; later rounds need exact scope."""
    sprint = _wave.verified_thread_sprint(wave, thread_n)
    if not sprint or not latest:
        return None
    if latest.get("checkpoint") not in {"sprint", "sprint-completion", "conflict", "assignment"}:
        return None
    number = latest.get("round", 0)
    if number < sprint["opening_round"]:
        return None
    expected = _delivery.scope_sha(wave, sprint)
    if number == sprint["opening_round"]:
        if latest.get("bootstrap_wave") != wave["wave_id"]:
            return None
        if latest.get("wave_id", wave["wave_id"]) != wave["wave_id"]:
            return None
        if latest.get("scope_sha256", expected) != expected:
            return None
    elif latest.get("wave_id") != wave["wave_id"] or latest.get("scope_sha256") != expected:
        return None
    return sprint


def print_table(rows):
    print(f"=== Coordinator <-> Architect channel  ({_now()}) ===")
    print(f"channel: {CHANNEL_DIR}")
    if not rows:
        print("  (no thread<n>.md files yet)")
        return
    owed = []
    for r in rows:
        latest = r["latest"]
        if not latest:
            desc = "no rounds / placeholder"
        else:
            desc = f"round {latest['round']} [{latest['checkpoint']}] -> {latest['status']}"
        flag = ""
        if _owed(latest):
            flag = "   <-- OWES ARCHITECT"
            owed.append(r["thread"])
        print(f"  Thread {r['thread']}: {desc}{flag}")
    print("-" * 60)
    if owed:
        print("Founder relay — type each of these to the architect conversation:")
        for n in owed:
            print(f"    Discuss Thread{n}")
    else:
        print("Nothing owed to the architect. All rounds aligned/green or parked.")


def notify(reset=False):
    """Emit `Discuss Thread<n>` for every thread that owes the architect, deduped via cursor."""
    rows = scan()
    cursor = {} if reset else _load_cursor()
    emitted = []
    for r in rows:
        latest = r["latest"]
        if not _owed(latest):
            continue
        key = str(r["thread"])
        sig = f"{latest['round']}:{latest['status']}"
        if cursor.get(key) == sig:
            continue  # already pinged for this exact round/status
        emitted.append(r["thread"])
        cursor[key] = sig
    for n in emitted:
        print(f"Discuss Thread{n}")
        _macos_banner(f"Discuss Thread{n}")
    if not reset:
        # keep cursor entries only for threads that still exist
        live = {str(r["thread"]) for r in rows}
        cursor = {k: v for k, v in cursor.items() if k in live}
    _save_cursor(cursor)
    return emitted


def _macos_banner(msg):
    """Best-effort desktop notification on macOS; silent no-op elsewhere/on failure."""
    if sys.platform != "darwin":
        return
    try:
        import subprocess
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{msg}" with title "Coordinator channel"'],
            check=False, capture_output=True, timeout=5,
        )
    except Exception:
        pass


def _heartbeat(path_mode, summary, *, live=False):
    """Best-effort daemon heartbeat for the supervisor/dashboard; never fatal if daemon.py absent.

    Stamps this daemon's OWN effective path (`path_mode`) and whether it is actually launching
    the architect live (`live`). The global runtime mode is computed centrally from these flags
    (daemon.runtime_mode), so we never stamp a global mode word here that could go stale/misleading.
    """
    try:
        import daemon as _d
        _d.write_status("architect_bridge", state="running",
                        path_mode=path_mode, live=bool(live), summary=summary)
    except Exception:
        pass


def watch(interval, reset=False):
    print(f"[architect_bridge] watch mode, interval={interval}s. Ctrl-C to stop.")
    first = reset
    try:
        while True:
            got = notify(reset=first)
            first = False
            if not got:
                # quiet tick; a timestamp line keeps the watcher legible
                print(f"[{_now()}] nothing owed.", flush=True)
                _heartbeat("notify", "no thread owes the architect", live=False)
            else:
                line = ', '.join('Thread%d' % n for n in got)
                print(f"[{_now()}] pinged: {line}", flush=True)
                _heartbeat("notify", f"pinged: {line}", live=False)
            time.sleep(max(5, interval))
    except KeyboardInterrupt:
        print("\n[architect_bridge] stopped.")


def watch_auto(interval, flag_set, *, model="opus", reset=False):
    """Continuous detect-and-invoke loop: the software-factory path. Each tick scans the channel
    and, for any newly-owed round, invokes the Solution Architect (LIVE only if dual-gated, else a
    preview). This is the auto counterpart of watch(); it replaces the founder relay on the happy
    path and leaves only ESCALATE for the human."""
    mode = "LIVE" if _gates_open(flag_set) else "PREVIEW (dual-gate not set)"
    print(f"[architect_bridge] watch+auto mode [{mode}], interval={interval}s. Ctrl-C to stop.")
    first = reset
    try:
        while True:
            res = auto_invoke_owed(flag_set, model=model, reset=first)
            first = False
            n = len([r for r in res if not r.get("skipped")])
            live = _gates_open(flag_set)
            _heartbeat("auto-live" if live else "auto-preview",
                       f"{n} architect launch(es) this tick" if n else "no owed round this tick",
                       live=live)
            time.sleep(max(5, interval))
    except KeyboardInterrupt:
        print("\n[architect_bridge] stopped.")


# --------------------------------------------------------------------------- #
#  AUTO write-back path -- HARD-DISABLED (dual-gated, like supervisor dispatch)
# --------------------------------------------------------------------------- #
def _auto_enabled():
    """
    Two independent gates, both required, neither set here:
      1. config:  automation/config/architect_bridge.json -> {"auto_writeback": "authorized"}
      2. flag:    --i-have-wired-and-authorized-architect-autowrite
    Even with both, a real headless-architect invocation that writes the ARCHITECT block
    must be wired and reviewed first. This function only reports the gate state.
    """
    cfg_path = os.path.join(HERE, "config", "architect_bridge.json")
    cfg_ok = False
    try:
        with open(cfg_path, "r", encoding="utf-8") as fh:
            cfg_ok = json.load(fh).get("auto_writeback") == "authorized"
    except (OSError, ValueError):
        cfg_ok = False
    return cfg_ok


def _gates_open(flag_set):
    """Live auto write-back requires BOTH gates. Gate 3 (invocation) is now wired."""
    return _auto_enabled() and flag_set


def auto_invoke_owed(flag_set, *, model="opus", reset=False):
    if _gates_open(flag_set):
        try:
            with _delivery.dispatch_guard():
                return _auto_invoke_owed_locked(flag_set, model=model, reset=reset)
        except BlockingIOError:
            print("Architect dispatch busy; no duplicate invocation.")
            return []
    return _auto_invoke_owed_locked(flag_set, model=model, reset=reset)


def _auto_invoke_owed_locked(flag_set, *, model="opus", reset=False):
    """For every thread that owes the architect, invoke the Solution Architect.

    LIVE (opens a visible window) only when both gates are open; otherwise every invocation is
    a dry-run PREVIEW that launches nothing. Deduped via the same cursor as notify(), so a
    standing round is invoked once, not every tick. The launched architect writes the ARCHITECT
    block itself; this function writes nothing into the channel.
    """
    import architect_invoke as _ai  # local import avoids a circular import at module load

    live = _gates_open(flag_set)
    rows = scan()
    # The auto path has its own cursor, and a PREVIEW never consumes a round: dedup only
    # tracks rounds we actually LAUNCHED live. So any number of previews can run first and
    # the first live --auto still fires for every owed round.
    cursor = {} if reset else _load_cursor(AUTO_CURSOR)
    results = []
    for r in rows:
        latest = r["latest"]
        if not _owed(latest):
            continue
        key = str(r["thread"])
        wave = _wave.active_wave()
        scoped = scoped_round(r["thread"], wave, latest)
        if live and not scoped:
            continue
        sig = f"{wave.get('wave_id') if wave else '-'}:{latest['round']}:{latest['status']}"
        if live and cursor.get(key) == sig:
            continue  # already LAUNCHED for this exact round
        notification = None
        if live:
            _delivery.foreign_controller_conflict()
            notification = _delivery.emit(wave_id=wave["wave_id"], scope=_delivery.scope_sha(wave, scoped),
                thread=r["thread"], recipient="architect", number=latest["round"], status=AWAITING,
                source=Path(CHANNEL_DIR) / f"thread{r['thread']}.md")
            active = _delivery.active_architect()
            if active:
                results.append({"thread": r["thread"], "round": latest,
                                "skipped": "queued for existing architect; read acknowledgement pending",
                                "notification": str(notification)})
                continue
        rec = _ai.invoke(r["thread"], dry_run=not live, model=model,
                         live_authorized=live, notification=notification)
        results.append(rec)
        if live and rec.get("launch", {}).get("window_id"):
            cursor[key] = sig
    if live:
        live_set = {str(r["thread"]) for r in rows}
        cursor = {k: v for k, v in cursor.items() if k in live_set}
        _save_cursor(cursor, AUTO_CURSOR)

    print(f"=== architect auto-invoke ({'LIVE' if live else 'PREVIEW — launches nothing'}) {_now()} ===")
    if not live:
        print("  gate 1 (config auto_writeback=authorized): "
              + ("SET" if _auto_enabled() else "not set"))
        print("  gate 2 (--i-have-wired-and-authorized-architect-autowrite): "
              + ("SET" if flag_set else "not set"))
        print("  gate 3 (architect invocation wired): WIRED (architect_invoke.py)")
        print("  -> both gates required for a live launch; previewing instead.")
    if not results:
        if live:
            print("  nothing owed (every owed round already launched this cursor; --reset to re-launch).")
        else:
            print("  nothing owed — no thread is AWAITING-ARCHITECT.")
    for rec in results:
        t = rec.get("thread")
        if rec.get("skipped"):
            print(f"  Thread {t}: {rec['skipped']}")
            continue
        launch = rec.get("launch", {})
        where = launch.get("window_id") or launch.get("note") or launch.get("refused") or "(no launch)"
        print(f"  Thread {t}: round {rec['round']['round']} -> architect {'LAUNCHED' if live else 'preview'} "
              f"[{launch.get('title','')}] {where}")
    return results


# Explicit, finite communication activation; never actor autolaunch.
WAKE_CHARTER_EXPIRES = _dt.datetime(2026, 11, 19, 0, 20, 22, 763308, tzinfo=_dt.timezone.utc)


def _wake_now():
    return _dt.datetime.now(_dt.timezone.utc)


def _wake_json(path, root, limit=262144):
    path = _delivery.safe_path(Path(root), Path(path).absolute())
    if path.stat().st_size > limit:
        raise ValueError('wake record exceeds size bound')
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError('wake record must be an object')
    return value


class ArchitectWakeWindow:
    """One optional lease on the existing bridge. No manifest/owner creation."""
    REQUIRED = {'schema_version', 'window_id', 'purpose', 'founder_auth_ref', 'approved_plan_digest',
                'review_receipt', 'review_receipt_sha256', 'starts_utc', 'expires_utc', 'max_submissions',
                'wave_id', 'wave_sha256', 'control_socket', 'target_session_id', 'target_binding_id',
                'allowed_threads', 'coordinator_bindings', 'communication_only', 'product_gates_unchanged'}
    OPTIONAL = {'pilot_event', 'pilot_source_sha256'}

    def __init__(self, manifest_path):
        import architect_invoke as native
        import fcntl, hashlib, uuid
        self.native = native
        self.root = Path(native.RUNS_DIR) / 'w15'
        self.path = _delivery.safe_path(self.root, Path(manifest_path).absolute())
        if self.path.parent != self.root or self.path.suffix != '.json':
            raise ValueError('wake manifest must be directly under existing w15')
        self.manifest = _wake_json(self.path, self.root, 16384)
        m = self.manifest
        if not self.REQUIRED <= set(m) or set(m) - self.REQUIRED - self.OPTIONAL:
            raise ValueError('invalid wake manifest fields')
        if bool(self.OPTIONAL & set(m)) and not self.OPTIONAL <= set(m):
            raise ValueError('pilot path and source hash must be paired')
        if (type(m['schema_version']) is not int or m['schema_version'] != 1 or
                m['purpose'] != 'existing-architect-communication-only' or
                m['communication_only'] is not True or m['product_gates_unchanged'] is not True or
                not isinstance(m['founder_auth_ref'], str) or not m['founder_auth_ref'].strip()):
            raise ValueError('explicit communication-only authorization required')
        for key in ('window_id', 'target_session_id', 'target_binding_id'):
            uuid.UUID(m[key])
        for key in ('approved_plan_digest', 'review_receipt_sha256', 'wave_sha256'):
            if not isinstance(m[key], str) or not re.fullmatch('[0-9a-f]{64}', m[key]):
                raise ValueError('invalid wake digest')
        self.start = self._date(m['starts_utc']); self.expiry = self._date(m['expires_utc'])
        if not 0 < (self.expiry - self.start).total_seconds() <= 14400 or self.expiry > WAKE_CHARTER_EXPIRES:
            raise ValueError('wake lifetime exceeds original four-hour charter')
        if type(m['max_submissions']) is not int or not 1 <= m['max_submissions'] <= 12:
            raise ValueError('wake submission budget must be 1..12')
        threads = m['allowed_threads']
        if (not isinstance(threads, list) or not threads or len(threads) != len(set(threads)) or
                any(type(n) is not int or n not in (1, 2, 3) for n in threads) or
                not isinstance(m['coordinator_bindings'], dict) or
                set(m['coordinator_bindings']) != {str(n) for n in threads}):
            raise ValueError('exact allowed thread/binding pins required')
        for pin in m['coordinator_bindings'].values():
            if not isinstance(pin, dict) or set(pin) != {'binding_id', 'session_id'}:
                raise ValueError('invalid coordinator pin')
            for value in pin.values(): uuid.UUID(value)
        endpoint = Path(m['control_socket'])
        if not endpoint.is_absolute() or '..' in endpoint.parts:
            raise ValueError('explicit absolute control socket required')
        review_path = _delivery.safe_path(self.root, Path(m['review_receipt']))
        review = _wake_json(review_path, self.root)
        if (_delivery.sha(review_path) != m['review_receipt_sha256'] or review.get('verdict') != 'APPROVED' or
                review.get('section_sha256') != m['approved_plan_digest']):
            raise ValueError('approved wake plan/review pin mismatch')
        if 'pilot_event' in m:
            pilot_path = _delivery.safe_path(self.root, Path(m['pilot_event']))
            if pilot_path.parent != self.root or pilot_path.name != 'event.json' or not re.fullmatch('[0-9a-f]{64}', m['pilot_source_sha256']):
                raise ValueError('only exact explicit pilot event permitted')
        self.manifest_sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        remaining = (self.expiry - _wake_now()).total_seconds()
        self.deadline_mono = time.monotonic() + max(0, remaining)
        self.state_path = self.root / (m['window_id'] + '.state.json')
        lockpath = _delivery.safe_path(self.root, self.root / (m['window_id'] + '.lock'))
        self.lock = lockpath.open('a+')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self.state_path.exists():
                self.state = _wake_json(self.state_path, self.root)
                if (self.state.get('manifest_sha256') != self.manifest_sha or
                        not isinstance(self.state.get('reservations'), dict) or
                        len(self.state['reservations']) > m['max_submissions']):
                    raise ValueError('wake state cannot be reset or repinned')
            else:
                self.state = {'schema_version': 1, 'window_id': m['window_id'], 'manifest_sha256': self.manifest_sha,
                              'wake_enabled': True, 'reservations': {}, 'created_utc': _now(), 'last_thread': 0}
            try:
                self.validate()
            except (OSError, ValueError, KeyError, TypeError) as error:
                self.disable(str(error))
            self.save()
        except BaseException:
            self.lock.close()
            raise

    @staticmethod
    def _date(value):
        if not isinstance(value, str): raise ValueError('UTC date required')
        parsed = _dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset() != _dt.timedelta(0):
            raise ValueError('UTC date required')
        return parsed

    def save(self):
        self.native._native_record(self.state_path, self.state)

    def close(self):
        self.lock.close()

    def remaining(self):
        return min((self.expiry - _wake_now()).total_seconds(), self.deadline_mono - time.monotonic())

    def validate(self):
        import owner_sessions as owners
        m = self.manifest
        if not self.state['wake_enabled']: raise ValueError('wake window terminal: ' + self.state.get('reason', 'disabled'))
        if _delivery.sha(self.path) != self.manifest_sha: raise ValueError('wake manifest changed')
        if not self.start <= _wake_now() < self.expiry or self.remaining() < 1:
            raise ValueError('wake window not started or expired')
        review_path = Path(m['review_receipt'])
        if _delivery.sha(_delivery.safe_path(self.root, review_path)) != m['review_receipt_sha256']:
            raise ValueError('wake review changed')
        current = self.native._native_envelope()
        if current['wave_id'] != m['wave_id'] or _delivery.sha(Path(_wave.WAVE_PATH)) != m['wave_sha256']:
            raise ValueError('wake wave changed')
        owner = owners.binding('architect')
        if (not owner or owner.get('state') != 'bound' or owner.get('executor') != 'codex' or
                owner.get('binding_id') != m['target_binding_id'] or owner.get('session_id') != m['target_session_id']):
            raise ValueError('wake architect binding changed')
        for n, pin in m['coordinator_bindings'].items():
            peer = owners.binding('coordinator', int(n))
            if not peer or peer.get('state') != 'bound' or any(peer.get(k) != v for k, v in pin.items()):
                raise ValueError('wake coordinator binding changed')
        return owner, current

    def disable(self, reason):
        if self.state['wake_enabled']:
            self.state.update(wake_enabled=False, reason=reason[:256], ended_utc=_now())
            self.save()

    def _selected(self, event_id, notification, digest, owner, current):
        selected_owner, selected_wave = self.validate()
        if owner != selected_owner or current != selected_wave:
            raise ValueError('wake authority changed before submission')
        chosen = self.native._native_event(notification, owner, current)
        if chosen[0] != event_id or chosen[2] != digest:
            raise ValueError('wake event changed before submission')
        raw = _wake_json(notification, Path(self.native.RUNS_DIR).parent.parent)
        if raw.get('kind') == 'bounded-tooling-native-handoff':
            if (str(Path(notification).absolute()) != self.manifest.get('pilot_event') or
                    digest != self.manifest.get('pilot_source_sha256')):
                raise ValueError('unlisted wake pilot event')
        elif raw.get('thread') not in self.manifest['allowed_threads']:
            raise ValueError('wake event thread outside window')
        return raw

    def reserve(self, event_id, notification, digest, owner, current):
        raw = self._selected(event_id, notification, digest, owner, current)
        if event_id in self.state['reservations'] or len(self.state['reservations']) >= self.manifest['max_submissions']:
            raise ValueError('wake reservation already exists or budget exhausted')
        self.state['reservations'][event_id] = {'event_path': str(Path(notification).absolute()),
            'source_sha256': digest, 'kind': raw.get('kind', 'scoped-v1'), 'state': 'reserved', 'utc': _now()}
        self.save()

    def pre_submit(self, event_id, notification, digest, owner, current):
        self._selected(event_id, notification, digest, owner, current)
        if event_id not in self.state['reservations']:
            raise ValueError('durable wake reservation missing')

    def acknowledged(self, event_id, record):
        m = self.manifest; path = Path(record['event_path'])
        if record['kind'] == 'bounded-tooling-native-handoff':
            ackpath = path.parent / 'architect-read-ack.json'
            if not ackpath.exists(): return False
            ack = _wake_json(ackpath, self.root)
            expected = {'schema_version': 1, 'event_id': event_id, 'source_sha256': record['source_sha256'],
                        'session_id': m['target_session_id'], 'binding_id': m['target_binding_id'],
                        'owner_authenticated': True, 'state': 'read'}
            if any(ack.get(k) != value for k, value in expected.items()) or not isinstance(ack.get('read_utc'), str):
                raise ValueError('invalid receiving-owner pilot ACK')
            self._date(ack['read_utc'])
            return True
        ackpath = path.with_suffix('.read.json')
        if not ackpath.exists(): return False
        event = _delivery.validate_event(_wake_json(path, _delivery.MAILBOX_ROOT), verify_source=False)
        expected = {k: event[k] for k in ('schema_version', 'id', 'recipient', 'thread', 'wave_id', 'scope_sha256', 'source_sha256')}
        expected['state'] = 'read'
        if _wake_json(ackpath, _delivery.MAILBOX_ROOT) != expected or record['source_sha256'] != event['source_sha256']:
            raise ValueError('invalid scoped architect ACK')
        return True

    def tick(self):
        try:
            if self.state['wake_enabled']: self.validate()
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.disable(str(error))
        queued = _delivery.delivery_only_tick('architect')
        if not self.state['wake_enabled']: return {'state': 'queue-only', 'queued': len(queued['events'])}
        try:
            for event_id, record in self.state['reservations'].items():
                if record['state'] != 'native-completed':
                    self.disable('prior submission needs reconciliation'); return {'state': 'wake-disabled'}
                if not self.acknowledged(event_id, record): return {'state': 'awaiting-owner-read-ACK'}
            if len(self.state['reservations']) >= self.manifest['max_submissions']:
                self.disable('submission budget exhausted'); return {'state': 'queue-only'}
            owner, current = self.validate()
            candidates = []
            if 'pilot_event' in self.manifest: candidates.append(self.manifest['pilot_event'])
            candidates.extend(sorted(queued['events'], key=lambda p: (int(_wake_json(p, _delivery.MAILBOX_ROOT)['thread']) - self.state['last_thread'] - 1) % 3))
            for path in candidates:
                raw = _wake_json(path, Path(self.native.RUNS_DIR).parent.parent)
                event_id = raw.get('event_id', raw.get('id'))
                if not event_id or event_id in self.state['reservations']: continue
                if raw.get('thread') is not None and raw['thread'] not in self.manifest['allowed_threads']: continue
                attempt = Path(self.native.RUNS_DIR) / 'native-deliveries' / (event_id + '.json')
                if attempt.exists(): continue  # Dedupe survives different windows/restarts.
                if raw.get('kind') != 'bounded-tooling-native-handoff' and Path(path).with_suffix('.read.json').exists():
                    # Existing pending validator also verifies completed ACK history after source edits.
                    _delivery.pending(recipient='architect', thread=raw['thread'], wave_id=current['wave_id'], scope=raw['scope_sha256'])
                    continue
                result = self.native.deliver_existing_native(path, self.manifest['control_socket'],
                         self.manifest['target_binding_id'], min(60, int(self.remaining())), wake_window=self)
                if result['state'] == 'queued-owner-not-idle': return result
                if result['state'] == 'already-attempted': continue
                record = self.state['reservations'].get(event_id)
                if record is None: raise ValueError('native attempt has no window reservation')
                record.update(state=result['state'], turn_id=result.get('turn_id'))
                self.state['last_thread'] = raw.get('thread', self.state['last_thread']); self.save()
                if result['state'] != 'native-completed': self.disable('submission needs reconciliation: ' + result['state'])
                return result
            return {'state': 'waiting-current-scoped-mail'}
        except BlockingIOError:
            return {'state': 'dispatch-busy-deferred'}
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.disable(str(error)); return {'state': 'wake-disabled', 'reason': str(error)[:256]}


def watch_existing_owner_delivery(manifest_path, interval):
    import daemon
    window = ArchitectWakeWindow(manifest_path)
    try:
        while True:
            try:
                result = window.tick()
            except (OSError, ValueError, KeyError, TypeError, BlockingIOError) as error:
                window.disable(str(error)); result = {'state': 'queue-blocked', 'reason': str(error)[:256]}
            daemon.write_status('architect_bridge', state='running', path_mode='delivery-only-existing-owner-wake',
                live=False, wake_enabled=window.state['wake_enabled'], window_id=window.manifest['window_id'],
                wake_deadline=window.manifest['expires_utc'], remaining_reservations=window.manifest['max_submissions']-len(window.state['reservations']),
                summary='existing-owner communication only: ' + result['state'])
            print(json.dumps(result), flush=True)
            time.sleep(min(max(5, interval), max(0.1, window.remaining())) if window.state['wake_enabled'] else max(5, interval))
    finally:
        window.close()


def main(argv=None):
    p = argparse.ArgumentParser(description="Coordinator<->Architect channel bridge (Stage-1 safe).")
    p.add_argument("--notify", action="store_true", help="one-shot: emit `Discuss Thread<n>` for owed rounds")
    p.add_argument("--watch", action="store_true", help="continuous notify loop")
    p.add_argument("--delivery-only", action="store_true", help="queue scoped file events; never launch actors")
    p.add_argument("--architect-wake-window", metavar="MANIFEST", help="explicit finite existing-owner communication window; requires watch/delivery-only")
    p.add_argument("--deliver-existing-once", metavar="EVENT", help="one bounded delivery to an already-bound idle Codex architect")
    p.add_argument("--reconcile-existing-once", metavar="EVENT", help="one metadata-only completion read for an already-submitted event")
    p.add_argument("--control-socket", metavar="SOCKET", help="explicit existing private app-server socket")
    p.add_argument("--expected-binding", metavar="UUID", help="exact existing architect binding for one-shot delivery")
    p.add_argument("--native-timeout", type=int, default=45, help="one-shot native deadline, 1..60 seconds")
    p.add_argument("--interval", type=int, default=30, help="watch interval seconds (min 5)")
    p.add_argument("--reset", action="store_true", help="ignore prior cursor")
    p.add_argument("--json", action="store_true", help="raw per-thread state")
    p.add_argument("--auto", action="store_true",
                   help="invoke the architect for every owed round (LIVE only if dual-gated, else previews)")
    p.add_argument("--preview-invoke", type=int, metavar="THREAD",
                   help="show the exact architect launch for one thread; launch nothing")
    p.add_argument("--model", default="opus", help="claude model for the invoked architect (default opus)")
    p.add_argument("--i-have-wired-and-authorized-architect-autowrite",
                   dest="auto_flag", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args(argv)

    if args.architect_wake_window:
        if (not args.watch or not args.delivery_only or args.auto or args.auto_flag or args.reset or args.notify or
                args.preview_invoke is not None or args.deliver_existing_once or args.reconcile_existing_once or
                args.control_socket or args.expected_binding or args.json):
            p.error('wake window requires watch/delivery-only and forbids launch/reset/one-shot options')
        try:
            watch_existing_owner_delivery(args.architect_wake_window, max(5, args.interval))
            return 0
        except (OSError, ValueError, KeyError, TypeError, BlockingIOError) as error:
            print(json.dumps({'state': 'wake-window-refused', 'reason': str(error)[:256]})); return 2

    if args.deliver_existing_once or args.reconcile_existing_once:
        if (args.watch or args.auto or args.auto_flag or args.reset or args.preview_invoke is not None
                or args.notify or not args.delivery_only or not args.control_socket or not args.expected_binding
                or (args.deliver_existing_once and args.reconcile_existing_once)):
            p.error('existing-owner delivery requires delivery-only/socket/binding and cannot launch/watch/reset')
        import architect_invoke
        try:
            operation = architect_invoke.deliver_existing_native if args.deliver_existing_once else architect_invoke.reconcile_existing_native
            result = operation(args.deliver_existing_once or args.reconcile_existing_once, args.control_socket,
                               args.expected_binding, args.native_timeout)
            print(json.dumps(result, indent=2))
            return 0 if result.get('state') in ('native-completed', 'already-attempted', 'reconciled-native-completed', 'already-reconciled') else 2
        except (OSError, ValueError, KeyError, TypeError, BlockingIOError) as error:
            print(json.dumps({'state':'refused', 'reason':str(error), 'sent':False})); return 2
    if args.control_socket or args.expected_binding:
        p.error('socket/binding are only valid with explicit one-shot existing-owner delivery')

    if args.delivery_only:
        if args.auto or args.auto_flag or args.reset or args.preview_invoke is not None:
            p.error('delivery-only cannot be combined with launch/reset options')
        if args.watch:
            _delivery.watch_delivery('architect', args.interval)
        else:
            print(json.dumps(_delivery.delivery_only_tick('architect'), indent=2))
        return 0

    if args.preview_invoke is not None:
        import architect_invoke as _ai
        print(json.dumps(_ai.invoke(args.preview_invoke, dry_run=True, model=args.model), indent=2))
        return 0
    if args.json:
        print(json.dumps(scan(), indent=2))
        return 0
    if args.watch:
        if args.auto:
            watch_auto(args.interval, args.auto_flag, model=args.model, reset=args.reset)
        else:
            watch(args.interval, reset=args.reset)
        return 0
    if args.auto:
        auto_invoke_owed(args.auto_flag, model=args.model, reset=args.reset)
        return 0
    if args.notify:
        emitted = notify(reset=args.reset)
        if not emitted:
            print("Nothing owed to the architect.")
        return 0
    print_table(scan())
    return 0


if __name__ == "__main__":
    sys.exit(main())
