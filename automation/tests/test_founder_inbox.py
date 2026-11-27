"""Founder decision inbox: ask, auto-detect ESCALATE/founder HOLD, notify once, remind, answer -> notice."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import founder_inbox as fi  # noqa: E402
import owner_wake as ow  # noqa: E402

WAVE = 'W-TEST'


def header(rnd, status):
    return f'<!-- round:{rnd} checkpoint:assignment status:{status} opened:2026-11-25T00:00:00+00:00 wave:{WAVE} scope:a binding:b -->\n'


class InboxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.calls = []
        self.runner = lambda cmd, **kw: self.calls.append(cmd)
        self.latest = {}
        self.table = self.tmp / 'human-actions.md'
        self.table.write_text('# Human actions\n\n' + fi.TABLE_BEGIN + '\n' + fi.TABLE_END + '\n\nfooter\n')
        self.patches = [patch.object(fi, 'INBOX', self.tmp / 'founder'),
                        patch.object(fi, 'HUMAN_ACTIONS', self.table),
                        patch.object(ow, 'NOTICE_ROOT', self.tmp / 'notices'),
                        patch.object(ow, 'CHANNEL_DIR', self.tmp),
                        patch.object(ow, 'latest_round', lambda n: self.latest.get(n)),
                        patch.object(fi.shutil, 'which', lambda name: '/usr/bin/osascript')]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def test_ask_notifies_once_and_answer_sends_notice(self):
        rec, new = fi.ask('coordinator1', 'Approve the R89 offline preflight?', thread=1,
                          options='A: approve | B: hold', recommendation='A', wave_id=WAVE, runner=self.runner)
        self.assertTrue(new)
        self.assertEqual(len(self.calls), 1)
        self.assertIn('osascript', self.calls[0][0])
        again, new2 = fi.ask('coordinator1', 'Approve the R89 offline preflight?', thread=1, wave_id=WAVE, runner=self.runner)
        self.assertFalse(new2)
        self.assertEqual(again['id'], rec['id'])
        self.assertEqual(len(self.calls), 1)  # no duplicate notification
        self.assertEqual([r['id'] for r in fi.requests()], [rec['id']])
        done = fi.answer(rec['id'][:6], 'Approved: A.', WAVE)
        self.assertEqual(done['status'], 'answered')
        self.assertEqual(done['notified_roles'], ['architect', 'coordinator1'])
        self.assertEqual(fi.requests(), [])
        labels = [label for _, label in ow.notice_inputs('coordinator1', {'wave_id': WAVE})]
        self.assertTrue(any('FOUNDER DECISION on ' + rec['id'] in label for label in labels))
        with self.assertRaises(ValueError):
            fi.answer(rec['id'], 'again', WAVE)

    def test_ask_rejects_bad_role_or_empty_question(self):
        with self.assertRaises(ValueError):
            fi.ask('worker', 'Something long enough', runner=self.runner)
        with self.assertRaises(ValueError):
            fi.ask('architect', 'short', runner=self.runner)

    def test_scan_records_escalate_and_founder_hold_only_once(self):
        (self.tmp / 'thread1.md').write_text(header(90, 'ESCALATE') + '### ARCHITECT\n\nNeed the R89 preflight decision.\n')
        (self.tmp / 'thread2.md').write_text(header(57, 'HOLD') + 'Waiting on the T1 handoff.\n')
        (self.tmp / 'thread3.md').write_text(header(39, 'HOLD') + 'Blocked on the founder START gate.\n')
        self.latest = {1: {'round': 90, 'status': 'ESCALATE', 'wave_id': WAVE},
                       2: {'round': 57, 'status': 'HOLD', 'wave_id': WAVE},
                       3: {'round': 39, 'status': 'HOLD', 'wave_id': WAVE}}
        made = fi.scan_channels({'wave_id': WAVE}, runner=self.runner)
        self.assertEqual(sorted(r['thread'] for r in made), [1, 3])
        self.assertIn('R89 preflight', made[0]['question'] + made[1]['question'])
        self.assertEqual(fi.scan_channels({'wave_id': WAVE}, runner=self.runner), [])
        self.assertEqual(len(self.calls), 2)

    def test_reconcile_closes_moved_rounds_and_other_waves_and_skips_asked_rounds(self):
        (self.tmp / 'thread1.md').write_text(header(114, 'ESCALATE') + 'Need the founder.\n')
        self.latest = {1: {'round': 114, 'status': 'ESCALATE', 'wave_id': WAVE}}
        made = fi.scan_channels({'wave_id': WAVE}, runner=self.runner)
        old_wave, _ = fi.ask('architect', 'Something from the last wave', wave_id='W-OLD', runner=self.runner)
        self.assertEqual([r['id'] for r in fi.reconcile({'wave_id': WAVE})], [old_wave['id']])
        self.assertNotIn(old_wave['id'], [r['id'] for r in fi.requests()])
        self.assertIn(made[0]['id'], [r['id'] for r in fi.requests()])  # still the current round
        self.latest[1] = {'round': 115, 'status': 'ALIGNED', 'wave_id': WAVE}
        closed = fi.reconcile({'wave_id': WAVE})
        self.assertEqual([r['id'] for r in closed], [made[0]['id']])
        self.assertEqual(fi.requests(), [])
        # an owner who asked during the round suppresses the auto copy
        fi.ask('coordinator1', 'Authorize the D161 run?', thread=1, wave_id=WAVE, runner=self.runner)
        (self.tmp / 'thread1.md').write_text(header(116, 'ESCALATE') + 'Need the founder.\n')
        self.latest[1] = {'round': 116, 'status': 'ESCALATE', 'wave_id': WAVE}
        self.assertEqual(fi.scan_channels({'wave_id': WAVE}, runner=self.runner), [])

    def test_auto_records_are_not_reminded_and_dismiss_closes(self):
        (self.tmp / 'thread1.md').write_text(header(90, 'ESCALATE') + 'x\n')
        self.latest = {1: {'round': 90, 'status': 'ESCALATE', 'wave_id': WAVE}}
        rec = fi.scan_channels({'wave_id': WAVE}, runner=self.runner)[0]
        path = fi.INBOX / f"{rec['id']}.json"
        raw = fi._load(path)
        raw['last_notified_utc'] = '2026-01-01T00:00:00+00:00'
        ow._write_json(path, raw)
        self.assertEqual(fi.remind_open(3600, runner=self.runner), 0)
        fi.dismiss(rec['id'][:5])
        self.assertEqual(fi.requests(), [])

    def test_budget_low_then_exhausted_notifies_once_each_and_closes_when_raised(self):
        usage = {'coordinator1': (5, 12)}
        cfg = {'owners': ['coordinator1'], 'max_wakes_per_owner': 12}
        with patch.object(fi, '_wake_usage', lambda c, cur: dict(usage)):
            self.assertEqual(fi.budget_alerts(cfg, {'wave_id': WAVE}, runner=self.runner), [])
            usage['coordinator1'] = (10, 12)
            low = fi.budget_alerts(cfg, {'wave_id': WAVE}, runner=self.runner)
            self.assertEqual([r['budget_level'] for r in low], ['low'])
            self.assertIn('10/12', low[0]['question'])
            self.assertEqual(fi.budget_alerts(cfg, {'wave_id': WAVE}, runner=self.runner), [])
            self.assertEqual(len(self.calls), 1)
            usage['coordinator1'] = (12, 12)
            self.assertEqual([r['id'] for r in fi.reconcile({'wave_id': WAVE}, cfg)], [low[0]['id']])
            out = fi.budget_alerts(cfg, {'wave_id': WAVE}, runner=self.runner)
            self.assertEqual(out[0]['budget_level'], 'exhausted')
            self.assertEqual(len(self.calls), 2)
            self.assertEqual(fi.remind_open(0, runner=self.runner), 0)  # never re-notified hourly
            cfg['max_wakes_per_owner'] = 24
            usage['coordinator1'] = (12, 24)
            self.assertEqual([r['id'] for r in fi.reconcile({'wave_id': WAVE}, cfg)], [out[0]['id']])
            self.assertEqual(fi.requests(), [])

    def test_learn_items_are_non_blocking_tabled_and_closed_by_done(self):
        rec, new = fi.learn('coordinator1', 'learn', 'Idempotent reservation in GAP-387', thread=1, task='S2R-06-13',
                            why='Shows how at-most-once admission survives retries', what='Reserve before send',
                            link='03_System_Design/009_queue_worker_module/05_interfaces.md', wave_id=WAVE,
                            runner=self.runner)
        self.assertTrue(new)
        self.assertIn('work continues', self.calls[0][2])
        self.assertEqual(fi.requests(), [])  # not a decision: status/watch "decisions" stay empty
        self.assertEqual([r['id'] for r in fi.requests(learning=True)], [rec['id']])
        fi.ask('architect', 'Pick the cache eviction policy for tenant config', wave_id=WAVE,
               research='LRU vs TTL; Redis maxmemory-policy', runner=self.runner)
        fi.ask('architect', 'Authorize one bounded local run of D161', wave_id=WAVE, runner=self.runner)
        table = self.table.read_text()
        self.assertIn('Idempotent reservation in GAP-387', table)
        self.assertIn('research-decision', table)
        self.assertNotIn('D161', table)  # simple authorizations stay out of human-actions.md
        self.assertTrue(table.endswith('footer\n'))
        self.assertEqual(fi.remind_open(0, runner=self.runner), 2)  # both asks; the learn item is not reminded
        self.assertEqual(fi.reconcile({'wave_id': 'W-NEXT'})[0]['origin'], 'ask')
        self.assertEqual([r['id'] for r in fi.requests(learning=True)], [rec['id']])  # learn items outlive waves
        fi.done(rec['id'][:6])
        self.assertEqual(fi.requests(learning=True), [])
        self.assertIn('| done |', self.table.read_text())
        with self.assertRaises(ValueError):
            fi.learn('coordinator1', 'research', 'Something to research here', why='because it matters', runner=self.runner)

    def test_owner_error_alerts_once_and_closes_when_reachable(self):
        bad = [{'role': 'coordinator1', 'state': 'owner-error', 'status': 'systemError'}]
        made = fi.owner_health(bad, {'wave_id': WAVE}, runner=self.runner)
        self.assertEqual(len(made), 1)
        self.assertIn('STOPPED', self.calls[0][2])
        self.assertEqual(fi.owner_health(bad, {'wave_id': WAVE}, runner=self.runner), [])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(fi.remind_open(0, runner=self.runner), 0)
        fi.owner_health([{'role': 'coordinator1', 'state': 'submitted'}], {'wave_id': WAVE}, runner=self.runner)
        self.assertEqual(fi.requests(), [])

    def test_remind_open_hourly(self):
        rec, _ = fi.ask('architect', 'Pick the tenant for the demo', wave_id=WAVE, runner=self.runner)
        self.assertEqual(fi.remind_open(3600, runner=self.runner), 0)
        path = fi.INBOX / f"{rec['id']}.json"
        raw = fi._load(path)
        raw['last_notified_utc'] = '2026-01-01T00:00:00+00:00'
        ow._write_json(path, raw)
        self.assertEqual(fi.remind_open(3600, runner=self.runner), 1)
        self.assertEqual(fi.remind_open(3600, runner=self.runner), 0)


if __name__ == '__main__':
    unittest.main()
