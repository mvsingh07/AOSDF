import datetime as dt
import json
import time
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import owner_wake as ow  # noqa: E402

REPO = ow.owners.REPO
WAVE_ID = 'W-TEST'


def wave(deadline_hours=2, verified=True):
    now = dt.datetime.now(dt.timezone.utc)
    return {'wave_id': WAVE_ID, 'status': 'active', 'verified_by_architect': verified,
            'created_utc': (now - dt.timedelta(hours=1)).isoformat(),
            'operating_deadline_utc': (now + dt.timedelta(hours=deadline_hours)).isoformat(), 'sprints': []}


RECORD = {'state': 'bound', 'executor': 'codex', 'binding_id': '072cd04e-f69d-4844-a870-84c6a20ba7d4',
          'session_id': '01a20822-88fe-7860-8fda-d2e5619eed73', 'thread': 1, 'pid': 1, 'process_fingerprint': 'x'}


class FakeControl:
    status = 'idle'
    fail_turn = False
    refuse = False
    turns = []

    def __init__(self, endpoint, owner, timeout):
        if FakeControl.refuse:
            raise ValueError('control peer PID/fingerprint mismatch')
        self.owner = owner

    def rpc(self, method, params, ident):
        if method == 'initialize':
            return {}
        if method == 'thread/read':
            return {'thread': {'id': self.owner['session_id'], 'cwd': str(REPO), 'status': {'type': FakeControl.status}}}
        if method == 'turn/start':
            if FakeControl.fail_turn:
                raise ConnectionError('reply lost')
            FakeControl.turns.append(params['input'][0]['text'])
            return {'turn': {'id': f'turn-{len(FakeControl.turns)}'}}
        raise AssertionError(method)

    def send(self, message):
        pass

    def close(self):
        pass


class FakeRunner:
    def __init__(self):
        self.calls = []
        self.agents = []
        self.returncode = 0

    def __call__(self, argv, **kw):
        self.calls.append((argv, kw))
        if argv[1:3] == ['agents', '--json']:
            return subprocess.CompletedProcess(argv, 0, json.dumps(self.agents), '')
        return subprocess.CompletedProcess(argv, self.returncode, 'ok', 'boom' if self.returncode else '')


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg_path = self.tmp / 'owner_wake.json'
        self.cfg = {'schema_version': 1, 'enabled': True, 'communication_only': True, 'wave_id': WAVE_ID,
                    'founder_auth_ref': 'test', 'socket_link': str(self.tmp / 'sock'),
                    'expires_utc': (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat(),
                    'owners': ['coordinator1'], 'max_wakes_per_owner': 2, 'min_gap_seconds': 30,
                    'codex_home': str(self.tmp / 'codex-home')}
        self.write_cfg()
        FakeControl.status, FakeControl.fail_turn, FakeControl.refuse, FakeControl.turns = 'idle', False, False, []
        self.runner = FakeRunner()
        self.record = dict(RECORD)
        self.inputs = [('k1', 'automation/var/delivery/peer/thread1/a.json')]
        self.wave = wave()
        self.patches = [
            patch.object(ow, 'WAKE_ROOT', self.tmp / 'wake'),
            patch.object(ow.delivery, 'safe_path', lambda root, path: Path(path)),
            patch.object(ow._wave, 'active_wave', lambda: self.wave),
            patch.object(ow, 'binding_for', lambda role: dict(self.record) if self.record else None),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def write_cfg(self):
        self.cfg_path.write_text(json.dumps(self.cfg))

    def tick(self, **kw):
        result = ow.tick(control_cls=FakeControl, runner=self.runner, config_path=self.cfg_path,
                         inputs_fn=lambda role, record, current: list(self.inputs), **kw)
        return result['owners'][0] if result['state'] == 'active' else result

    def age_last_submission(self, seconds):
        path = self.tmp / 'wake' / RECORD['binding_id'] / 'state.json'
        state = json.loads(path.read_text())
        state['submissions'][-1]['utc'] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=seconds)).isoformat()
        path.write_text(json.dumps(state))


