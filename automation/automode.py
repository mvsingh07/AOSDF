#!/usr/bin/env python3
"""automode.py — one control point for Ultimate Auto Mode (founder-named 24Nov2026).

Ultimate Auto Mode = the EXISTING bound SA and coordinator sessions + an SA-verified, delivery-only wave +
the wake relay (rounds, peer messages, worker results, founder notices, all-threads-drained -> SA).
It launches no new agent and crosses no founder gate.

  start      Begin Ultimate Auto Mode for the ACTIVE, architect-verified wave: pin the wake relay to that
             wave and its deadline, start the two delivery watchers and the wake relay, wake now.
  pause      Hold everything: wave -> paused (coordinators stop at their next checkpoint), relay off.
             Processes keep running so `continue` is instant.
  continue   Undo pause: wave -> active, relay on, processes ensured, wake now.  (alias: resume)
  close      End Ultimate Auto Mode: relay off, stop the relay and both delivery watchers.
             The wave is left as it is unless --complete-wave is given.  (alias: stop)
  restart    close + start (wave untouched).
  status     One screen: state, wave, processes, owners (runtime, wake path, last wake, owed input).
  wake       Wake owners with unread input now (optionally --owner architect|coordinator1..3).
  tell       Send a founder notice to owners (--to all|architect|coordinator1..3 ...); the relay delivers it
             with its normal idle/once-only guards.
  watch      Live, auto-refreshing console (read-only): mode, wave countdown, processes, owners with wake
             budget, each thread's latest round and who it is owed to, workers, and the recent wake log.
  header     Print the exact round header (with the mandatory wave:/scope: tags) for a thread.
  ask        (agents) Record a decision the founder owes: --from ROLE --question ... [--thread N]
             [--options ...] [--recommendation ...] [--blocked ...]. Raises a desktop notification.
             Never stop for the founder without it.
  decisions  List open founder decisions (with --all: answered ones too).
  answer     (founder) Answer one: answer ID --message ...; closes it and notifies the asker and the SA.
  learn      (agents) NON-blocking founder item: --from ROLE --kind learn|read|review|research|answer --title ...
             --why ... [--what ...] [--research ...] [--thread N] [--task ID] [--link PATH]; work continues.
  learning   (founder) List learn/read/review/research items (also 12_Manual_Actions/human-actions.md).
  done       (founder) Mark one done: done ID [--note ...]; no notice sent.
  dismiss    (founder) Close one without sending anything (already handled elsewhere): dismiss ID.
  rotate     Archive old channel rounds verbatim to coordinator-architect/history/ (rule C17), keeping the
             newest 5 [--thread N] [--keep K] [--dry-run]. Changes no round; status says when it is due.

Never launches or replaces an agent, never changes owners/profiles/Mode/review rules, and grants no
protected-operation authority. Defining or verifying a wave stays with the founder and the SA.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import channel_delivery as _delivery  # noqa: E402
import daemon as _d  # noqa: E402
import owner_sessions as _owners  # noqa: E402
import initiate_automation as runtime  # noqa: E402
import owner_wake as relay  # noqa: E402
import wave as _wave  # noqa: E402
import founder_inbox as _inbox  # noqa: E402

WATCHERS = ('architect_bridge', 'coordinator_trigger')
INTERVAL = 30


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _spec(name: str) -> dict:
    return next(s for s in runtime.DAEMONS if s['name'] == name)


def _set_wake(**changes) -> dict:
    cfg = json.loads(relay.CONFIG.read_text())
    cfg.update(changes)
    tmp = relay.CONFIG.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(cfg, indent=2) + '\n')
    tmp.replace(relay.CONFIG)
    return cfg


def _set_wave_status(status: str) -> None:
    current = _wave.load()
    if not current:
        raise SystemExit('No wave defined. Define and verify one first (wave.py define + SA verification).')
    current['status'] = status
    current['updated_utc'] = _utc()
    _wave.save(current)


def _ensure_processes() -> list[dict]:
    started = []
    for name in WATCHERS:
        started.append(runtime.start_one(_spec(name), False, INTERVAL, delivery_only=True))
    started.append(runtime.start_one(_spec('owner_wake'), False, INTERVAL))
    return started


def _stop_processes() -> list[dict]:
    return [runtime.stop_one(name) for name in ('owner_wake',) + WATCHERS]


def _require_verified_active_wave() -> dict:
    current = _wave.load()
    if not current:
        raise SystemExit('No wave defined. Define one (wave.py define) and have the SA verify it.')
    if current.get('status') != 'active':
        raise SystemExit(f"Wave {current['wave_id']} is {current.get('status')}. Use `continue` for a paused wave.")
    if current.get('verified_by_architect') is not True:
        raise SystemExit(f"Wave {current['wave_id']} is not verified by the SA yet; nothing can run until it is.")
    deadline = dt.datetime.fromisoformat(current['operating_deadline_utc'].replace('Z', '+00:00'))
    if dt.datetime.now(dt.timezone.utc) >= deadline:
        raise SystemExit(f"Wave {current['wave_id']} expired at {current['operating_deadline_utc']}. Define a new wave.")
    return current


def _print_wake(result: dict) -> None:
    if result.get('state') != 'active':
        print(f"  wake relay inactive: {result.get('reason')}")
        return
    for o in result['owners']:
        extra = o.get('events') or o.get('pending') or o.get('error') or ''
        print(f"  {o['role']:<13} {o.get('adapter', ''):<12} {o['state']}  {extra if extra else ''}")


def cmd_start(_a) -> int:
    current = _require_verified_active_wave()
    _set_wake(enabled=True, wave_id=current['wave_id'], expires_utc=current['operating_deadline_utc'])
    for r in _ensure_processes():
        print(f"  {r['name']:<20} {r['action']}" + (f" (pid {r['pid']})" if r.get('pid') else ''))
    print(f"Ultimate Auto Mode STARTED for {current['wave_id']} until {current['operating_deadline_utc']}.")
    _print_wake(relay.tick())
    return 0


def cmd_pause(_a) -> int:
    _set_wave_status('paused')
    _set_wake(enabled=False)
    print('Ultimate Auto Mode PAUSED: wave paused (coordinators stop at their next checkpoint), wake relay off.')
    print('Resume with: python3 automation/automode.py continue')
    return 0


def cmd_continue(_a) -> int:
    current = _wave.load()
    if not current:
        raise SystemExit('No wave defined.')
    if current.get('status') == 'complete':
        raise SystemExit(f"Wave {current['wave_id']} is complete; define a new wave and use `start`.")
    _set_wave_status('active')
    return cmd_start(_a)


def cmd_close(a) -> int:
    _set_wake(enabled=False)
    for r in _stop_processes():
        print(f"  {r['name']:<20} {r['action']}")
    if a.complete_wave:
        _set_wave_status('complete')
        print('Wave marked complete.')
    print('Ultimate Auto Mode CLOSED. Agents keep their sessions; nothing will wake them until `start`.')
    return 0


def cmd_restart(a) -> int:
    a.complete_wave = False
    cmd_close(a)
    return cmd_start(a)


def state_word() -> str:
    current = _wave.load() or {}
    try:
        cfg = relay.load_config()
    except (OSError, ValueError):
        cfg = {}
    running = runtime._running_pid('owner_wake')
    if not running:
        return 'CLOSED'
    if current.get('status') == 'paused' or not cfg.get('enabled'):
        return 'PAUSED'
    if current.get('status') != 'active':
        return f"IDLE (wave {current.get('status', 'missing')})"
    return 'RUNNING'


def cmd_status(_a) -> int:
    print('Process Mode: ' + _d.runtime_mode()['mode'])
    current = _wave.load()
    print(f"Ultimate Auto Mode: {state_word()}")
    pending = _inbox.requests()
    if pending:
        print(f"!! {len(pending)} FOUNDER DECISION(S) NEEDED — see `automode.py decisions`:")
        print('\n'.join(_decision_lines(pending)))
    learning = _inbox.requests(learning=True)
    if learning:
        print(f"-- {len(learning)} item(s) for you to learn/read/review/research (non-blocking) — `automode.py learning`")
    print(f"Wave: {_wave.summary_line(current) if current else 'none'}"
          + (f" | verified={current.get('verified_by_architect')} | ends {current.get('operating_deadline_utc')}" if current else ''))
    for name in WATCHERS + ('owner_wake',):
        pid = runtime._running_pid(name)
        st = _d.read_status(name)
        print(f"  {name:<20} {'up ' + str(pid) if pid else 'down':<10} {st.get('summary', '')[:60]}")
    info = relay.status()
    if 'owners' in info:
        dry = relay.tick(dry_run=True)
        owed = {o['role']: o for o in dry.get('owners', [])}
        print(f"Owners (relay {'on' if info['enabled'] else 'off'}, until {info['expires_utc']}):")
        for role, row in info['owners'].items():
            if row == 'unbound':
                print(f"  {role:<13} unbound")
                continue
            last = row['recent'][-1] if row['recent'] else {}
            pending = owed.get(role, {})
            pend = pending.get('events') or pending.get('state', '')
            used = f"{row.get('used', '?')}/{row.get('budget', '?')}"
            warn = '  << BUDGET EXHAUSTED: raise max_wakes_per_owner' if row.get('used', 0) >= row.get('budget', 1) else ''
            print(f"  {role:<13} {row['executor']:<7} path={row['adapter']:<11} wakes {used:<6} last: "
                  f"{last.get('utc', '-')[11:19]} {last.get('state', '')} | waiting: {pend}{warn}")
    else:
        print(f"Relay config: {info.get('config')}")
    try:
        import channel_rotate as rot
        big = rot.large_channels()
        if big:
            print('Channels to rotate (C17): ' + ', '.join(f'thread{n} {b // 1024}KB' for n, b in big)
                  + ' — run `automode.py rotate`')
    except Exception:
        pass
    return 0


def cmd_wake(a) -> int:
    _print_wake(relay.tick(only=a.owner))
    return 0


def round_header(thread: int, rnd: int, checkpoint: str, status: str) -> str:
    current = _require_verified_active_wave()
    sprint = _wave.verified_thread_sprint(current, thread)
    if not sprint:
        raise SystemExit(f'Thread {thread} has no verified sprint in {current["wave_id"]}.')
    binding = json.loads((_owners.OWNERS / f'coordinator{thread}.json').read_text()).get('binding_id', '')
    return (f'<!-- round:{rnd} checkpoint:{checkpoint} status:{status} opened:{_utc()} '
            f'wave:{current["wave_id"]} scope:{_delivery.scope_sha(current, sprint)} binding:{binding} -->')


def cmd_header(a) -> int:
    print(round_header(a.thread, a.round, a.checkpoint, a.status))
    return 0


def cmd_tell(a) -> int:
    current = _require_verified_active_wave()
    roles = list(relay.ROLES) if 'all' in a.to else a.to
    path = relay.post_notice(roles, a.message, current['wave_id'])
    print(f'Notice {path.stem[:12]} posted for {", ".join(roles)}; delivering now (busy owners get it when idle).')
    _print_wake(relay.tick())
    return 0


def _decision_lines(rows: list[dict], c=lambda t, *s: str(t)) -> list[str]:
    out = []
    for r in rows:
        tail = f"  [{r.get('status')}] answer: {r.get('answer', '')[:80]}" if r.get('status') != 'open' else ''
        out.append(f"  {c(r['id'], 'b')}  {r.get('utc', '')[:16]}Z  from {r['from']}"
                   + (f" T{r['thread']}" if r.get('thread') else '') + f"  ({r.get('origin')}){tail}")
        out.append(f"      Q: {r['question'][:300]}")
        for label, key in (('Options', 'options'), ('Recommends', 'recommendation'), ('Blocks', 'blocked')):
            if r.get(key):
                out.append(f"      {label}: {r[key][:200]}")
    return out


def _learn_lines(rows: list[dict], c=lambda t, *s: str(t)) -> list[str]:
    out = []
    for r in rows:
        out.append(f"  {c(r['id'], 'b')}  {r.get('utc', '')[:16]}Z  {c(r.get('kind', '').upper(), 'cyn')}  from {r['from']}"
                   + (f" T{r['thread']}" if r.get('thread') else '') + (f"  {r['task']}" if r.get('task') else '')
                   + (f"  [{r.get('status')}]" if r.get('status') != 'open' else ''))
        out.append(f"      {r['question'][:200]}")
        for label, key in (('Why', 'why'), ('What', 'what'), ('Research', 'research'), ('Look at', 'link')):
            if r.get(key):
                out.append(f"      {label}: {r[key][:200]}")
    return out


def thread_summaries() -> dict[int, str]:
    """The latest `**Summary:**` line each coordinator/SA wrote in coordinator-architect/threadN.md."""
    out = {}
    for n in (1, 2, 3):
        try:
            text = (relay.CHANNEL_DIR / f'thread{n}.md').read_text(encoding='utf-8')
        except OSError:
            continue
        found = re.findall(r'(?m)^\*\*Summary:\*\*\s*(.+)$', text)
        if found:
            out[n] = ' '.join(found[-1].split())
    return out


def cmd_learn(a) -> int:
    if state_word() == 'RUNNING':  # founder 26Nov: learning notes stay out of Ultimate Auto Mode, for speed
        print('Not recorded: learning/design items are off while Ultimate Auto Mode is RUNNING. Continue your work; '
              'if it needs a founder decision, use `ask`.')
        return 0
    current = _wave.load() or {}
    record, new = _inbox.learn(a.sender, a.kind, a.title, why=a.why, what=a.what or '', research=a.research or '',
                               thread=a.thread, task=a.task or '', link=a.link or '',
                               wave_id=current.get('wave_id', ''))
    print(f"Founder {a.kind} item {record['id']} {'recorded and notified' if new else 'already recorded'} "
          '(also in 12_Manual_Actions/human-actions.md). This does NOT block: continue your work.')
    return 0


def cmd_learning(a) -> int:
    rows = _inbox.requests(open_only=not a.all, learning=True)
    if not rows:
        print('Nothing to learn, read, review or research right now.')
        return 0
    print('\n'.join(_learn_lines(rows)))
    print('Mark done: automode.py done <id>   ·   reply to the agents: automode.py answer <id> --message "..."')
    return 0


def cmd_done(a) -> int:
    record = _inbox.done(a.id, a.note or '')
    print(f"Marked {record['id']} done; no notice sent.")
    return 0


def cmd_ask(a) -> int:
    current = _wave.load() or {}
    record, new = _inbox.ask(a.sender, a.question, thread=a.thread, options=a.options or '',
                             recommendation=a.recommendation or '', blocked=a.blocked or '',
                             wave_id=current.get('wave_id', ''), research=a.research or '')
    print(f"Founder decision {record['id']} {'recorded and notified' if new else 'already open'}. "
          'Now STOP that work, say so in your reply, and wait for the FOUNDER DECISION notice.')
    return 0


def cmd_decisions(a) -> int:
    rows = _inbox.requests(open_only=not a.all)
    if not rows:
        print('No open founder decisions.' if not a.all else 'No founder decisions recorded.')
        return 0
    print('\n'.join(_decision_lines(rows)))
    print('Answer with: python3 automation/automode.py answer <id> --message "..."')
    return 0


def cmd_dismiss(a) -> int:
    record = _inbox.dismiss(a.id)
    print(f"Dismissed {record['id']}; no notice sent.")
    return 0


def cmd_answer(a) -> int:
    current = _require_verified_active_wave()
    record = _inbox.answer(a.id, a.message, current['wave_id'])
    print(f"Answered {record['id']}; notice sent to {', '.join(record['notified_roles'])}.")
    _print_wake(relay.tick())
    return 0


class _Skin:
    CODES = {'b': '1', 'dim': '2', 'red': '31', 'grn': '32', 'yel': '33', 'cyn': '36'}

    def __init__(self, on: bool):
        self.on = on

    def __call__(self, text, *styles) -> str:
        if not self.on or not styles:
            return str(text)
        return '\033[' + ';'.join(self.CODES[s] for s in styles) + 'm' + str(text) + '\033[0m'


def _ago(iso: str | None) -> str:
    if not iso:
        return '-'
    try:
        secs = int((dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(iso.replace('Z', '+00:00'))).total_seconds())
    except ValueError:
        return '?'
    if secs < 120:
        return f'{secs}s ago'
    if secs < 7200:
        return f'{secs // 60}m ago'
    return f'{secs // 3600}h ago' if secs < 172800 else f'{secs // 86400}d ago'


def _iso(value) -> str | None:
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat()
    return value.isoformat() if hasattr(value, 'isoformat') else value


def _left(iso: str | None) -> str:
    try:
        secs = int((dt.datetime.fromisoformat(iso.replace('Z', '+00:00')) - dt.datetime.now(dt.timezone.utc)).total_seconds())
    except (AttributeError, ValueError):
        return '?'
    return 'expired' if secs <= 0 else f'{secs // 3600}h{(secs % 3600) // 60:02d}m left'


def watch_frame(c: _Skin) -> list[str]:
    """One read-only frame. Writes nothing (dry-run relay pass only)."""
    import architect_bridge as bridge
    out = []
    word = state_word()
    colour = {'RUNNING': 'grn', 'PAUSED': 'yel', 'CLOSED': 'red'}.get(word, 'yel')
    current = _wave.load() or {}
    out.append(c(' ULTIMATE AUTO MODE ', 'b') + c(f'[{word}]', 'b', colour) + c(f'   {_utc()[:19]}Z   (Ctrl-C to exit)', 'dim'))
    if current:
        out.append(f" Wave {c(current.get('wave_id'), 'cyn')}  {current.get('status')}  verified={current.get('verified_by_architect')}"
                   f"  ends {current.get('operating_deadline_utc', '')[:16]}Z ({_left(current.get('operating_deadline_utc'))})")
    else:
        out.append(' Wave: none')
    pending = _inbox.requests()
    if pending:
        out.append(c(f' FOUNDER DECISIONS NEEDED ({len(pending)})', 'red', 'b')
                   + c('   answer: automode.py answer <id> --message "…"', 'dim'))
        out.extend(c(line, 'red') if line.startswith('  ') and not line.startswith('      ') else line
                   for line in _decision_lines(pending, c))
    learning = _inbox.requests(learning=True)
    if learning:
        out.append(c(f' FOR YOU TO LEARN / REVIEW / RESEARCH ({len(learning)}, non-blocking)', 'cyn', 'b')
                   + c('   list: automode.py learning   done: automode.py done <id>', 'dim'))
        out.extend(_learn_lines(learning[-4:], c))
    summaries = thread_summaries()
    if summaries:
        out.append(c(' WHAT IS HAPPENING (latest **Summary:** per thread)', 'b'))
        out.extend(f"  T{n}  {txt[:180]}" for n, txt in sorted(summaries.items()))
    out.append(c(' ' + '─' * 92, 'dim'))
    out.append(c(' PROCESSES', 'b'))
    for name in WATCHERS + ('owner_wake',):
        pid = runtime._running_pid(name)
        st = _d.read_status(name)
        out.append(f"  {c('●', 'grn') if pid else c('○', 'red')} {name:<20} {('pid ' + str(pid)) if pid else 'down':<10} "
                   f"{c(str(st.get('summary', ''))[:58], 'dim')}")
    info = relay.status()
    dry = relay.tick(dry_run=True) if 'owners' in info else {}
    owed = {o['role']: o for o in dry.get('owners', [])}
    out.append(c(' OWNERS', 'b') + c(f"   relay {'on' if info.get('enabled') else 'off'}", 'dim'))
    log = []
    for role, row in (info.get('owners') or {}).items():
        if row == 'unbound':
            out.append(f'  {role:<13} {c("unbound", "red")}')
            continue
        used, budget = row.get('used', 0), row.get('budget', 0)
        last = row['recent'][-1] if row['recent'] else {}
        pend = owed.get(role, {})
        waiting = pend.get('state', '')
        flag = c('would wake now', 'yel') if waiting == 'would-wake' else c(waiting, 'dim')
        bud = c(f'{used}/{budget}', 'red' if used >= budget else ('yel' if used >= budget * 0.75 else 'grn'))
        out.append(f"  {role:<13} {row['executor']:<6} wakes {bud:<6}  last {_ago(last.get('utc')):<9} "
                   f"{last.get('adapter', ''):<11} {last.get('state', ''):<10} {flag}")
        for sub in row['recent']:
            log.append((sub.get('utc', ''), role, sub.get('state', ''), '; '.join(sub.get('events', []))))
    out.append(c(' CHANNELS (coordinator ↔ SA)', 'b'))
    for n in (1, 2, 3):
        raw = bridge._latest_round(str(relay.CHANNEL_DIR / f'thread{n}.md')) or {}
        latest = relay.latest_round(n) or {}
        if not latest:
            out.append(f'  T{n}  no rounds')
            continue
        status = latest.get('status', '')
        owner = 'SA' if status == 'AWAITING-ARCHITECT' else ('coordinator' if status in ('ALIGNED', 'REDIRECT') else '-')
        tag = c('tags ok', 'grn') if raw.get('wave_id') and raw.get('scope_sha256') else c('MISSING wave:/scope: tags', 'red', 'b')
        wave_ok = '' if latest.get('wave_id') == current.get('wave_id') else c(' (other wave)', 'yel')
        out.append(f"  T{n}  Round {latest['round']:<4} {latest.get('checkpoint', ''):<18} {status:<19} owed to {owner:<12} {tag}{wave_ok}")
    if current:
        drained = relay.drained_input(current, relay.load_config().get('idle_after_seconds', relay.IDLE_AFTER_SECONDS)) \
            if info.get('owners') else []
        busy = relay.busy_workers()
        if drained:
            out.append('  ' + c('ALL THREADS DRAINED', 'yel', 'b') + c(' -> the SA is asked once for next assignments or a founder-gate list', 'dim'))
        elif not busy:
            out.append(c('  no worker running; drained check fires after the threads stay quiet for '
                         f"{relay.load_config().get('idle_after_seconds', relay.IDLE_AFTER_SECONDS) // 60} min", 'dim'))
    out.append(c(' WORKERS', 'b'))
    try:
        import monitor
        _cfg, _root, agents = monitor.scan(HERE / 'config' / 'topology.json')
        for a in agents:
            mark = c('▶', 'grn') if a.get('run_running') else c('·', 'dim')
            st = str(a.get('state_status') or '-')
            col = 'grn' if st in ('running', 'ready') else ('red' if st in ('blocked', 'failed') else 'dim')
            ended = a.get('run_ended') or a.get('run_started')
            out.append(f"  {mark} {a['agent']:<9} {c(f'{st:<10}', col)} seq {a.get('state_seq') or '-'!s:<5} "
                       f"{str(a.get('model') or ''):<8} {c(('started ' if a.get('run_running') else 'last ') + _ago(_iso(ended)), 'dim')}")
    except (SystemExit, Exception) as error:  # read-only view: never crash the console
        out.append(c(f'  worker scan unavailable: {error}', 'dim'))
    out.append(c(' RECENT WAKES', 'b'))
    for utc, role, state, events in sorted(set(log), reverse=True)[:6]:
        out.append(f"  {utc[11:19]} {role:<13} {state:<10} {c(events[:70], 'dim')}")
    out.append(c(' ' + '─' * 92, 'dim'))
    out.append(c(' start | pause | continue | close | restart | wake | tell | header | decisions | answer ID --message … | learning | done ID', 'dim'))
    return out


def cmd_rotate(a) -> int:
    import channel_rotate as rot
    for n in ([a.thread] if a.thread else [1, 2, 3]):
        r = rot.rotate(n, keep=a.keep, min_bytes=0 if a.thread else rot.MIN_BYTES, dry_run=a.dry_run)
        extra = f" moved {r['moved_rounds']} round(s), kept {r['kept_rounds']}, {r['bytes']}B -> {r['new_bytes']}B" if 'moved_rounds' in r else f" {r['bytes']}B"
        print(f"thread{n}: {r['state']}{extra}{' -> ' + r['history'] if r.get('history') else ''}")
    return 0


def cmd_watch(a) -> int:
    skin = _Skin(a.color == 'always' or (a.color == 'auto' and sys.stdout.isatty() and 'NO_COLOR' not in os.environ))
    if a.once:
        print('\n'.join(watch_frame(skin)))
        return 0
    try:
        while True:
            frame = '\n'.join(watch_frame(skin))
            sys.stdout.write('\033[H\033[2J' + frame + '\n')
            sys.stdout.flush()
            time.sleep(max(2, a.interval))
    except KeyboardInterrupt:
        return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description='Control Ultimate Auto Mode (start/pause/continue/close/restart/status/wake).')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('start')
    sub.add_parser('pause')
    sub.add_parser('continue', aliases=['resume'])
    c = sub.add_parser('close', aliases=['stop'])
    c.add_argument('--complete-wave', action='store_true', help='also mark the wave complete')
    sub.add_parser('restart')
    sub.add_parser('status')
    w = sub.add_parser('wake')
    w.add_argument('--owner', choices=relay.ROLES)
    t = sub.add_parser('tell')
    t.add_argument('--to', nargs='+', required=True, choices=('all',) + tuple(relay.ROLES))
    t.add_argument('--message', required=True)
    wt = sub.add_parser('watch')
    wt.add_argument('--interval', type=int, default=5)
    wt.add_argument('--once', action='store_true')
    wt.add_argument('--color', choices=('auto', 'always', 'never'), default='auto')
    h = sub.add_parser('header')
    h.add_argument('--thread', type=int, required=True, choices=(1, 2, 3))
    h.add_argument('--round', type=int, required=True)
    h.add_argument('--checkpoint', required=True, choices=('sprint', 'sprint-completion', 'conflict', 'assignment'))
    h.add_argument('--status', default='AWAITING-ARCHITECT')
    k = sub.add_parser('ask', help='(agents) record a decision the founder owes')
    k.add_argument('--from', dest='sender', required=True, choices=relay.ROLES)
    k.add_argument('--question', required=True)
    k.add_argument('--thread', type=int, choices=(1, 2, 3))
    k.add_argument('--options')
    k.add_argument('--recommendation')
    k.add_argument('--blocked', help='what is waiting on this decision')
    k.add_argument('--research', help='what the founder should research before deciding (listed in human-actions.md)')
    ln = sub.add_parser('learn', help='(agents) NON-blocking item for the founder to learn/read/review/research/answer')
    ln.add_argument('--from', dest='sender', required=True, choices=relay.ROLES)
    ln.add_argument('--kind', required=True, choices=_inbox.LEARN_KINDS)
    ln.add_argument('--title', required=True, help='what to look at, in plain language')
    ln.add_argument('--why', required=True, help='why it matters to the founder / what concept it teaches')
    ln.add_argument('--what', help='the short explanation or the question')
    ln.add_argument('--research', help='what to research (required for --kind research)')
    ln.add_argument('--thread', type=int, choices=(1, 2, 3))
    ln.add_argument('--task', help='task / row id')
    ln.add_argument('--link', help='file path to read')
    lg = sub.add_parser('learning', help='(founder) list learn/read/review/research items')
    lg.add_argument('--all', action='store_true')
    dn = sub.add_parser('done', help='(founder) mark a learn/review/research item done')
    dn.add_argument('id')
    dn.add_argument('--note')
    ro = sub.add_parser('rotate', help='archive old channel rounds verbatim (C17)')
    ro.add_argument('--thread', type=int, choices=[1, 2, 3])
    ro.add_argument('--keep', type=int, default=5)
    ro.add_argument('--dry-run', action='store_true')
    d = sub.add_parser('decisions')
    d.add_argument('--all', action='store_true')
    an = sub.add_parser('answer', help='(founder) answer an open decision')
    an.add_argument('id')
    an.add_argument('--message', required=True)
    ds = sub.add_parser('dismiss', help='(founder) close a decision without sending anything')
    ds.add_argument('id')
    a = p.parse_args(argv)
    handler = {'start': cmd_start, 'pause': cmd_pause, 'continue': cmd_continue, 'resume': cmd_continue,
               'close': cmd_close, 'stop': cmd_close, 'restart': cmd_restart, 'status': cmd_status,
               'wake': cmd_wake, 'tell': cmd_tell, 'header': cmd_header, 'watch': cmd_watch,
               'ask': cmd_ask, 'rotate': cmd_rotate, 'decisions': cmd_decisions, 'learn': cmd_learn,
               'learning': cmd_learning, 'done': cmd_done, 'answer': cmd_answer, 'dismiss': cmd_dismiss}[a.cmd]
    return handler(a)


if __name__ == '__main__':
    sys.exit(main())
