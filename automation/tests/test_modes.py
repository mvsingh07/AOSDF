import importlib.util
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

MODES = Path(__file__).resolve().parent.parent / 'modes'
os.environ['MODE_DRY_RUN'] = '1'
sys.path.insert(0, str(MODES))
import _engine  # noqa: E402


def load(rel):
    spec = importlib.util.spec_from_file_location(rel.replace('/', '_'), MODES / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def commands(mod, argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = mod.main(argv)
    return code, [line[2:] for line in buf.getvalue().splitlines() if line.startswith('→ ')]


class ModeScriptsTest(unittest.TestCase):
    def setUp(self):
        _engine.DRY_RUN = True

    def test_ultimate_passes_through_to_automode(self):
        code, cmds = commands(load('ultimate-auto/ultimate_auto.py'), ['tell', '--to', 'all', '--message', 'x'])
        self.assertEqual((code, cmds), (0, ['python3 automation/automode.py tell --to all --message x']))
        self.assertEqual(commands(load('ultimate-auto/ultimate_auto.py'), ['bogus'])[0], 2)

    def test_semi_auto_maps_to_supervisor_and_sprint(self):
        mod = load('semi-auto/semi_auto.py')
        self.assertEqual(commands(mod, ['assign', 'agent1-1', '--preview'])[1],
                         ['python3 automation/supervisor.py --assign agent1-1 --preview'])
        self.assertEqual(commands(mod, ['sprint', '2'])[1], ['python3 automation/sprint.py --thread-folder thread2 show'])

    def test_manual_quiet_closes_relay_then_stops_all(self):
        self.assertEqual(commands(load('manual/manual.py'), ['quiet'])[1],
                         ['python3 automation/automode.py close', 'python3 automation/initiate_automation.py --stop'])

    def test_easy_uses_queue_only_watchers_and_refuses_beside_ultimate(self):
        mod = load('easy/easy.py')
        self.assertEqual(commands(mod, ['start'])[1], ['python3 automation/initiate_automation.py --start-delivery'])
        _engine.DRY_RUN = False
        with patch.object(_engine, 'running', lambda name: 1 if name == 'owner_wake' else None), \
                patch.object(_engine, 'run', side_effect=AssertionError('must not run')):
            with self.assertRaises(SystemExit):
                mod.main(['start'])

    def test_auto_arm_requires_explicit_authorization_flag(self):
        mod = load('auto/auto.py')
        with self.assertRaises(SystemExit):
            mod.main(['start-armed'])
        self.assertEqual(commands(mod, ['start-armed', '--i-have-founder-authorization'])[1],
                         ['python3 automation/initiate_automation.py --start --arm'])


if __name__ == '__main__':
    unittest.main()