class SafetyTest(Base):
    def test_idle_owner_woken_once_per_input(self):
        first = self.tick()
        self.assertEqual((first['state'], first['adapter'], first['turn_id']), ('submitted', 'codex-app', 'turn-1'))
        self.assertEqual(self.tick()['state'], 'no-new-input')
        self.assertEqual(len(FakeControl.turns), 1)
        self.assertLessEqual(len(FakeControl.turns[0].encode()), ow.MAX_PROMPT_BYTES)

    def test_new_input_respects_min_gap(self):
        self.tick()
        self.inputs = [('k2', 'b')]
        self.assertEqual(self.tick()['state'], 'min-gap-wait')
        self.age_last_submission(60)
        self.assertEqual(self.tick()['state'], 'submitted')

    def test_busy_owner_not_interrupted_or_reserved(self):
        FakeControl.status = 'active'
        self.assertEqual(self.tick()['state'], 'owner-busy')
        FakeControl.status = 'idle'
        self.assertEqual(self.tick()['state'], 'submitted')

    def test_budget_exhausted(self):
        for n in range(2):
            self.inputs = [(f'k{n}', 'x')]
            self.assertEqual(self.tick()['state'], 'submitted')
            self.age_last_submission(60)
        self.inputs = [('k9', 'x')]
        self.assertEqual(self.tick()['state'], 'budget-exhausted')

    def test_lost_reply_never_resends(self):
        FakeControl.fail_turn = True
        self.assertEqual(self.tick()['state'], 'submit-uncertain')
        FakeControl.fail_turn = False
        self.age_last_submission(60)
        self.assertEqual(self.tick()['state'], 'no-new-input')

    def test_inactive_when_disabled_expired_unverified_or_other_wave(self):
        for change in ({'enabled': False}, {'wave_id': 'W-OTHER'},
                       {'expires_utc': (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()}):
            cfg = dict(self.cfg, **change)
            self.cfg_path.write_text(json.dumps(cfg))
            self.assertEqual(self.tick()['state'], 'inactive')
        self.write_cfg()
        self.wave = wave(verified=False)
        self.assertEqual(self.tick()['state'], 'inactive')
        self.wave = wave(deadline_hours=-1)
        self.assertEqual(self.tick()['state'], 'inactive')
        self.assertEqual(FakeControl.turns, [])

    def test_unbound_owner_skipped(self):
        self.record = None
        self.assertEqual(self.tick()['state'], 'skip-no-bound-owner')

    def test_dry_run_sends_nothing(self):
        self.assertEqual(self.tick(dry_run=True)['state'], 'would-wake')
        self.assertEqual((FakeControl.turns, self.runner.calls), ([], []))

    def test_prompt_bounded_with_many_long_labels(self):
        labels = ['x' * 200 + str(n) for n in range(10)]
        for role in ('coordinator1', 'architect'):
            prompt = ow.build_prompt(role, RECORD, WAVE_ID, labels)
            self.assertLessEqual(len(prompt.encode()), ow.MAX_PROMPT_BYTES)
            self.assertIn('more)', prompt)

    def test_config_validation(self):
        for bad in ({'communication_only': False}, {'owners': ['worker1']}, {'max_wakes_per_owner': 0},
                    {'min_gap_seconds': 1}, {'adapters': {'architect': 'telepathy'}}, {'claude_bg_resume': 'yes'}):
            self.cfg_path.write_text(json.dumps(dict(self.cfg, **bad)))
            with self.assertRaises(ValueError):
                ow.load_config(self.cfg_path)


class AdapterTest(Base):
    def test_codex_terminal_session_falls_back_to_queue(self):
        FakeControl.refuse = True  # socket peer is the app-server, not this owner's terminal process
        result = self.tick()
        self.assertEqual((result['adapter'], result['state']), ('codex-queue', 'queued'))
        argv, kw = self.runner.calls[-1]
        self.assertEqual(argv[1:4], ['queue', '--thread', RECORD['session_id']])
        self.assertEqual(kw['env']['CODEX_HOME'], self.cfg['codex_home'])
        self.assertEqual(self.tick()['state'], 'no-new-input')

    def test_forced_queue_adapter_and_pending_queue_item_not_duplicated(self):
        self.cfg['adapters'] = {'coordinator1': 'codex-queue'}
        self.write_cfg()
        home = Path(self.cfg['codex_home'])
        home.mkdir()
        import sqlite3
        con = sqlite3.connect(home / 'queue_1.sqlite')
        con.execute('create table queued_items (id text, thread_id text, payload_json text, queue_order int,'
                    ' created_at_ms int, updated_at_ms int)')
        con.execute("insert into queued_items values ('q', ?, '{}', 1, 0, 0)", (RECORD['session_id'],))
        con.commit()
        con.close()
        self.assertEqual(self.tick()['state'], 'already-queued')
        self.assertEqual(self.runner.calls, [])

    def test_queue_failure_reported_and_not_resent(self):
        FakeControl.refuse = True
        self.runner.returncode = 1
        self.assertEqual(self.tick()['state'], 'queue-failed')
        self.runner.returncode = 0
        self.age_last_submission(60)
        self.assertEqual(self.tick()['state'], 'no-new-input')

    def test_claude_running_uses_native_wait_and_busy_defers(self):
        self.record = dict(RECORD, executor='claude')
        self.runner.agents = [{'sessionId': RECORD['session_id'], 'status': 'idle'}]
        self.assertEqual(self.tick()['state'], 'claude-running-use-native-wait')
        self.runner.agents = [{'sessionId': RECORD['session_id'], 'status': 'busy'}]
        self.assertEqual(self.tick()['state'], 'owner-busy')
        self.assertFalse(any('--resume' in c[0] for c in self.runner.calls))

    def test_claude_stopped_resume_only_when_enabled(self):
        self.record = dict(RECORD, executor='claude')
        self.assertEqual(self.tick()['state'], 'claude-stopped-resume-disabled')
        self.cfg['claude_bg_resume'] = True
        self.write_cfg()
        result = self.tick()
        self.assertEqual((result['adapter'], result['state']), ('claude', 'resumed-background'))
        argv = self.runner.calls[-1][0]
        self.assertEqual(argv[1:4], ['--bg', '--resume', RECORD['session_id']])


class ChannelInputTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / 'mail' / 'coordinator' / 'thread1').mkdir(parents=True)
        self.latest = {}
        self.patches = [patch.object(ow, 'latest_round', lambda n: self.latest.get(n)),
                        patch.object(ow.delivery, 'MAILBOX_ROOT', self.tmp / 'mail')]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def test_architect_owed_round_found_even_without_valid_notification(self):
        self.latest = {3: {'round': 34, 'status': 'AWAITING-ARCHITECT', 'wave_id': WAVE_ID},
                       1: {'round': 86, 'status': 'ALIGNED', 'wave_id': WAVE_ID},
                       2: {'round': 9, 'status': 'AWAITING-ARCHITECT', 'wave_id': 'W-OLD'}}
        found = ow.channel_inputs('architect', wave())
        self.assertEqual([label for _, label in found], ['coordinator-architect/thread3.md Round 34 AWAITING-ARCHITECT'])

    def test_coordinator_round_skipped_once_read_acked(self):
        self.latest = {1: {'round': 86, 'status': 'ALIGNED', 'wave_id': WAVE_ID}}
        self.assertEqual(len(ow.channel_inputs('coordinator1', wave())), 1)
        event = self.tmp / 'mail' / 'coordinator' / 'thread1' / 'e.json'
        event.write_text(json.dumps({'round': 86}))
        event.with_suffix('.read.json').write_text('{}')
        self.assertEqual(ow.channel_inputs('coordinator1', wave()), [])


    def test_unmarked_round_inherits_prior_wave_and_still_wakes(self):
        chan = self.tmp / 'chan'
        chan.mkdir()
        (chan / 'thread3.md').write_text(
            f'<!-- round:35 checkpoint:assignment status:ALIGNED wave:{WAVE_ID} scope:{"a"*64} -->\n'
            '<!-- round:36 checkpoint:sprint-completion status:ALIGNED -->\n')
        for p in reversed(self.patches):
            p.stop()
        self.patches = [patch.object(ow, 'CHANNEL_DIR', chan),
                        patch.object(ow.delivery, 'MAILBOX_ROOT', self.tmp / 'mail')]
        for p in self.patches:
            p.start()
        latest = ow.latest_round(3)
        self.assertEqual((latest['round'], latest['wave_id'], latest['wave_inferred']), (36, WAVE_ID, True))
        (label,) = [l for _, l in ow.channel_inputs('coordinator3', wave())]
        self.assertIn('Round 36 ALIGNED', label)
        self.assertIn('lacks wave:/scope:', label)

    def test_founder_notice_reaches_only_named_owners_once(self):
        with patch.object(ow, 'NOTICE_ROOT', self.tmp / 'notices'):
            ow.post_notice(['coordinator3', 'architect'], 'Use  the header\ncommand.', WAVE_ID)
            ow.post_notice(['coordinator3'], 'old wave', 'W-OLD')
            labels = [l for _, l in ow.notice_inputs('coordinator3', wave())]
            self.assertEqual(labels, ['FOUNDER NOTICE: Use the header command.'])
            self.assertEqual(ow.notice_inputs('coordinator1', wave()), [])
            with self.assertRaises(ValueError):
                ow.post_notice(['coordinator9'], 'x', WAVE_ID)
            with self.assertRaises(ValueError):
                ow.post_notice(['architect'], 'x' * 401, WAVE_ID)

    def test_prompt_carries_strict_header_rule(self):
        prompt = ow.build_prompt('coordinator3', {'thread': 3, 'binding_id': 'e765f776-x'}, WAVE_ID, ['FOUNDER NOTICE: ' + 'y' * 400])
        self.assertIn(f'wave:{WAVE_ID} scope:', prompt)
        self.assertIn('automode.py header', prompt)
        self.assertIn('supervisor.py --assign', prompt)
        self.assertLessEqual(len(prompt.encode()), ow.MAX_PROMPT_BYTES)

class DrainedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.marker = self.tmp / 'activity'
        self.marker.write_text('x')
        self.latest = {n: {'round': 10 + n, 'status': 'ALIGNED', 'wave_id': WAVE_ID} for n in (1, 2, 3)}
        self.busy, self.pending = [], []
        self.patches = [patch.object(ow, 'latest_round', lambda n: self.latest[n]),
                        patch.object(ow, 'busy_workers', lambda: self.busy),
                        patch.object(ow, 'binding_for', lambda role: {'binding_id': 'b-' + role}),
                        patch.object(ow, 'owner_inputs', lambda role, rec, cur: self.pending),
                        patch.object(ow, 'WAKE_ROOT', self.tmp / 'wake'),
                        patch.object(ow, 'activity_paths', lambda: [self.marker])]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def age(self, seconds):
        t = time.time() - seconds
        os.utime(self.marker, (t, t))

    def test_quiet_and_drained_wakes_sa_once_per_quiet_period(self):
        self.age(1000)
        first = ow.drained_input(wave(), 900)
        self.assertEqual(len(first), 1)
        self.assertIn('ALL THREADS DRAINED', first[0][1])
        self.assertEqual(ow.drained_input(wave(), 900)[0][0], first[0][0])  # same period, same key
        self.age(950)
        self.assertNotEqual(ow.drained_input(wave(), 900)[0][0], first[0][0])  # new activity -> new period

    def test_not_drained_when_recent_busy_owed_or_awaiting(self):
        self.age(100)
        self.assertEqual(ow.drained_input(wave(), 900), [])
        self.age(1000)
        self.busy = ['agent1-1:running']
        self.assertEqual(ow.drained_input(wave(), 900), [])
        self.busy, self.pending = [], [('k', 'peer message')]
        self.assertEqual(ow.drained_input(wave(), 900), [])
        self.pending = []
        self.latest[2] = {'round': 5, 'status': 'AWAITING-ARCHITECT', 'wave_id': WAVE_ID}
        self.assertEqual(ow.drained_input(wave(), 900), [])

