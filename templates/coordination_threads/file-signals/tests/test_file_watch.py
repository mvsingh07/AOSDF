"""Isolated notification contract checks; no model/application process is launched."""
import datetime as dt
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parents[1] / 'file_watch.py'

class FileSignalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.state = self.root / 'runtime'
        self.source = self.root / 'control.md'
        self.source.write_text('baseline')
        self.processes = []

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
            process.communicate(timeout=3)
        self.temp.cleanup()

    def argv(self, mode='wait', paths=None, timeout=.25, until=None, actor='coordinator3'):
        deadline = until or (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=20)).isoformat()
        args = [sys.executable, str(HELPER), '--root', str(self.root), '--actor', actor,
                '--state-dir', str(self.state), '--mode', mode, '--interval', '.05',
                '--timeout', str(timeout), '--until', deadline]
        for path in paths or ['control.md']:
            args += ['--path', path]
        return args

    def start(self, **kwargs):
        process = subprocess.Popen(self.argv(**kwargs), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.processes.append(process)
        return process

    def ready(self, receiver=False):
        name = 'coordinator3.receive.status.json' if receiver else 'coordinator3.status.json'
        stop = time.monotonic() + 3
        while time.monotonic() < stop:
            if (self.state / name).exists():
                return
            time.sleep(.01)
        self.fail('helper failed to initialize')

    def result(self, process):
        output, error = process.communicate(timeout=4)
        return process.returncode, [json.loads(line) for line in output.splitlines()], error

    def test_baseline_emits_no_change(self):
        code, events, _ = self.result(self.start())
        self.assertEqual(code, 2)
        self.assertEqual([e['event'] for e in events], ['timeout'])

    def test_change_is_observed(self):
        process = self.start(timeout=2); self.ready(); self.source.write_text('changed')
        code, events, _ = self.result(process)
        self.assertEqual(code, 0)
        self.assertEqual(events[0]['paths'], ['control.md'])
        self.assertEqual(events[0]['authority'], 'notification-only')

    def test_unchanged_bytes_do_not_deliver(self):
        process = self.start(); self.ready(); self.source.write_text('baseline')
        self.assertEqual(self.result(process)[1][0]['event'], 'timeout')

    def test_restart_uses_persisted_cursor(self):
        self.result(self.start())
        self.source.write_text('offline-change')
        code, events, _ = self.result(self.start())
        self.assertEqual(code, 0)
        self.assertEqual(events[0]['event'], 'changed')

    def test_deadline_is_bounded(self):
        before = time.monotonic()
        code, events, _ = self.result(self.start(timeout=20, until='2000-01-01T00:00:00Z'))
        self.assertEqual(code, 2)
        self.assertEqual(events[0]['event'], 'deadline')
        self.assertLess(time.monotonic() - before, 2)

    def test_observer_lock_is_exclusive(self):
        self.start(mode='watch', timeout=2); self.ready()
        code, events, _ = self.result(self.start(mode='watch'))
        self.assertEqual(code, 3)
        self.assertEqual(events[0]['event'], 'already-running')

    def test_receiver_lock_is_exclusive(self):
        self.start(mode='receive', timeout=2); self.ready(receiver=True)
        self.assertEqual(self.result(self.start(mode='receive'))[0], 3)

    def test_receive_with_running_observer(self):
        self.start(mode='watch', timeout=2); self.ready()
        receiver = self.start(mode='receive', timeout=2); self.ready(receiver=True)
        self.source.write_text('changed')
        code, events, _ = self.result(receiver)
        self.assertEqual(code, 0)
        self.assertIn('control.md', events[0]['paths'])

    def test_fast_changes_aggregate_paths(self):
        other = self.root / 'other.md'; other.write_text('baseline')
        self.start(mode='watch', paths=['control.md', 'other.md'], timeout=2); self.ready()
        self.source.write_text('new'); other.write_text('new')
        time.sleep(.16)
        self.source.write_text('latest')
        time.sleep(.16)
        code, events, _ = self.result(self.start(mode='receive', paths=['control.md', 'other.md']))
        self.assertEqual(code, 0)
        self.assertEqual(events[0]['paths'], ['control.md', 'other.md'])
        self.assertNotIn('latest', json.dumps(events))

    def test_workspace_escape_refused(self):
        code, _, error = self.result(self.start(paths=['../outside.md']))
        self.assertEqual(code, 1); self.assertIn('escapes workspace', error)

    def test_credential_paths_refused(self):
        code, _, error = self.result(self.start(paths=['.env']))
        self.assertEqual(code, 1); self.assertIn('credential-bearing', error)

    def test_symlink_and_ancestor_refused(self):
        (self.root / 'link.md').symlink_to(self.source)
        self.assertEqual(self.result(self.start(paths=['link.md']))[0], 1)
        folder = self.root / 'folder'; folder.mkdir(); (folder / 'a.md').write_text('data')
        (self.root / 'alias').symlink_to(folder, target_is_directory=True)
        self.assertEqual(self.result(self.start(paths=['alias/a.md']))[0], 1)

    def test_sigterm_releases_lock_and_records_stop(self):
        process = self.start(mode='watch', timeout=2); self.ready(); process.terminate()
        self.assertEqual(self.result(process)[0], 0)
        self.assertEqual(json.loads((self.state / 'coordinator3.status.json').read_text())['state'], 'stopped')
        self.assertEqual(self.result(self.start())[0], 2)

    def test_invalid_actor_refused(self):
        self.assertEqual(self.result(self.start(actor='../foreign'))[0], 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
