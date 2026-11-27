"""Standalone-clone path and inactive-adoption regressions, with no native sessions."""
from pathlib import Path
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import layout
import channel_delivery
import owner_wake
import owner_sessions
import supervisor
import automode


class PortableLayoutTests(unittest.TestCase):
    def test_all_transports_share_the_consolidated_thread_root(self):
        self.assertEqual(layout.THREADS, layout.HERE / 'coordination-threads')
        self.assertEqual(channel_delivery.ARTIFACT_ROOT, layout.THREADS)
        self.assertEqual(owner_wake.THREADS_DIR, layout.THREADS)

    def test_project_root_is_explicit_and_not_a_fixed_private_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, AOSDF_PROJECT_ROOT=directory, PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([sys.executable, '-c',
                'import sys; sys.path.insert(0,sys.argv[1]); import layout; print(layout.PROJECT_ROOT)',
                str(layout.HERE)], capture_output=True, text=True, check=True, env=env)
            self.assertEqual(Path(result.stdout.strip()), Path(directory).resolve())

    def test_disabled_example_cannot_consult_or_start_a_wave(self):
        config = json.loads((layout.HERE/'config/owner_wake.example.json').read_text())
        self.assertFalse(config['enabled'])
        self.assertFalse(config['claude_bg_resume'])
        self.assertEqual(config['owners'], [])
        with patch.object(owner_wake._wave, 'active_wave', side_effect=AssertionError('must remain inactive')):
            with self.assertRaisesRegex(ValueError, 'disabled'):
                owner_wake.envelope(config)

    def test_generic_supervisor_does_not_inherit_a_product_pilot_grant(self):
        self.assertFalse(hasattr(supervisor, 'PILOT'))

    def test_controller_status_uses_the_shared_mode_word(self):
        output = io.StringIO()
        with patch.object(automode._d, 'runtime_mode', return_value={'mode':'MANUAL'}), \
             patch.object(automode, 'state_word', return_value='CLOSED'), \
             patch.object(automode._wave, 'load', return_value=None), \
             patch.object(automode.runtime, '_running_pid', return_value=None), \
             patch.object(automode.relay, 'load_config', side_effect=FileNotFoundError('inactive')), \
             contextlib.redirect_stdout(output):
            automode.cmd_status(None)
        self.assertIn('Process Mode: MANUAL', output.getvalue())
        self.assertIn('CLOSED', output.getvalue())