class TailAfterVerdictTest(unittest.TestCase):
    HEAD = ('<!-- round:92 checkpoint:assignment status:ALIGNED opened:2026-11-24T15:20:15+00:00 '
            f'wave:{WAVE_ID} scope:abc binding:b -->\n\n### ARCHITECT\n\ngo\n\n'
            '<!-- verdict:ALIGNED by:solution-architect at:2026-11-24T15:20:15+00:00 -->\n')

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / 'thread1.md').write_text(self.HEAD)
        self.patches = [patch.object(ow, 'CHANNEL_DIR', self.tmp),
                        patch.object(ow, 'latest_round', lambda n: {'round': 92, 'status': 'ALIGNED', 'wave_id': WAVE_ID}
                                     if n == 1 else None)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def write(self, extra, age):
        path = self.tmp / 'thread1.md'
        path.write_text(self.HEAD + extra)
        t = time.time() - age
        os.utime(path, (t, t))

    def test_tail_after_verdict_wakes_sa_once_per_tail(self):
        self.write('', 1000)
        self.assertEqual(ow.tail_after_verdict_input(wave(), 300, busy=[]), [])  # nothing appended
        self.write('\n### Round 92 D135 intake\n\nPlease reconcile.\n', 1000)
        first = ow.tail_after_verdict_input(wave(), 300, busy=[])
        self.assertEqual(len(first), 1)
        self.assertIn('Round 92 D135 intake', first[0][1])
        self.assertEqual(ow.tail_after_verdict_input(wave(), 300, busy=[])[0][0], first[0][0])
        self.write('\n### Round 92 D135 intake\n\nPlease reconcile. More.\n', 1000)
        self.assertNotEqual(ow.tail_after_verdict_input(wave(), 300, busy=[])[0][0], first[0][0])

    def test_tail_waits_for_quiet_and_idle_worker(self):
        self.write('\n### COORDINATOR ACK\n\nRead-ACKed.\n\n### Round 92 launch\n\nlaunched\n', 1000)
        self.assertEqual(ow.tail_after_verdict_input(wave(), 300, busy=[]), [])  # bookkeeping only
        self.write('\n### Round 92 intake\n', 100)
        self.assertEqual(ow.tail_after_verdict_input(wave(), 300, busy=[]), [])
        self.write('\n### Round 92 intake\n', 1000)
        self.assertEqual(ow.tail_after_verdict_input(wave(), 300, busy=['agent1-2:running']), [])
        self.assertEqual(len(ow.tail_after_verdict_input(wave(), 300, busy=['agent2-1:running'])), 1)


if __name__ == '__main__':
    unittest.main()
