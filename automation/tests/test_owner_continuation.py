import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import owner_sessions as owners
import coordinator_continuation as continuation
import channel_delivery as delivery
import coordinator_trigger as trigger
import architect_invoke as architect
import architect_bridge as bridge
import initiate_automation as runtime
from test_channel_delivery import fixture_wave


class OwnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.coord = self.root / 'coord'; self.auto = self.coord / 'automation'
        self.auto.mkdir(parents=True)
        self.owners = self.auto / 'var/owners'
        values = [(owners, 'HERE', self.auto), (owners, 'OWNERS', self.owners), (owners, 'REPO', self.root),
                  (delivery, 'DISPATCH_LOCK', self.auto / 'dispatch.lock'),
                  (delivery, 'ARTIFACT_ROOT', self.coord), (delivery, 'MAILBOX_ROOT', self.auto / 'mail'),
                  (bridge, 'CHANNEL_DIR', str(self.coord / 'channels'))]
        for module, name, value in values:
            p = patch.object(module, name, value); p.start(); self.addCleanup(p.stop)
        self.who = dict(executor='claude', session_id=str(uuid.uuid4()), profile='/fixture/profile',
                        pid=12345, process_fingerprint='fingerprint', repository=str(self.root))
        p = patch.object(owners, 'identity', return_value=self.who); p.start(); self.addCleanup(p.stop)
        p = patch.object(owners, 'fingerprint', return_value='fingerprint'); p.start(); self.addCleanup(p.stop)
        self.folder = self.coord / 'thread1'; self.folder.mkdir()
        self.sprint = dict(sprint_id='TASK-current', thread=1, executor='claude', model='opus', status='active',
                           tasks=[dict(id='TASK-09', agent='agent1-1', status='pending')])
        self.save_sprint()
        self.assignment = self.coord / 'assignment.md'; self.assignment.write_text('founder assigned source work')
        self.worker = self.folder / 'agent1-1'; self.worker.mkdir()
        self.state = dict(status='idle', task_digest='a'*64, dispatch_sequence=1, result_location='runs/001/result.json')
        self.save_worker()
        p = patch.object(continuation.wave, 'active_wave', return_value=None); p.start(); self.addCleanup(p.stop)

    def save_sprint(self):
        (self.folder / 'sprint.json').write_text(json.dumps(self.sprint))

    def save_worker(self):
        (self.worker / 'state.json').write_text(json.dumps(self.state))

    def bind(self, role='coordinator', thread=1):
        return owners.register(role, thread, 'claude')

    def arm(self):
        record = self.bind()
        owners.arm(1, ['TASK-09'], str(self.assignment))
        return record

    def payload(self, record):
        return dict(hook_event_name='Stop', session_id=record['session_id'], cwd=str(self.root))

    def test_reservation_is_not_owner_but_blocks_all_new_launch_checks(self):
        owners.reserve('coordinator', 1); owners.reserve('architect')
        self.assertIn('reserved', trigger.live_coordinator_run(1))
        self.assertIn('reserved', delivery.active_architect())
        with patch.object(delivery, 'foreign_controller_conflict'), patch.object(architect._vl, 'launch_visible') as launch:
            result = architect._launch_architect(self.root/'new', 'fixture', ['fixture'], dry_run=False)
        launch.assert_not_called(); self.assertIn('refused', result)

    def test_same_owner_idempotent_foreign_owner_and_release_cannot_take_over(self):
        record = self.bind(); self.assertEqual(record, self.bind())
        with patch.object(owners, 'identity', return_value={**self.who, 'session_id':str(uuid.uuid4())}):
            with self.assertRaisesRegex(ValueError, 'takeover'): self.bind()
            with self.assertRaisesRegex(ValueError, 'only the bound'): owners.release('coordinator',1)
        owners.release('coordinator',1)
        self.assertIsNone(owners.blocking_owner('coordinator',1))
        with self.assertRaisesRegex(ValueError, 'new assignment'): self.bind()

    def test_same_codex_app_thread_refreshes_process_without_new_owner(self):
        codex = {**self.who, 'executor':'codex', 'profile':None}
        with patch.object(owners,'identity',return_value=codex):
            first=owners.register('architect',0,'codex')
        with patch.object(owners,'identity',return_value={**codex,'pid':54321,'process_fingerprint':'new-process'}):
            second=owners.register('architect',0,'codex')
        self.assertEqual(first['binding_id'],second['binding_id']);self.assertEqual(second['pid'],54321)
        with patch.object(owners,'identity',return_value={**codex,'session_id':str(uuid.uuid4())}):
            with self.assertRaisesRegex(ValueError,'takeover'):owners.register('architect',0,'codex')

    def test_dead_reused_permission_denied_malformed_and_symlink_all_block(self):
        self.bind()
        for value in (ValueError('dead'), PermissionError('denied'), 'other-birth'):
            with patch.object(owners, 'fingerprint', side_effect=value if isinstance(value, Exception) else None,
                              return_value=value if isinstance(value,str) else None):
                self.assertTrue(owners.blocking_owner('coordinator',1))
        path=owners.owner_path('coordinator',1);path.write_text('{}')
        self.assertIn('invalid',owners.blocking_owner('coordinator',1))
        path.unlink(); target=self.root/'foreign';target.write_text('{}');path.symlink_to(target)
        self.assertIn('invalid',owners.blocking_owner('coordinator',1))

    def test_concurrent_registration_never_creates_two_owners(self):
        def attempt(_):
            try:return self.bind()['binding_id']
            except BlockingIOError:return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            ids=[x for x in pool.map(attempt,range(20)) if x]
        self.assertEqual(len(set(ids)),1)

    def test_continuation_blocks_premature_stop_without_accepting_or_launching(self):
        record=self.arm()
        with patch.object(trigger,'invoke') as launch:
            result=continuation.hook(self.payload(record))
        self.assertEqual(result['decision'],'block');launch.assert_not_called()
        self.assertEqual(owners.read(owners.work_path(record))['blocks'],1)
        self.assertEqual(self.sprint['tasks'][0]['status'],'pending')

    def test_unbound_foreign_repo_and_subagent_hooks_have_no_effect(self):
        record=self.arm();payload=self.payload(record)
        for other in ({**payload,'session_id':str(uuid.uuid4())}, {**payload,'cwd':'/foreign'}, {**payload,'agent_id':'worker'}):
            self.assertEqual(continuation.hook(other),{})

    def test_work_authority_allows_progress_but_rejects_task_or_assignment_changes(self):
        record=self.arm();self.sprint['tasks'][0]['status']='running';self.save_sprint()
        self.assertEqual(continuation.hook(self.payload(record))['decision'],'block')
        self.sprint['tasks'][0]['agent']='agent1-2';self.save_sprint()
        self.assertNotIn('decision',continuation.hook(self.payload(record)))
        self.sprint['tasks'][0]['agent']='agent1-1';self.save_sprint();self.assignment.write_text('scope changed')
        self.assertNotIn('decision',continuation.hook(self.payload(record)))

    def test_blocks_are_bounded_and_rearm_requires_explicit_boundary(self):
        record=self.arm()
        with self.assertRaisesRegex(ValueError,'already active'): owners.arm(1,['TASK-09'],str(self.assignment))
        for _ in range(continuation.MAX_BLOCKS):self.assertEqual(continuation.hook(self.payload(record))['decision'],'block')
        self.assertNotIn('decision',continuation.hook(self.payload(record)))
        self.assertEqual(owners.read(owners.work_path(record))['state'],'continuation-exhausted')

    def test_time_budget_exhaustion_is_visible_not_silent_rearm(self):
        record=self.arm();value=owners.read(owners.work_path(record))
        value['started_utc']=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=901)).isoformat()
        owners.write(owners.work_path(record),value)
        self.assertIn('exhausted',continuation.hook(self.payload(record))['systemMessage'])
        self.assertEqual(owners.read(owners.work_path(record))['blocks'],0)

    def test_completed_boundary_requires_done_tasks_and_real_evidence(self):
        record=self.arm()
        with self.assertRaisesRegex(ValueError,'not complete'):owners.boundary(1,'completed',str(self.assignment))
        self.sprint['tasks'][0]['status']='done';self.save_sprint()
        owners.boundary(1,'completed',str(self.assignment))
        self.assertEqual(continuation.hook(self.payload(record)),{})

    def test_founder_gate_and_pause_allow_stop_without_claiming_completion(self):
        record=self.arm();owners.boundary(1,'founder-gate',str(self.assignment))
        self.assertEqual(continuation.hook(self.payload(record)),{})
        self.assertEqual(owners.read(owners.work_path(record))['state'],'founder-gate')

    def test_generic_background_task_does_not_bypass_stop(self):
        record=self.arm();payload=self.payload(record)
        payload['background_tasks']=[dict(id='bg',type='shell',status='running',command='sleep 999')]
        self.assertEqual(continuation.hook(payload)['decision'],'block')

    def test_pending_event_prompts_exact_path_and_never_acknowledges(self):
        record=self.arm()
        with patch.object(continuation,'pending_events',return_value=[{'path':'/exact/event.json','id':'a'*64}]):
            result=continuation.hook(self.payload(record))
        self.assertIn('Pending event paths: /exact/event.json',result['reason'])
        self.assertFalse(list(delivery.MAILBOX_ROOT.rglob('*.read.json')))

    def test_exact_native_waiter_allows_yield_but_no_read_ack(self):
        record=self.arm();value=owners.read(owners.work_path(record));wait_id=str(uuid.uuid4())
        owners.write(continuation.wait_path(record,wait_id),dict(state='waiting',binding_id=record['binding_id'],
            authority=value['authority'],session_id=record['session_id'],sprint_id=value['sprint_id'],pid=12345,
            process_fingerprint='fingerprint', deadline_utc=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=60)).isoformat()))
        payload=self.payload(record);payload['background_tasks']=[dict(id='native-bg',type='shell',status='running',
            command=f'python3 {continuation.__file__} wait --thread 1 --wait-id {wait_id}')]
        self.assertEqual(continuation.hook(payload),{})
        receipt=owners.read(owners.OWNERS/'hooks'/f"{record['binding_id']}.json")
        self.assertEqual(receipt['state'],'native-wait-armed');self.assertEqual(receipt['native_task_id'],'native-bg')
        self.assertFalse(list((delivery.MAILBOX_ROOT).rglob('*.read.json')))

    def test_waiter_reports_pinned_result_but_never_accepts_it(self):
        record=self.arm();self.state['status']='running';self.save_worker()
        target=self.worker/'runs/001/result.json';target.parent.mkdir(parents=True);target.write_text('{"outcome":"plan_ready"}')
        wait_id=str(uuid.uuid4())
        self.assertEqual(continuation.wait_for_work(1,wait_id,1),0)
        result=owners.read(continuation.wait_path(record,wait_id));self.assertEqual(result['state'],'worker-result')
        self.assertEqual(json.loads((self.worker/'state.json').read_text())['status'],'running')
        with self.assertRaisesRegex(ValueError,'already used'):continuation.wait_for_work(1,wait_id,1)

    def test_worker_result_traversal_refused(self):
        record=self.arm();self.state.update(status='running',result_location='../../other/result.json');self.save_worker()
        with self.assertRaisesRegex(ValueError,'escapes'):continuation.wait_for_work(1,str(uuid.uuid4()),1)

    def test_queue_only_real_flow_never_launches_and_requires_current_scope(self):
        current=fixture_wave();current['delivery_only']=True
        scope=delivery.scope_sha(current,current['sprints'][0]);channels=Path(bridge.CHANNEL_DIR);channels.mkdir()
        source=channels/'thread1.md';source.write_text(f'<!-- round:1 checkpoint:assignment status:AWAITING-ARCHITECT bootstrap:wave:fixture wave:fixture scope:{scope} -->')
        with patch.object(bridge._wave,'active_wave',return_value=current), patch.object(architect,'invoke') as invoke:
            result=delivery.delivery_only_tick('architect');self.assertEqual(len(result['events']),1)
            self.assertEqual(delivery.delivery_only_tick('architect')['events'],result['events']);invoke.assert_not_called()
            event=Path(result['events'][0]);delivery.acknowledge(event,recipient='architect',thread=1,wave_id='fixture',scope=scope)
            source.write_text(source.read_text().replace('AWAITING-ARCHITECT','ALIGNED'))
            response=delivery.delivery_only_tick('coordinator');self.assertEqual(len(response['events']),1)
            delivery.acknowledge(Path(response['events'][0]),recipient='coordinator',thread=1,wave_id='fixture',scope=scope)
            source.write_text(source.read_text()+'\nCoordinator consumed and appended status; machine token not yet edited.')
            self.assertEqual(delivery.delivery_only_tick('coordinator')['events'],[])
            source.write_text(source.read_text()+'\nTimestamp corrected.')
            self.assertEqual(delivery.delivery_only_tick('coordinator')['events'],[])
            source.write_text(source.read_text().replace('ALIGNED','GREEN'))
            self.assertEqual(delivery.delivery_only_tick('coordinator')['events'],[])
        self.assertEqual(len(list(delivery.MAILBOX_ROOT.rglob('*.read.json'))),2)

    def test_queue_only_does_not_compete_for_actor_lock_and_rejects_changed_sources(self):
        current=fixture_wave();current.update(delivery_only=True,source_sha256={'assignment.md':delivery.sha(self.assignment)})
        channels=Path(bridge.CHANNEL_DIR);channels.mkdir()
        with patch.object(bridge._wave,'active_wave',return_value=current), \
             patch.object(delivery,'dispatch_guard',side_effect=BlockingIOError('actor busy')):
            self.assertEqual(delivery.delivery_only_tick('architect')['events'],[])
            self.assignment.write_text('unreviewed change')
            with self.assertRaisesRegex(ValueError,'source changed'):delivery.delivery_only_tick('architect')

    def test_event_selection_source_race_does_not_publish_wrong_round(self):
        self.assignment.write_text('changed')
        with self.assertRaisesRegex(ValueError,'channel changed'):
            delivery.emit(wave_id='fixture',scope='a'*64,thread=1,recipient='architect',number=1,
                          status='AWAITING-ARCHITECT',source=self.assignment,expected_source_sha='b'*64)
        self.assertFalse(list(delivery.MAILBOX_ROOT.rglob('*.json')))

    def test_delivery_only_runtime_starts_no_manual_router_and_no_arm(self):
        with patch.object(runtime,'start_one',return_value={}) as start:
            self.assertEqual(runtime.main(['--start-delivery']),0)
        self.assertEqual([c.args[0]['name'] for c in start.call_args_list],['architect_bridge','coordinator_trigger'])
        self.assertTrue(all(c.kwargs['delivery_only'] for c in start.call_args_list))
        with self.assertRaises(SystemExit): runtime.main(['--start-delivery','--arm'])


class IdentityTests(unittest.TestCase):
    def test_real_process_fingerprint_and_wrong_ancestor_refusal(self):
        self.assertEqual(owners.fingerprint(os.getpid()),owners.fingerprint(os.getpid()))
        with self.assertRaises((ValueError,subprocess.SubprocessError)):owners.ancestor('no-such-executor')

    def test_claude_profile_session_must_match_actual_ancestor(self):
        with tempfile.TemporaryDirectory(dir=Path.home()) as folder, patch.object(owners,'ancestor',return_value=4321), \
             patch.object(owners,'fingerprint',return_value='birth'), \
             patch.object(owners.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps([
                 dict(pid=4321,sessionId=str(uuid.uuid4()),cwd=str(owners.REPO))]),'')):
            with self.assertRaisesRegex(ValueError,'identity mismatch'):owners.identity('claude',folder,str(uuid.uuid4()))
            who=owners.identity('claude',folder);self.assertEqual(who['pid'],4321)
            self.assertEqual(who['profile'],folder)


if __name__=='__main__':unittest.main()
