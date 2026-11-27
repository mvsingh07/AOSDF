"""Finite communication-window fixtures; never operate real owners or daemons."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import architect_bridge as bridge
import architect_invoke as native
import channel_delivery as delivery
import owner_sessions as owners
import test_architect_native_transport as transport


class WakeWindowTests(unittest.TestCase):
    def setUp(self):
        transport.NativeTransportTests.setUp(self)
        self.now = dt.datetime(2026, 11, 18, 21, tzinfo=dt.timezone.utc)
        p = patch.object(bridge, '_wake_now', side_effect=lambda: self.now)
        p.start(); self.addCleanup(p.stop)
        self.wavepath = self.root / 'wave.json'; self.wavepath.write_text(json.dumps(self.wave))
        p = patch.object(bridge._wave, 'WAVE_PATH', str(self.wavepath))
        p.start(); self.addCleanup(p.stop)
        p = patch.object(delivery, 'delivery_only_tick', return_value={'state': 'delivery-only', 'events': []})
        self.queue = p.start(); self.addCleanup(p.stop)
        self.w15 = self.runs / 'w15'; self.w15.mkdir(parents=True)
        self.notification = self.w15 / 'event.json'; self.notification.write_text(json.dumps(self.event))
        self.review = self.w15 / 'initial-review.json'
        self.review.write_text(json.dumps({'verdict': 'APPROVED', 'section_sha256': 'a' * 64}))
        self.peers = {}
        for n in (1, 2, 3):
            peer = {**self.owner, 'role': 'coordinator', 'thread': n,
                    'binding_id': str(uuid.uuid4()), 'session_id': str(uuid.uuid4())}
            owners.write(owners.owner_path('coordinator', n), peer)
            self.peers[str(n)] = {k: peer[k] for k in ('binding_id', 'session_id')}
        self.manifest = dict(schema_version=1, window_id=str(uuid.uuid4()),
            purpose='existing-architect-communication-only', founder_auth_ref='fixture explicit activation',
            approved_plan_digest='a'*64, review_receipt=str(self.review), review_receipt_sha256=delivery.sha(self.review),
            starts_utc=(self.now-dt.timedelta(seconds=1)).isoformat(),
            expires_utc=(self.now+dt.timedelta(hours=1)).isoformat(), max_submissions=3,
            wave_id=self.wave['wave_id'], wave_sha256=delivery.sha(self.wavepath), control_socket=str(self.endpoint),
            target_session_id=self.owner['session_id'], target_binding_id=self.owner['binding_id'],
            allowed_threads=[1, 2, 3], coordinator_bindings=self.peers,
            communication_only=True, product_gates_unchanged=True,
            pilot_event=str(self.notification), pilot_source_sha256=self.event['source_sha256'])
        self.manifestpath = self.w15 / 'window.json'

    def window(self, **changes):
        self.manifest.update(changes)
        self.manifestpath.write_text(json.dumps(self.manifest))
        window = bridge.ArchitectWakeWindow(self.manifestpath)
        self.addCleanup(window.close)
        return window

    def server(self, mode='normal', on_read=None):
        return transport.NativeTransportTests.server(self, mode, on_read)

    def ack(self, **changes):
        value = dict(schema_version=1, event_id=self.event['event_id'], source_sha256=self.event['source_sha256'],
            session_id=self.owner['session_id'], binding_id=self.owner['binding_id'],
            owner_authenticated=True, state='read', read_utc=self.now.isoformat())
        value.update(changes)
        (self.w15/'architect-read-ack.json').write_text(json.dumps(value))

    def test_opt_in_cli_only_and_no_default_native_call(self):
        with patch.object(bridge, 'watch_existing_owner_delivery') as watch, patch.object(delivery, 'watch_delivery') as queue:
            bridge.main(['--watch','--delivery-only'])
            queue.assert_called_once(); watch.assert_not_called()
            for flags in [[],['--watch'],['--delivery-only'],['--watch','--delivery-only','--auto'],
                          ['--watch','--delivery-only','--reset'],['--watch','--delivery-only','--notify']]:
                with self.assertRaises(SystemExit):bridge.main(flags+['--architect-wake-window','manifest'])
            bridge.main(['--watch','--delivery-only','--architect-wake-window','manifest'])
            watch.assert_called_once_with('manifest',30)

    def test_strict_fields_review_and_hard_charter_cap(self):
        for changes in [{'extra':True}, {'max_submissions':13}, {'max_submissions':True},
                        {'expires_utc':'2026-11-19T00:20:23Z'}, {'pilot_event':None},
                        {'review_receipt_sha256':'0'*64}, {'allowed_threads':[1,1]}]:
            original=dict(self.manifest)
            with self.subTest(changes=changes), self.assertRaises((ValueError,TypeError)):
                self.window(**changes)
            self.manifest=original

    def test_exact_manifest_and_single_window_lock(self):
        window=self.window()
        with self.assertRaises(BlockingIOError):bridge.ArchitectWakeWindow(self.manifestpath)
        self.assertTrue(window.state['wake_enabled'])
        self.assertEqual(len(window.state['reservations']),0)

    def test_expired_window_keeps_queueing_without_send(self):
        window=self.window(expires_utc=self.now.isoformat())
        with patch.object(native,'deliver_existing_native') as send:
            self.assertEqual(window.tick()['state'],'queue-only');send.assert_not_called()
        self.queue.assert_called_once();self.assertFalse(window.state['wake_enabled'])

    def test_monotonic_deadline_prevents_backward_clock_extension(self):
        window=self.window();window.deadline_mono=0
        self.now-=dt.timedelta(seconds=10)
        self.assertEqual(window.tick()['state'],'queue-only')

    def test_manifest_drift_disables_window(self):
        window=self.window();self.manifestpath.write_text(self.manifestpath.read_text()+' ')
        self.assertEqual(window.tick()['state'],'queue-only');self.assertFalse(window.state['wake_enabled'])

    def test_wave_drift_disables_without_mutation(self):
        window=self.window();self.wavepath.write_text('changed')
        with patch.object(native,'deliver_existing_native') as send:
            self.assertEqual(window.tick()['state'],'queue-only');send.assert_not_called()

    def test_architect_and_coordinator_rebinding_disable(self):
        for role,n in [('architect',0),('coordinator',2)]:
            with self.subTest(role=role):
                window=self.window(window_id=str(uuid.uuid4()))
                path=owners.owner_path(role,n);old=owners.read(path)
                owners.write(path,{**old,'binding_id':str(uuid.uuid4())})
                self.assertEqual(window.tick()['state'],'queue-only')
                owners.write(path,old);window.close()

    def test_busy_defers_without_reservation_or_payload(self):
        window=self.window();server=self.server('busy')
        self.assertEqual(window.tick()['state'],'queued-owner-not-idle')
        self.assertEqual(window.state['reservations'],{})
        self.assertFalse(any(r['method']=='turn/start' for r in server.requests))

    def test_real_socket_pilot_once_then_wait_for_exact_owner_ack(self):
        window=self.window();server=self.server()
        self.assertEqual(window.tick()['state'],'native-completed')
        self.assertEqual(window.tick()['state'],'awaiting-owner-read-ACK')
        self.ack();self.assertEqual(window.tick()['state'],'waiting-current-scoped-mail')
        self.assertEqual(sum(r['method']=='turn/start' for r in server.requests),1)
        record=next(iter(window.state['reservations'].values()));self.assertEqual(record['state'],'native-completed')
        self.assertFalse(server.errors)

    def test_foreign_or_unauthenticated_ACK_disables(self):
        window=self.window();self.server();window.tick();self.ack(owner_authenticated=False)
        self.assertEqual(window.tick()['state'],'wake-disabled')

    def test_lost_reply_disables_and_restart_cannot_rearm(self):
        window=self.window();server=self.server('lost_reply');result=window.tick()
        self.assertEqual(result['state'],'write-outcome-uncertain');self.assertFalse(window.state['wake_enabled'])
        statebytes=window.state_path.read_bytes();window.close()
        restarted=bridge.ArchitectWakeWindow(self.manifestpath);self.addCleanup(restarted.close)
        self.assertEqual(restarted.tick()['state'],'queue-only')
        self.assertEqual(len(restarted.state['reservations']),1)
        self.assertFalse(restarted.state['wake_enabled'])
        self.assertEqual(sum(r['method']=='turn/start' for r in server.requests),1)
        self.assertEqual(restarted.state_path.read_bytes(),statebytes)

    def test_budget_persists_across_restart_and_no_second_submission(self):
        window=self.window(max_submissions=1);server=self.server();window.tick();self.ack();window.close()
        restarted=bridge.ArchitectWakeWindow(self.manifestpath);self.addCleanup(restarted.close)
        self.assertEqual(restarted.tick()['state'],'queue-only')
        self.assertFalse(restarted.state['wake_enabled'])
        self.assertEqual(sum(r['method']=='turn/start' for r in server.requests),1)

    def test_new_window_never_resends_old_attempt(self):
        window=self.window();server=self.server();window.tick();self.ack();window.close()
        other=self.window(window_id=str(uuid.uuid4()))
        self.assertEqual(other.tick()['state'],'waiting-current-scoped-mail')
        self.assertEqual(other.state['reservations'],{})
        self.assertEqual(sum(r['method']=='turn/start' for r in server.requests),1)

    def test_expiry_after_idle_metadata_prevents_submission(self):
        window=self.window();server=self.server(on_read=lambda:setattr(self,'now',window.expiry))
        self.assertEqual(window.tick()['state'],'wake-disabled')
        self.assertFalse(any(r['method']=='turn/start' for r in server.requests))

    def test_expiry_after_durable_attempt_before_actual_write_blocks_payload(self):
        window=self.window();server=self.server();original=native._native_record
        def expire(path,value,**kwargs):
            original(path,value,**kwargs)
            if kwargs.get('create') and path.parent.name=='native-deliveries':self.now=window.expiry
        with patch.object(native,'_native_record',side_effect=expire):result=window.tick()
        self.assertEqual(result['state'],'write-outcome-uncertain')
        self.assertFalse(any(r['method']=='turn/start' for r in server.requests))
        self.assertEqual(len(window.state['reservations']),1)

    def test_unlisted_pilot_never_submits(self):
        window=self.window(pilot_source_sha256='0'*64);server=self.server()
        self.assertEqual(window.tick()['state'],'wake-disabled')
        self.assertFalse(any(r['method']=='turn/start' for r in server.requests))

    def test_deadline_clamps_native_transport_timeout(self):
        window=self.window(expires_utc=(self.now+dt.timedelta(seconds=7)).isoformat())
        with patch.object(native,'deliver_existing_native',return_value={'state':'queued-owner-not-idle'}) as send:
            window.tick();self.assertLessEqual(send.call_args.args[3],7)
            self.assertIs(send.call_args.kwargs['wake_window'],window)

    def test_read_receipt_is_not_manufactured(self):
        window=self.window();self.server();window.tick()
        self.assertFalse((self.w15/'architect-read-ack.json').exists())
        self.assertFalse((self.w15/'architect-response.json').exists())

    def test_failed_completion_disables_not_success(self):
        window=self.window();self.server('failed_readback')
        self.assertEqual(window.tick()['state'],'completion-needs-reconciliation')
        self.assertFalse(window.state['wake_enabled'])

    def test_review_pin_rechecked_immediately_before_submission(self):
        window=self.window();server=self.server(on_read=lambda:self.review.write_text('{}'))
        self.assertEqual(window.tick()['state'],'wake-disabled')
        self.assertFalse(any(r['method']=='turn/start' for r in server.requests))

    def test_loop_heartbeat_is_communication_only_and_uses_existing_daemon(self):
        window=self.window()
        with patch.object(bridge,'ArchitectWakeWindow',return_value=window),patch.object(window,'tick',return_value={'state':'waiting-current-scoped-mail'}),patch.object(bridge.time,'sleep',side_effect=KeyboardInterrupt),patch('daemon.write_status') as status:
            with self.assertRaises(KeyboardInterrupt):bridge.watch_existing_owner_delivery(self.manifestpath,10)
            fields=status.call_args.kwargs
            self.assertIs(fields['live'],False);self.assertTrue(fields['wake_enabled'])
            self.assertEqual(status.call_args.args[0],'architect_bridge')
            self.assertEqual(fields['path_mode'],'delivery-only-existing-owner-wake')


if __name__=='__main__':unittest.main()
