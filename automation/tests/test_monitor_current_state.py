import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('coord_monitor', Path(__file__).parents[1] / 'monitor.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MonitorCurrentState(unittest.TestCase):
    def test_current_executor_and_single_thread_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for t in (1, 2):
                folder = root / f'thread{t}' / f'agent{t}-1'
                folder.mkdir(parents=True)
                (folder / 'task.md').write_text('current task')
                (folder / 'state.json').write_text(json.dumps({
                    'model': 'codex', 'status': 'completed',
                    'task_digest': m._digest('current task'),
                    'owned_write_targets': ['current/path'],
                }))
            config = root / 'config.json'
            config.write_text(json.dumps({'coordination_root': '.', 'active_threads': [1],
                'threads': [{'thread': t, 'agents': [{'agent': f'agent{t}-1',
                    'model': 'claude', 'owned_write_targets': ['old/path']}]} for t in (1, 2)]}))
            cfg, coord, agents = m.scan(config)
            self.assertEqual(agents[0]['model'], 'codex')
            self.assertEqual(agents[0]['owned'], ['current/path'])
            report, _, _ = m.report(cfg, coord, agents, {}, config)
            self.assertIn('agent1-1   1    codex', report)   # model override shown in the row
            self.assertNotIn('agent2-1   2', report)         # out-of-scope agent is not a table row
            self.assertIn('OUT OF SCOPE', report)
            self.assertIn('agent2-1', report)                # listed under the out-of-scope section

    def test_changes_only_signature_ignores_heading_time_but_tracks_status(self):
        config = {"active_threads": [1]}
        agents = [{"agent": "agent1-1", "model": "claude", "state_status": "running"}]
        first = m.display_signature(config, agents, {})
        self.assertEqual(first, m.display_signature(config, agents, {}))
        agents[0]["state_status"] = "blocked"
        self.assertNotEqual(first, m.display_signature(config, agents, {}))
        second = m.display_signature(config, agents, {})
        agents[0]["model"] = "codex"
        self.assertNotEqual(second, m.display_signature(config, agents, {}))



if __name__ == '__main__':
    unittest.main()
