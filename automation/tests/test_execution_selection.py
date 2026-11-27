"""Engine selection must rebuild commands, preserve policy and report actual identity."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import visible_launch as visible
import supervisor
import coordinator_trigger as coordinator
import architect_invoke as architect


class ExecutionSelection(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in ('CLAUDE_PROFILE_DIR', 'CODEX_PROFILE_DIR', 'EXECUTOR_OVERRIDE'):
            p = patch.object(visible, name, None); p.start(); self.addCleanup(p.stop)

    def test_selection_inherits_or_changes_engine_without_foreign_model(self):
        self.assertEqual(visible.execution_choice('claude','opus'),('claude','opus'))
        self.assertEqual(visible.execution_choice('codex','codex-model'),('codex','codex-model'))
        for destination, requested, model in [('claude','codex','codex-model'),('codex','claude','opus')]:
            with patch.object(visible,'EXECUTOR_OVERRIDE',destination):
                self.assertEqual(visible.execution_choice(requested,model),(destination,None))
                with self.assertRaisesRegex(ValueError,'fresh session'):
                    visible.execution_choice(requested,model,resume='existing-id')
        with patch.object(visible,'EXECUTOR_OVERRIDE','typo'), self.assertRaisesRegex(ValueError,'must be'):
            visible.execution_choice('claude')

    def test_worker_claude_to_codex_rebuilds_command_and_selects_codex_profile(self):
        with patch.object(visible,'EXECUTOR_OVERRIDE','codex'), \
             patch.object(visible,'CODEX_PROFILE_DIR',self.root), \
             patch.object(visible.subprocess,'run') as opened:
            result=supervisor._visible_worker_launch({'agent':'agent1-2','thread':1,'model':'claude'},
                self.root,self.root/'worker',dry_run=True,model='opus')
        opened.assert_not_called()
        self.assertEqual(result['executor'],'codex');self.assertEqual(result['requested_executor'],'claude')
        self.assertEqual(result['command'][0],'codex');self.assertIn('--yolo',result['command'])
        self.assertNotIn('--dangerously-skip-permissions',result['command']);self.assertNotIn('--model',result['command'])
        self.assertEqual(result['profile_env']['CODEX_HOME'],str(self.root))
        self.assertEqual(json.loads((self.root/'worker/launch.json').read_text())['executor'],'codex')

    def test_worker_codex_to_claude_preserves_interactive_approval(self):
        with patch.object(visible,'EXECUTOR_OVERRIDE','claude'), patch.object(visible.subprocess,'run') as opened:
            result=supervisor._visible_worker_launch({'agent':'agent1-2','thread':1,'model':'codex'},
                self.root,self.root/'worker',dry_run=True,model='codex-model',launch_mode='interactive')
        opened.assert_not_called()
        self.assertEqual(result['executor'],'claude');self.assertEqual(result['requested_executor'],'codex')
        self.assertEqual(result['command'][0],'claude')
        self.assertNotIn('--dangerously-skip-permissions',result['command']);self.assertNotIn('--model',result['command'])
        self.assertNotIn('--yolo',result['command'])

    def test_restricted_docs_and_unconverted_callers_refuse_switch_before_launch(self):
        with patch.object(visible,'EXECUTOR_OVERRIDE','codex'), patch.object(visible.subprocess,'run') as opened:
            with self.assertRaisesRegex(ValueError,'executor-pinned'):
                supervisor._visible_worker_launch({'agent':'agent1-2','thread':1,'model':'claude'},
                    self.root,self.root/'doc',dry_run=True,profile='doc')
            with self.assertRaisesRegex(ValueError,'cannot apply'):
                visible.launch_visible(self.root/'legacy','claude',['claude','prompt'],title='old',dry_run=True)
        opened.assert_not_called();self.assertFalse((self.root/'doc').exists());self.assertFalse((self.root/'legacy').exists())

    def test_explicit_engine_choice_never_resumes_or_forks(self):
        for engine, argv in [('claude',['claude','--resume','id']),('claude',['claude','--fork-session']),
                             ('codex',['codex','exec','resume','id']),('codex',['codex','fork','id'])]:
            with self.subTest(engine=engine,argv=argv), patch.object(visible,'EXECUTOR_OVERRIDE',engine):
                with self.assertRaisesRegex(ValueError,'fresh session'):
                    visible.launch_visible(self.root/'resume',engine,argv,title='resume',dry_run=True)
        self.assertFalse((self.root/'resume').exists())

    def test_coordinator_preview_records_actual_engine_model_and_profile(self):
        sprint=self.root/'thread';sprint.mkdir()
        (sprint/'sprint.json').write_text(json.dumps({'executor':'claude','model':'opus'}))
        cfg=self.root/'launch-config.json';cfg.write_text(json.dumps({'auto_launch':'disabled','claude_profile':'alternate'}))
        with patch.object(visible,'EXECUTOR_OVERRIDE','codex'), \
             patch.object(coordinator,'_thread_folder',return_value=str(sprint)), \
             patch.object(coordinator,'RUNS_DIR',str(self.root/'runs')), \
             patch.object(coordinator,'LAUNCH_CFG',str(cfg)), \
             patch.object(visible.subprocess,'run') as opened:
            result=coordinator.invoke(1,{'trigger':'fixture','round':{'round':1,'status':'ALIGNED'}},None,dry_run=True)
        opened.assert_not_called()
        self.assertEqual(result['executor'],'codex');self.assertIsNone(result['model'])
        self.assertEqual(result['launch']['command'][0],'codex')
        self.assertEqual(result['launch']['requested_executor'],'claude')
        self.assertNotIn('--model',result['launch']['command'])

    def test_manual_and_wave_architects_switch_without_auto_bypass(self):
        with patch.object(visible,'EXECUTOR_OVERRIDE','codex'), \
             patch.object(architect,'RUNS_DIR',str(self.root/'architects')), \
             patch.object(visible.subprocess,'run') as opened:
            manual=architect.invoke_manual('fixture',dry_run=True,model='opus')
            wave=architect.invoke_wave({'wave_id':'fixture','sprints':[]},dry_run=True,model='opus')
        opened.assert_not_called()
        for result in (manual,wave):
            self.assertEqual(result['executor'],'codex');self.assertIsNone(result['model'])
            self.assertEqual(result['launch']['command'][0],'codex')
            self.assertNotIn('exec',result['launch']['command'][:2])
            self.assertNotIn('--yolo',result['launch']['command'])

    def test_automatic_architect_stays_headless_with_existing_auto_permission(self):
        with patch.object(visible,'EXECUTOR_OVERRIDE','codex'):
            engine,model,args=architect._architect_argv('resume','opus','claude',automatic=True)
        self.assertEqual(engine,'codex');self.assertIsNone(model);self.assertEqual(args[:2],['codex','exec'])
        self.assertIn('--dangerously-bypass-approvals-and-sandbox',args)
        self.assertEqual(args[-2:],['--','resume']);self.assertNotIn('--print',args)
        with patch.object(visible,'EXECUTOR_OVERRIDE','claude'):
            _,_,args=architect._architect_argv('prompt','opus','claude',automatic=True)
        self.assertIn('--print',args);self.assertIn('--dangerously-skip-permissions',args)


if __name__=='__main__':unittest.main()
