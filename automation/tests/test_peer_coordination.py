"""Peer delivery and no-sprint native wait regressions; no AI/product operations."""
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import channel_delivery as d
import coordinator_continuation as c
import owner_sessions as o


class PeerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.auto = self.root / 'automation'; self.auto.mkdir()
        for mod, name, value in [(d, 'ARTIFACT_ROOT', self.root), (d, 'MAILBOX_ROOT', self.auto/'mail'),
                                 (d, 'DISPATCH_LOCK', self.auto/'lock'), (o, 'HERE', self.auto),
                                 (o, 'OWNERS', self.auto/'owners'), (o, 'REPO', self.root)]:
            p = patch.object(mod, name, value); p.start(); self.addCleanup(p.stop)
        self.actor = 1
        self.records = {}
        for n in (1, 2):
            folder = self.root/f'thread{n}'; folder.mkdir()
            (folder/'sprint.json').write_text(json.dumps(dict(sprint_id=f'S{n}', thread=n, status='completed', tasks=[])))
            self.records[n] = dict(schema_version=1, role='coordinator', thread=n, state='bound',
                binding_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()), executor='claude', profile='/fixture',
                repository=str(self.root), pid=os.getpid(), process_fingerprint=o.fingerprint(os.getpid()))
            o.write(o.owner_path('coordinator', n), self.records[n])
        p = patch.object(o, 'identity', side_effect=lambda *a, **kw: {k:self.records[self.actor][k] for k in
            ('executor', 'session_id', 'profile', 'repository', 'pid', 'process_fingerprint')})
        p.start(); self.addCleanup(p.stop)
        p = patch.object(c.wave, 'active_wave', return_value=None); p.start(); self.addCleanup(p.stop)
        self.source = self.root/'thread1/question.md'; self.source.write_text('Which qualified digest should be consumed?')

    def send(self, kind='question', source=None, sender=1, receiver=2, reply_to=None):
        self.actor = sender
        return d.peer_send(sender, receiver, kind, source or self.source, reply_to)

    def payload(self):
        return dict(hook_event_name='Stop', session_id=self.records[2]['session_id'], cwd=str(self.root))

    def test_question_ack_linked_answer_without_active_sprint_or_wave(self):
        q = self.send(); original = json.loads(q.read_text()); self.actor = 2
        self.assertEqual(len(d.peer_pending(self.records[2])), 1)
        answer = self.root/'thread2/answer.md'; answer.write_text('Use the versioned supplier receipt; shared apply remains held.')
        with self.assertRaisesRegex(ValueError, 'ACK'): self.send('answer', answer, 2, 1, original['id'])
        self.actor = 2; d.peer_ack(q, 2)
        self.assertEqual(d.peer_pending(self.records[2]), [])
        a = self.send('answer', answer, 2, 1, original['id'])
        self.assertEqual(json.loads(a.read_text())['reply_to'], original['id'])
        self.actor = 1; d.peer_ack(a, 1)
        self.assertEqual(d.peer_pending(self.records[1]), [])
        self.assertFalse(o.work_path(self.records[1]).exists())
        self.assertFalse(o.work_path(self.records[2]).exists())

    def test_all_modes_publish_same_owner_mail_without_mode_or_wave_authority(self):
        with patch.object(c.wave, 'active_wave', side_effect=AssertionError('no wave required')):
            for mode in ('Manual', 'Semi-auto', 'Easy', 'Auto'):
                self.source.write_text(f'{mode}: request supplier status, no dispatch permission')
                q = self.send(); self.actor = 2; d.peer_ack(q, 2)
        self.assertEqual(len(list(d.peer_folder(2).glob('*.read.json'))), 4)

    def test_duplicate_publication_and_original_mutation_preserve_snapshot_and_read(self):
        q = self.send(); self.assertEqual(q, self.send())
        event = json.loads(q.read_text()); self.source.write_text('A later source revision')
        snap = json.loads((d.MAILBOX_ROOT/event['snapshot']).read_text())
        self.assertIn('qualified digest', snap['body'])
        self.actor = 2; d.peer_ack(q, 2)
        self.assertEqual(d.peer_pending(self.records[2]), [])

    def test_wrong_sender_or_recipient_cannot_send_or_ack(self):
        self.actor = 2
        with self.assertRaisesRegex(ValueError, 'bound owner'):d.peer_send(1,2,'question',self.source)
        q = self.send(); self.actor = 1
        with self.assertRaisesRegex(ValueError, 'bound owner'):d.peer_ack(q,2)
        with self.assertRaisesRegex(ValueError, 'recipient mailbox'):d.peer_ack(q,1)

    def test_reserved_owner_cannot_receive_or_be_replaced(self):
        o.write(o.owner_path('coordinator',2), {**self.records[2], 'state':'reserved'})
        with self.assertRaisesRegex(ValueError,'not bound'):self.send()
        self.assertFalse(d.peer_folder(2).exists())

    def test_rebinding_rejects_unread_but_preserves_read_history(self):
        q = self.send(); current = self.records[2]
        o.write(o.owner_path('coordinator',2), {**current,'binding_id':str(uuid.uuid4())})
        with self.assertRaisesRegex(ValueError,'changed'):d.peer_pending(current)
        o.write(o.owner_path('coordinator',2),current); self.actor=2;d.peer_ack(q,2)
        new = {**current,'binding_id':str(uuid.uuid4())};o.write(o.owner_path('coordinator',2),new)
        self.assertEqual(d.peer_pending(new),[])

    def test_paths_worker_sources_oversize_and_symlinks_are_refused(self):
        worker = self.root/'thread1/agent1-1';worker.mkdir();(worker/'task.md').write_text('not a coordinator handoff')
        other = self.root/'thread2/other.md';other.write_text('foreign')
        for path in (worker/'task.md', other, self.root, self.root/'thread1/../thread2/other.md'):
            with self.assertRaises(ValueError):self.send(source=path)
        linked=self.root/'thread1/linked.md';linked.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'symlink'):self.send(source=linked)
        self.source.write_text('x'*(d.MAX_PEER_BYTES+1))
        with self.assertRaisesRegex(ValueError,'size'):self.send()

    def test_malformed_snapshot_event_and_reply_links_fail_closed(self):
        q=self.send();event=json.loads(q.read_text());snapshot=d.MAILBOX_ROOT/event['snapshot']
        snapshot.write_text(json.dumps({'body':'changed','sha256':event['source_sha256']}))
        with self.assertRaisesRegex(ValueError,'snapshot'):d.peer_pending(self.records[2])
        answer=self.root/'thread2/answer.md';answer.write_text('answer')
        with self.assertRaisesRegex(ValueError,'question id'):self.send('answer',answer,2,1)
        with self.assertRaisesRegex(ValueError,'kind/reply'):self.send('notice',reply_to='a'*64)
        q.write_text(json.dumps({**event,'unexpected':True}))
        with self.assertRaisesRegex(ValueError,'schema'):d.peer_pending(self.records[2])

    def test_stale_architect_round_does_not_starve_valid_peer_mail(self):
        question=self.send();self.actor=2
        with patch.object(c.wave,'active_wave',return_value={'wave_id':'fixture'}), patch.object(c.wave,'verified_thread_sprint',return_value={'id':'S2','thread':2}), patch.object(d,'pending',side_effect=ValueError('stale delivery source; reconcile current channel')) as rounds:
            pending=c.pending_events(self.records[2])
            self.assertEqual(pending[0]['id'],json.loads(question.read_text())['id'])
            rounds.assert_not_called()
            d.peer_ack(question,2)
            with self.assertRaisesRegex(ValueError,'stale delivery source'):c.pending_events(self.records[2])

    def test_stop_processes_peer_mail_without_work_and_preserves_task_state(self):
        self.send();self.actor=2
        result=c.hook(self.payload());self.assertEqual(result['decision'],'block')
        self.assertIn('linked answer',result['reason']);self.assertFalse(o.work_path(self.records[2]).exists())
        self.assertFalse(list(d.peer_folder(2).glob('*.read.json')))

    def test_completed_or_stale_work_does_not_hide_mail_but_pause_is_respected(self):
        self.send();self.actor=2
        for state in ('completed','founder-gate','active'):
            o.write(o.work_path(self.records[2]),{'state':state,'deliberately_stale_sprint':'old'})
            self.assertEqual(c.hook(self.payload())['decision'],'block')
        for state in ('paused','continuation-exhausted'):
            o.write(o.work_path(self.records[2]),{'state':state})
            self.assertNotIn('decision',c.hook(self.payload()))

    def test_communication_budget_is_bounded_and_never_auto_rearmed(self):
        self.send();self.actor=2
        for _ in range(c.MAX_BLOCKS):self.assertEqual(c.hook(self.payload())['decision'],'block')
        self.assertIn('exhausted',c.hook(self.payload())['systemMessage'])
        self.assertIn('exhausted',c.hook(self.payload())['systemMessage'])
        record=o.read(o.OWNERS/'hooks'/(self.records[2]['binding_id']+'-mail.json'))
        self.assertEqual(record['blocks'],c.MAX_BLOCKS)

    def test_mailbox_wait_without_work_reports_notification_and_never_accepts(self):
        self.send();self.actor=2;wait_id=str(uuid.uuid4())
        self.assertEqual(c.wait_for_work(2,wait_id,1,True),0)
        receipt=o.read(c.wait_path(self.records[2],wait_id))
        self.assertEqual(receipt['mode'],'mailbox-only');self.assertEqual(receipt['state'],'notification')
        self.assertFalse(o.work_path(self.records[2]).exists())
        with self.assertRaisesRegex(ValueError,'already used'):c.wait_for_work(2,wait_id,1,True)

    def test_native_mailbox_task_yields_without_starting_response_budget(self):
        self.actor=2;record=self.records[2];wait_id=str(uuid.uuid4())
        o.write(c.wait_path(record,wait_id),dict(**c.mailbox_authority(record),mode='mailbox-only',state='waiting',
            binding_id=record['binding_id'],session_id=record['session_id'],pid=os.getpid(),
            process_fingerprint=o.fingerprint(os.getpid()),deadline_utc=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=60)).isoformat()))
        payload=self.payload();payload['background_tasks']=[dict(id='native',type='shell',status='running',
            command=f'python3 {c.__file__} wait --thread 2 --wait-id {wait_id} --timeout 60 --mailbox-only')]
        self.assertEqual(c.hook(payload),{})
        receipt=o.read(o.OWNERS/'hooks'/(record['binding_id']+'-mail.json'))
        self.assertEqual(receipt['state'],'native-wait-armed');self.assertIsNone(receipt['started_utc'])
        self.send();self.actor=2;self.assertEqual(c.hook(payload)['decision'],'block')

    def test_generic_background_task_cannot_impersonate_mail_wait(self):
        self.actor=2;payload=self.payload();payload['background_tasks']=[dict(id='generic',type='shell',status='running',command='sleep 99')]
        self.assertIn('not active',c.hook(payload)['systemMessage'])

    def test_mailbox_timeout_records_boundary_without_rearming_any_work(self):
        self.actor=2;wait_id=str(uuid.uuid4())
        self.assertEqual(c.wait_for_work(2,wait_id,.01,True),124)
        self.assertEqual(o.read(c.wait_path(self.records[2],wait_id))['state'],'timeout')
        self.assertFalse(o.work_path(self.records[2]).exists())

    def test_mailbox_wait_stops_on_owner_change(self):
        self.actor=2;wait_id=str(uuid.uuid4())
        def switch():
            o.write(o.owner_path('coordinator',2),{**self.records[2],'binding_id':str(uuid.uuid4())})
            return []
        with patch.object(c,'pending_events',side_effect=lambda record:switch()), patch.object(c.time,'sleep'):
            self.assertEqual(c.wait_for_work(2,wait_id,1,True),124)
        self.assertEqual(o.read(c.wait_path(self.records[2],wait_id))['state'],'owner-changed')

    def test_peer_notice_cannot_be_used_as_question_for_answer(self):
        q=self.send('notice');self.actor=2;d.peer_ack(q,2)
        answer=self.root/'thread2/answer.md';answer.write_text('not an answer to a question')
        with self.assertRaisesRegex(ValueError,'question from the target'):
            self.send('answer',answer,2,1,json.loads(q.read_text())['id'])

    def test_native_mailbox_wait_runs_as_process_and_returns_on_file_delivery(self):
        # Only executor authentication is a fixture. Real process, lock, files,
        # owner fingerprint and waiter receipt exercise the actual transport.
        script='''import sys,json\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nimport channel_delivery as d,owner_sessions as o,coordinator_continuation as c\nr=Path(sys.argv[2]);a=r/'automation'\nd.ARTIFACT_ROOT=r;d.MAILBOX_ROOT=a/'mail';d.DISPATCH_LOCK=a/'lock'\no.HERE=a;o.OWNERS=a/'owners';o.REPO=r\no.authenticate=lambda record:None\nc.wave.active_wave=lambda:None\nraise SystemExit(c.wait_for_work(2,sys.argv[3],5,True))\n'''
        wait_id=str(uuid.uuid4());self.actor=2
        process=subprocess.Popen([sys.executable,'-c',script,str(Path(c.__file__).parent),str(self.root),wait_id],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            deadline=time.monotonic()+3
            while not c.wait_path(self.records[2],wait_id).exists() and time.monotonic()<deadline:
                time.sleep(.02)
            self.assertTrue(c.wait_path(self.records[2],wait_id).exists())
            self.send();out,err=process.communicate(timeout=6)
            self.assertEqual(process.returncode,0,err);self.assertEqual(json.loads(out)['state'],'notification')
            self.assertFalse(list(d.peer_folder(2).glob('*.read.json')))
        finally:
            if process.poll() is None:process.kill();process.communicate()

    def grant_wave(self):
        source = self.root/'authority.md'; source.write_text('explicit bounded communication only')
        self.grant_source = source
        selected = dict(id='S-mail', thread=2, status='pending', task_ids=['TASK-12'],
                        scope_review_ref='authority.md', model_policy='unchanged', target_tier='communication',
                        founder_auth_ref='fixture founder grant', opening_round=1)
        self.grant_config = dict(wave_id='W-mail', status='active', verified_by_architect=True,
            operating_deadline_utc=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=600)).isoformat(),
            source_sha256={'authority.md':d.sha(source)}, sprints=[selected])
        p=patch.object(c.wave,'active_wave',return_value=self.grant_config); p.start(); self.addCleanup(p.stop)
        self.actor=2

    def test_explicit_mail_grant_preserves_old_receipt_and_refuses_replay(self):
        self.grant_wave();record=self.records[2];path=c.mail_receipt_path(record)
        o.write(path,dict(**c.mailbox_authority(record),blocks=1,started_utc=o.now(),state='continuation-exhausted'))
        raw=path.read_text();grant=c.arm_mail(2,3600,24)
        self.assertEqual(grant['prior_receipt_utf8'],raw)
        self.assertEqual(grant['author']['session_id'],record['session_id'])
        receipt=o.read(path);self.assertEqual(receipt['blocks'],0);self.assertIsNone(receipt['started_utc'])
        self.assertEqual(receipt['deadline_utc'],self.grant_config['operating_deadline_utc'])
        with self.assertRaisesRegex(ValueError,'already used'):c.arm_mail(2,3600,24)
        self.assertEqual(o.read(path),receipt)
        self.assertFalse(o.work_path(record).exists())

    def test_architect_mail_grant_is_not_a_recipient_ack(self):
        self.grant_wave();a={**self.records[2], 'role':'architect','thread':0,
                            'binding_id':str(uuid.uuid4()),'session_id':str(uuid.uuid4())}
        self.records[0]=a;o.write(o.owner_path('architect'),a);self.actor=0
        grant=c.arm_mail(2,60,3,True)
        self.assertEqual(grant['author']['session_id'],a['session_id'])
        self.assertEqual(grant['session_id'],self.records[2]['session_id'])
        self.assertFalse(list(d.peer_folder(2).glob('*.read.json')))

    def test_mail_grant_auth_paused_expired_source_and_argument_refusals(self):
        self.grant_wave();self.actor=1
        with self.assertRaisesRegex(ValueError,'bound owner'):c.arm_mail(2)
        self.actor=2
        for seconds,blocks in ((0,6),(3601,6),(60,0),(60,25)):
            with self.assertRaises(ValueError):c.arm_mail(2,seconds,blocks)
        self.grant_source.write_text('drift')
        with self.assertRaisesRegex(ValueError,'source pin'):c.arm_mail(2)
        self.grant_source.write_text('explicit bounded communication only')
        for state in ('paused','continuation-exhausted'):
            o.write(o.work_path(self.records[2]),{'state':state})
            with self.assertRaisesRegex(ValueError,'work'):c.arm_mail(2)
        o.write(o.work_path(self.records[2]),{'state':'completed'})
        self.grant_config['operating_deadline_utc']=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(ValueError,'expired'):c.arm_mail(2)

    def test_explicit_response_budget_then_exhaustion_and_wait_refusal(self):
        self.grant_wave();c.arm_mail(2,600,8)
        with patch.object(c,'pending_events',return_value=[{'path':'fixture-peer'}]):
            for _ in range(8):self.assertEqual(c.mail_hook(self.records[2],{}).get('decision'),'block')
            self.assertIn('exhausted',c.mail_hook(self.records[2],{})['systemMessage'])
        with self.assertRaisesRegex(ValueError,'exhausted'):c.wait_for_work(2,str(uuid.uuid4()),1,True)

    def test_mail_grant_scope_and_source_drift_fail_closed(self):
        self.grant_wave();c.arm_mail(2)
        receipt=o.read(c.mail_receipt_path(self.records[2]))
        self.grant_source.write_text('changed')
        with self.assertRaisesRegex(ValueError,'source pin'):c.mail_limits(self.records[2],receipt)
        self.grant_source.write_text('explicit bounded communication only')
        self.grant_config['sprints'][0]['task_ids']=['different-task']
        with self.assertRaisesRegex(ValueError,'scope'):c.mail_limits(self.records[2],receipt)

    def test_explicit_deadline_stops_idle_hook_and_wait(self):
        self.grant_wave();grant=c.arm_mail(2);path=c.mail_receipt_path(self.records[2]);receipt=o.read(path)
        expired=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=1)).isoformat()
        grant['deadline_utc']=expired;receipt['deadline_utc']=expired
        o.write(Path(receipt['grant_path']),grant);o.write(path,receipt)
        with patch.object(c,'pending_events',return_value=[]):
            self.assertIn('expired',c.mail_hook(self.records[2],{})['systemMessage'])
        with self.assertRaisesRegex(ValueError,'exhausted'):c.wait_for_work(2,str(uuid.uuid4()),1,True)

    def test_explicit_mail_wait_is_capped_by_original_deadline(self):
        self.grant_wave();grant=c.arm_mail(2,1,2)
        with patch.object(c,'pending_events',return_value=[{'path':'fixture-peer'}]):
            wait_id=str(uuid.uuid4());self.assertEqual(c.wait_for_work(2,wait_id,3600,True),0)
        receipt=o.read(c.wait_path(self.records[2],wait_id))
        self.assertLessEqual(dt.datetime.fromisoformat(receipt['deadline_utc']),dt.datetime.fromisoformat(grant['deadline_utc']))


if __name__=='__main__':unittest.main()
