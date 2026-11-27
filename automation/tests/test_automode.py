import argparse
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import automode  # noqa: E402


class AutomodeTest(unittest.TestCase):
    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.wave_path = tmp / 'wave.json'
        self.cfg_path = tmp / 'owner_wake.json'
        deadline = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)).isoformat()
        self.wave = {'wave_id': 'W-T', 'status': 'active', 'verified_by_architect': True,
                     'operating_deadline_utc': deadline, 'sprints': []}
        self.wave_path.write_text(json.dumps(self.wave))
        self.cfg_path.write_text(json.dumps({'enabled': False, 'wave_id': 'W-OLD', 'expires_utc': 'x'}))
        self.running = set()
        self.calls = []
        self.patches = [
            patch.object(automode._wave, 'load', lambda: json.loads(self.wave_path.read_text())),
            patch.object(automode._wave, 'save', lambda w: self.wave_path.write_text(json.dumps(w))),
            patch.object(automode.relay, 'CONFIG', self.cfg_path),
            patch.object(automode.relay, 'load_config', lambda: json.loads(self.cfg_path.read_text())),
            patch.object(automode.relay, 'tick', lambda **kw: {'state': 'active', 'owners': []}),
            patch.object(automode.runtime, 'start_one', self.start_one),
            patch.object(automode.runtime, 'stop_one', self.stop_one),
            patch.object(automode.runtime, '_running_pid', lambda name: 99 if name in self.running else None),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def start_one(self, spec, armed, interval, delivery_only=False):
        self.assertFalse(armed)  # automode never arms live actor launch
        if spec['name'] != 'owner_wake':
            self.assertTrue(delivery_only)
        self.running.add(spec['name'])
        self.calls.append(('start', spec['name']))
        return {'name': spec['name'], 'action': 'started', 'pid': 99}

    def stop_one(self, name):
        self.running.discard(name)
        self.calls.append(('stop', name))
        return {'name': name, 'action': 'stopped'}

    def cfg(self):
        return json.loads(self.cfg_path.read_text())

    def args(self, **kw):
        return argparse.Namespace(complete_wave=False, owner=None, **kw)

    def test_start_pins_relay_to_wave_and_starts_three_processes(self):
        automode.cmd_start(self.args())
        cfg = self.cfg()
        self.assertEqual((cfg['enabled'], cfg['wave_id'], cfg['expires_utc']),
                         (True, 'W-T', self.wave['operating_deadline_utc']))
        self.assertEqual(self.running, {'owner_wake', 'architect_bridge', 'coordinator_trigger'})
        self.assertEqual(automode.state_word(), 'RUNNING')

    def test_start_refuses_unverified_paused_or_expired_wave(self):
        for change in ({'verified_by_architect': False}, {'status': 'paused'},
                       {'operating_deadline_utc': (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)).isoformat()}):
            self.wave_path.write_text(json.dumps(dict(self.wave, **change)))
            with self.assertRaises(SystemExit):
                automode.cmd_start(self.args())
        self.assertEqual(self.running, set())

    def test_pause_then_continue(self):
        automode.cmd_start(self.args())
        automode.cmd_pause(self.args())
        self.assertEqual(json.loads(self.wave_path.read_text())['status'], 'paused')
        self.assertFalse(self.cfg()['enabled'])
        self.assertEqual(automode.state_word(), 'PAUSED')
        automode.cmd_continue(self.args())
        self.assertEqual(json.loads(self.wave_path.read_text())['status'], 'active')
        self.assertTrue(self.cfg()['enabled'])
        self.assertEqual(automode.state_word(), 'RUNNING')

    def test_close_keeps_wave_unless_complete_requested(self):
        automode.cmd_start(self.args())
        automode.cmd_close(self.args())
        self.assertEqual((self.running, automode.state_word()), (set(), 'CLOSED'))
        self.assertEqual(json.loads(self.wave_path.read_text())['status'], 'active')
        automode.cmd_close(argparse.Namespace(complete_wave=True))
        self.assertEqual(json.loads(self.wave_path.read_text())['status'], 'complete')
        with self.assertRaises(SystemExit):
            automode.cmd_continue(self.args())

    def test_restart_stops_then_starts(self):
        automode.cmd_restart(self.args())
        names = [c[0] for c in self.calls]
        self.assertLess(names.index('stop'), names.index('start'))
        self.assertEqual(automode.state_word(), 'RUNNING')


if __name__ == '__main__':
    unittest.main()
