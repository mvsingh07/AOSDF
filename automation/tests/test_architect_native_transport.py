"""Private-socket process transport fixtures. No AI, new actor or product operation."""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import architect_invoke as a
import architect_bridge as bridge
import channel_delivery as d
import owner_sessions as owners
from test_channel_delivery import fixture_wave


class SocketServer:
    def __init__(self, path, owner, mode='normal', on_read=None):
        self.path, self.owner, self.mode, self.on_read = path, owner, mode, on_read
        self.requests, self.errors = [], []
        self.readbacks = 0
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(path)); os.chmod(path, 0o600); self.listener.listen(1); self.listener.settimeout(2)
        self.worker = threading.Thread(target=self.run, daemon=True); self.worker.start()

    def run(self):
        try:
            conn, _ = self.listener.accept(); conn.settimeout(2)
            with conn:
                def exact(n):
                    data=b''
                    while len(data)<n:
                        chunk=conn.recv(n-len(data))
                        if not chunk:raise EOFError()
                        data+=chunk
                    return data
                header=b''
                while not header.endswith(b'\r\n\r\n'):header+=exact(1)
                key=next(l.split(b':',1)[1].strip() for l in header.split(b'\r\n') if l.lower().startswith(b'sec-websocket-key:'))
                accept=base64.b64encode(hashlib.sha1(key+b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
                if self.mode=='bad_accept':accept=b'wrong'
                conn.sendall(b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept+b'\r\n\r\n')
                def send(value, opcode=1):
                    body=json.dumps(value).encode() if opcode==1 else value
                    prefix=bytes([128|opcode])+ (bytes([len(body)]) if len(body)<126 else b'\x7e'+struct.pack('!H',len(body)))
                    conn.sendall(prefix+body)
                while True:
                    first,second=exact(2);assert first==129 and second&128,'client must mask text frames'
                    size=second&127
                    if size==126:size=struct.unpack('!H',exact(2))[0]
                    elif size==127:size=struct.unpack('!Q',exact(8))[0]
                    mask=exact(4);body=exact(size);message=json.loads(bytes(v^mask[i%4] for i,v in enumerate(body)))
                    self.requests.append(message);method=message['method']
                    if method=='initialized':continue
                    if method=='initialize':
                        if self.mode=='approval':
                            send({'id':55,'method':'item/commandExecution/requestApproval','params':{}});return
                        if self.mode=='oversize':conn.sendall(b'\x81\x7f'+struct.pack('!Q',a.NativeControl.MAX_FRAME+1));return
                        send({'id':message['id'],'result':{'userAgent':'fixture'}})
                    elif method=='thread/read':
                        if self.on_read:self.on_read()
                        status='active' if self.mode=='busy' else 'idle'
                        identity=str(uuid.uuid4()) if self.mode=='wrong_thread' else self.owner['session_id']
                        send({'id':message['id'],'result':{'thread':{'id':identity,'cwd':self.owner['repository'],'status':{'type':status}}}})
                    elif method=='turn/start':
                        if self.mode=='lost_reply':return
                        if self.mode!='unsubscribed':send({'method':'turn/started','params':{'threadId':self.owner['session_id'],'turn':{'id':'fixture-turn'}}})
                        send({'id':message['id'],'result':{'turn':{'id':'fixture-turn','status':'inProgress'}}})
                        if self.mode=='timeout':
                            threading.Event().wait(1.2);return
                        if self.mode=='wrong_completion':
                            send({'method':'turn/completed','params':{'threadId':self.owner['session_id'],'turn':{'id':'other-turn','status':'completed'}}})
                        if self.mode!='unsubscribed':send({'method':'turn/completed','params':{'threadId':self.owner['session_id'],'turn':{'id':'fixture-turn','status':'completed'}}})
                    elif method=='thread/turns/list':
                        self.readbacks+=1
                        assert message['params']=={'threadId':self.owner['session_id'],'limit':1,'sortDirection':'desc','itemsView':'notLoaded'}
                        identity='different-turn' if self.mode=='mismatch_readback' else 'fixture-turn'
                        status='failed' if self.mode=='failed_readback' else 'inProgress' if self.mode=='pending_readback' and self.readbacks==1 else 'completed'
                        send({'id':message['id'],'result':{'data':[{'id':identity,'status':status,'items':[]}]}})
                    else:raise AssertionError('forbidden RPC '+method)
        except (EOFError,BrokenPipeError,ConnectionResetError,socket.timeout):pass
        except Exception as error:self.errors.append(error)

    def close(self):
        self.listener.close();self.worker.join(2)


class NativeTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='n-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();os.chmod(self.root,0o700)
        self.auto=self.root/'automation';self.auto.mkdir()
        self.runs=self.auto/'var/architect-runs'
        for module,name,value in [(a,'THREADS_DIR',str(self.root)),(a,'RUNS_DIR',str(self.runs)),(a,'REPO_ROOT',str(self.root)),
            (d,'ARTIFACT_ROOT',self.root),(d,'MAILBOX_ROOT',self.auto/'mail'),(d,'DISPATCH_LOCK',self.auto/'dispatch.lock'),
            (owners,'OWNERS',self.auto/'owners'),(owners,'REPO',self.root),(bridge,'CHANNEL_DIR',str(self.root/'channels'))]:
            p=patch.object(module,name,value);p.start();self.addCleanup(p.stop)
        self.owner=dict(schema_version=1,role='architect',thread=0,state='bound',binding_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),executor='codex',profile=None,pid=os.getpid(),
            process_fingerprint=owners.fingerprint(os.getpid()),repository=str(self.root))
        owners.write(owners.owner_path('architect'),self.owner)
        self.wave=fixture_wave();self.wave.update(delivery_only=True,autonomous=False)
        self.source=self.root/'request.md';self.source.write_text('A real coordination question; do not release runtime gates.')
        self.pin=self.root/'plan.md';self.pin.write_text('unchanged scope');self.wave['source_sha256']={'plan.md':d.sha(self.pin)}
        p=patch.object(a._wave,'active_wave',return_value=self.wave);p.start();self.addCleanup(p.stop)
        self.event=dict(schema_version=1,kind='bounded-tooling-native-handoff',created_utc='2026-11-18T19:00:00Z',source=str(self.source),source_sha256=d.sha(self.source),
            target_session_id=self.owner['session_id'],target_binding_id=self.owner['binding_id'],sender_role='bounded-tooling-repair-owner',sender_session_id=str(uuid.uuid4()),actor_launch_authority=False,auto_activation=False)
        self.event['event_id']=hashlib.sha256(d.canonical(self.event).encode()).hexdigest()
        self.notification=self.runs/'fixture/event.json';self.notification.parent.mkdir(parents=True);self.notification.write_text(json.dumps(self.event))
        self.endpoint=self.root/'s.sock'

    def server(self,mode='normal',on_read=None):
        server=SocketServer(self.endpoint,self.owner,mode,on_read);self.addCleanup(server.close);return server

    def deliver(self,timeout=2):return a.deliver_existing_native(self.notification,self.endpoint,self.owner['binding_id'],timeout)

    def test_real_private_socket_delivery_exact_RPCs_completion_and_no_ACK(self):
        server=self.server();result=self.deliver()
        self.assertEqual(result['state'],'native-completed');self.assertTrue(result['completion']['new_turn_started_observed'])
        self.assertEqual([r['method']for r in server.requests],['initialize','initialized','thread/read','turn/start','thread/turns/list'])
        turn=next(r for r in server.requests if r['method']=='turn/start');self.assertEqual(set(turn['params']),{'threadId','input'})
        self.assertEqual(turn['params']['threadId'],self.owner['session_id'])
        self.assertEqual(set(turn['params']['input'][0]),{'type','text'})
        self.assertFalse(result['read_acknowledged']);self.assertFalse(result['accepted']);self.assertFalse(server.errors)
        self.assertFalse(list(self.root.rglob('*.read.json')))

    def test_duplicate_event_does_not_send_again(self):
        server=self.server();self.deliver();second=self.deliver()
        self.assertEqual(second['state'],'already-attempted');self.assertFalse(second['resent'])
        self.assertEqual(sum(r['method']=='turn/start'for r in server.requests),1)

    def test_lost_reply_preserves_uncertain_reservation_without_resend(self):
        server=self.server('lost_reply');result=self.deliver()
        self.assertEqual(result['state'],'write-outcome-uncertain');self.assertFalse(result['automatic_retry'])
        self.assertEqual(self.deliver()['state'],'already-attempted')
        self.assertEqual(sum(r['method']=='turn/start'for r in server.requests),1)

    def test_timeout_after_submission_retains_turn_and_no_resend(self):
        server=self.server('timeout');result=self.deliver(1)
        self.assertEqual(result['state'],'submitted-uncertain');self.assertEqual(result['turn_id'],'fixture-turn')
        self.assertEqual(self.deliver()['state'],'already-attempted')
        self.assertEqual(sum(r['method']=='turn/start'for r in server.requests),1)

    def test_busy_owner_is_queued_without_payload_or_reservation(self):
        server=self.server('busy');self.assertEqual(self.deliver()['state'],'queued-owner-not-idle')
        self.assertFalse((self.runs/'native-deliveries').exists())
        self.assertFalse(any(r['method']=='turn/start'for r in server.requests))

    def test_changed_binding_refused_before_connection(self):
        self.owner['binding_id']=str(uuid.uuid4());owners.write(owners.owner_path('architect'),self.owner)
        with self.assertRaisesRegex(ValueError,'owner/authority'):self.deliver()

    def test_wrong_thread_on_same_server_never_receives_payload(self):
        server=self.server('wrong_thread')
        with self.assertRaisesRegex(ValueError,'identity/repository'):self.deliver()
        self.assertFalse(any(r['method']=='turn/start'for r in server.requests))

    def test_private_socket_permissions_and_symlink_enforced(self):
        self.server();os.chmod(self.endpoint,0o666)
        with self.assertRaisesRegex(ValueError,'private same-user'):self.deliver()
        alias=self.root/'alias';alias.symlink_to(self.endpoint)
        with self.assertRaisesRegex(ValueError,'symlink'):a.deliver_existing_native(self.notification,alias,self.owner['binding_id'],1)

    def test_peer_PID_mismatch_refused(self):
        self.server();changed={**self.owner,'pid':os.getpid()+100};owners.write(owners.owner_path('architect'),changed)
        with self.assertRaisesRegex(ValueError,'peer PID'):self.deliver()

    def test_bad_handshake_and_oversize_are_bounded(self):
        self.server('bad_accept')
        with self.assertRaisesRegex(ValueError,'WebSocket upgrade'):self.deliver()

    def test_oversize_frame_refused_before_payload(self):
        self.server('oversize')
        with self.assertRaisesRegex(ValueError,'oversize native frame'):self.deliver()

    def test_server_approval_request_is_not_answered(self):
        server=self.server('approval')
        with self.assertRaisesRegex(ValueError,'no approval sent'):self.deliver()
        self.assertEqual([r['method']for r in server.requests],['initialize'])

    def test_source_or_wave_drift_refused_before_submission(self):
        server=self.server(on_read=lambda:self.source.write_text('changed after metadata read'))
        with self.assertRaisesRegex(ValueError,'source mismatch'):self.deliver()
        self.assertFalse(any(r['method']=='turn/start'for r in server.requests))

    def test_wave_pin_drift_refused(self):
        self.pin.write_text('new unauthorized scope')
        with self.assertRaisesRegex(ValueError,'wave source pin'):self.deliver()

    def test_owner_race_before_submission_is_refused(self):
        server=self.server(on_read=lambda:owners.write(owners.owner_path('architect'),{**self.owner,'binding_id':str(uuid.uuid4())}))
        with self.assertRaisesRegex(ValueError,'selection changed'):self.deliver()
        self.assertFalse(any(r['method']=='turn/start'for r in server.requests))

    def test_wrong_completion_does_not_complete_another_turn(self):
        self.server('wrong_completion');result=self.deliver();self.assertEqual(result['completion']['turn_id'],'fixture-turn')

    def test_unsubscribed_transport_uses_exact_metadata_completion(self):
        server=self.server('unsubscribed');result=self.deliver()
        self.assertEqual(result['state'],'native-completed');self.assertFalse(result['completion']['new_turn_started_observed'])
        self.assertEqual(result['completion']['observation'],'bounded-metadata-readback');self.assertEqual(server.readbacks,1)

    def test_readback_wait_is_bounded_inside_original_deadline(self):
        server=self.server('pending_readback');result=self.deliver(3)
        self.assertEqual(result['state'],'native-completed');self.assertEqual(server.readbacks,2)

    def test_newest_mismatch_stays_unknown_without_pagination(self):
        server=self.server('mismatch_readback');result=self.deliver()
        self.assertEqual(result['state'],'completion-needs-reconciliation');self.assertEqual(result['completion']['status'],'unknown')
        self.assertEqual(server.readbacks,1)

    def test_failed_turn_is_not_success(self):
        self.server('failed_readback');result=self.deliver()
        self.assertEqual(result['state'],'completion-needs-reconciliation');self.assertEqual(result['completion']['status'],'failed')

    def make_existing_attempt(self):
        path=self.runs/'native-deliveries'/(self.event['event_id']+'.json')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(dict(event_id=self.event['event_id'],source_sha256=self.event['source_sha256'],
            target_session_id=self.owner['session_id'],target_binding_id=self.owner['binding_id'],turn_id='fixture-turn',state='submitted-uncertain')))
        return path,path.read_bytes()

    def test_separate_read_only_reconciliation_preserves_uncertain_bytes(self):
        path,before=self.make_existing_attempt();server=self.server()
        result=a.reconcile_existing_native(self.notification,self.endpoint,self.owner['binding_id'],2)
        self.assertEqual(result['state'],'reconciled-native-completed');self.assertFalse(result['payload_submitted'])
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual([r['method']for r in server.requests],['initialize','initialized','thread/read','thread/turns/list'])
        self.assertEqual(a.reconcile_existing_native(self.notification,self.endpoint,self.owner['binding_id'],2)['state'],'already-reconciled')
        self.assertEqual(server.readbacks,1)

    def test_reconciliation_of_different_newest_turn_is_unknown(self):
        path,before=self.make_existing_attempt();server=self.server('mismatch_readback')
        result=a.reconcile_existing_native(self.notification,self.endpoint,self.owner['binding_id'],2)
        self.assertEqual(result['state'],'reconciliation-unknown');self.assertEqual(server.readbacks,1)
        self.assertEqual(path.read_bytes(),before)

    def test_invalid_event_digest_refused(self):
        self.event['created_utc']='changed';self.notification.write_text(json.dumps(self.event))
        with self.assertRaisesRegex(ValueError,'event digest'):self.deliver()

    def test_no_autonomous_or_non_delivery_envelope(self):
        for key,value in [('autonomous',True),('delivery_only',False)]:
            with self.subTest(key=key),patch.dict(self.wave,{key:value}):
                with self.assertRaisesRegex(ValueError,'non-autonomous'):self.deliver()

    def test_existing_scoped_architect_event_keeps_original_ACK_protocol(self):
        folder=self.root/'channels';folder.mkdir();source=folder/'thread1.md';scope=d.scope_sha(self.wave,self.wave['sprints'][0])
        source.write_text(f'<!-- round:1 checkpoint:sprint status:AWAITING-ARCHITECT bootstrap:wave:fixture wave:fixture scope:{scope} -->')
        self.notification=d.emit(wave_id='fixture',scope=scope,thread=1,recipient='architect',number=1,status='AWAITING-ARCHITECT',source=source)
        self.server();self.assertEqual(self.deliver()['state'],'native-completed')
        self.assertFalse(self.notification.with_suffix('.read.json').exists())

    def test_bridge_CLI_refuses_watch_or_launch_combination(self):
        with patch.object(a,'deliver_existing_native') as send:
            with self.assertRaises(SystemExit):bridge.main(['--delivery-only','--deliver-existing-once','event','--control-socket','socket','--expected-binding','id','--watch'])
            send.assert_not_called()


if __name__=='__main__':unittest.main()
