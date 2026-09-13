import json, os, tempfile, threading, unittest
from datetime import datetime, timedelta
from http.client import HTTPConnection
from zoneinfo import ZoneInfo
from .server import ThreadingHTTPServer, Handler, conn, init_db

class VoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); cls.old={k:os.environ.get(k) for k in ('DATABASE_PATH','VOICE_TOKEN_FILE','WEBHOOK_TOKEN_FILE','ELEVENLABS_AGENT_ID','VOICE_PREVIEW_ENABLED')}
        token=os.path.join(cls.tmp.name,'voice-token')
        with open(token,'w') as fh: fh.write('voice-secret')
        os.environ.update(DATABASE_PATH=os.path.join(cls.tmp.name,'db.sqlite'), VOICE_TOKEN_FILE=token, WEBHOOK_TOKEN_FILE='', ELEVENLABS_AGENT_ID='agent-test', VOICE_PREVIEW_ENABLED='true')
        c=conn(); init_db(c); c.commit(); c.close(); cls.s=ThreadingHTTPServer(('127.0.0.1',0),Handler); threading.Thread(target=cls.s.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.s.shutdown(); cls.s.server_close()
        for k,v in cls.old.items():
            if v is None: os.environ.pop(k,None)
            else: os.environ[k]=v
        cls.tmp.cleanup()
    def req(self,path,body,caller='+34600123123',conversation='voice-test'):
        c=HTTPConnection('127.0.0.1',self.s.server_port); h={'Authorization':'Bearer voice-secret','X-ElevenLabs-Agent-Id':'agent-test','X-ElevenLabs-Conversation-Id':conversation,'X-ElevenLabs-Caller-Id':caller,'Content-Type':'application/json'}; c.request('POST',path,json.dumps(body),h); r=c.getresponse(); return r.status,json.loads(r.read())
    def start(self,hour='09:00'):
        d=datetime.now(ZoneInfo('Europe/Madrid'))+timedelta(days=3)
        while d.weekday()>4: d+=timedelta(days=1)
        hh,mm=map(int,hour.split(':')); return d.replace(hour=hh,minute=mm,second=0,microsecond=0).isoformat()
    def test_prepare_does_not_mutate_then_confirm_replay(self):
        b={'action':'create','serviceId':'physio','professionalId':'p1','start':self.start(),'customerName':'Voice User'}
        before=len(conn().execute('SELECT * FROM bookings').fetchall())
        st,x=self.req('/api/voice/v1/prepare',b); self.assertEqual(st,200)
        self.assertEqual(len(conn().execute('SELECT * FROM bookings').fetchall()),before)
        cst,y=self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']}); self.assertEqual(cst,200)
        self.assertEqual(self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']})[1],y)
        self.booking=y['booking']
    def test_ownership_and_conversation_scope(self):
        b={'action':'create','serviceId':'physio','professionalId':'p2','start':self.start('10:00'),'customerName':'Owner'}
        _,x=self.req('/api/voice/v1/prepare',b,caller='+34600123124',conversation='owner-conv')
        self.assertEqual(self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},caller='+34600123125',conversation='owner-conv')[0],403)
        self.assertEqual(self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},caller='+34600123124',conversation='other-conv')[0],403)
    def test_reschedule_cancel_and_normalized_phone(self):
        # 9-digit Spanish caller normalizes to the same E.164 owner.
        caller='+34600123126'; b={'action':'create','serviceId':'osteo','professionalId':'p1','start':self.start('12:00'),'customerName':'Move'}
        _,x=self.req('/api/voice/v1/prepare',b,caller=caller,conversation='move'); _,created=self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},caller=caller,conversation='move'); bid=created['booking']['id']
        c=conn(); c.execute("UPDATE bookings SET phone='600123126' WHERE id=?",(bid,)); c.commit(); c.close()
        _,x=self.req('/api/voice/v1/prepare',{'action':'reschedule','bookingId':bid,'start':self.start('13:00')},caller=caller,conversation='move2'); st,moved=self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},caller=caller,conversation='move2'); self.assertEqual(st,200); self.assertIn('13:00',moved['booking']['start'])
        _,x=self.req('/api/voice/v1/prepare',{'action':'cancel','bookingId':bid},caller=caller,conversation='move3'); st,cancelled=self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},caller=caller,conversation='move3'); self.assertEqual(st,200); self.assertEqual(cancelled['booking']['status'],'cancelled')
    def test_manual_whatsapp_requires_consent_and_is_separate(self):
        b={'action':'create','serviceId':'physio','professionalId':'p4','start':self.start('11:00'),'customerName':'WhatsApp','whatsappPhone':'683498975'}
        self.assertEqual(self.req('/api/voice/v1/prepare',b,conversation='wa-no-consent')[0],409)
        b['whatsappConsent']=True; st,x=self.req('/api/voice/v1/prepare',b,conversation='wa-ok'); self.assertEqual(st,200); self.assertEqual(x['summary']['whatsappPhone'],'+34683498975')
        st,y=self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},conversation='wa-ok'); self.assertEqual(st,200); self.assertEqual(y['booking']['phone'],'34600123123')
    def test_manual_whatsapp_invalid_rejected(self):
        b={'action':'create','serviceId':'physio','professionalId':'p5','start':self.start('11:00'),'customerName':'Bad','whatsappPhone':'123','whatsappConsent':True}
        self.assertEqual(self.req('/api/voice/v1/prepare',b,conversation='wa-bad')[0],409)
    def test_prepare_overlap_rejected_and_auth(self):
        b={'action':'create','serviceId':'physio','professionalId':'p3','start':self.start('15:00'),'customerName':'Overlap'}
        self.assertEqual(self.req('/api/voice/v1/prepare',b)[0],409)
        c=HTTPConnection('127.0.0.1',self.s.server_port); c.request('POST','/api/voice/v1/catalog','{}',{'Authorization':'Bearer voice-secret','X-ElevenLabs-Agent-Id':'wrong','X-ElevenLabs-Conversation-Id':'x'}); self.assertEqual(c.getresponse().status,401)

    def test_preview_scope_and_actual_overlap(self):
        b={'action':'create','serviceId':'training','professionalId':'p6','start':self.start('10:00'),'customerName':'Demo prueba'}
        status,x=self.req('/api/voice/v1/prepare',b,caller='',conversation='preview-one'); self.assertEqual(status,200)
        status,y=self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},caller='',conversation='preview-one'); self.assertEqual(status,200)
        self.assertEqual(len(self.req('/api/voice/v1/upcoming',{},caller='',conversation='preview-one')[1]['bookings']),1)
        self.assertEqual(self.req('/api/voice/v1/upcoming',{},caller='',conversation='preview-two')[1]['bookings'],[])
        self.assertEqual(self.req('/api/voice/v1/prepare',{'action':'cancel','bookingId':y['booking']['id']},caller='',conversation='preview-two')[0],409)
        self.assertEqual(self.req('/api/voice/v1/prepare',b,caller='',conversation='preview-two')[0],409)
        os.environ['VOICE_PREVIEW_ENABLED']='false'
        try: self.assertEqual(self.req('/api/voice/v1/catalog',{},caller='not-a-phone')[0],403)
        finally: os.environ['VOICE_PREVIEW_ENABLED']='true'

    def test_manual_whatsapp_target_preserves_preview_identity(self):
        b={'action':'create','serviceId':'physio','professionalId':'p5','start':self.start('12:00'),'customerName':'Demo Whatsapp','whatsappPhone':'600123456','whatsappConsent':True}
        status,x=self.req('/api/voice/v1/prepare',b,caller='',conversation='manual-wa'); self.assertEqual(status,200)
        self.assertEqual(x['summary']['whatsappPhone'],'+34600123456')
        status,y=self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},caller='',conversation='manual-wa'); self.assertEqual(status,200)
        self.assertTrue(y['booking']['phone'].startswith('demo:'))
        c=conn(); row=c.execute('SELECT recipient_phone FROM notification_outbox WHERE booking_id=?',(y['booking']['id'],)).fetchone();c.close();self.assertEqual(row[0],'+34600123456')
        self.assertEqual(self.req('/api/voice/v1/upcoming',{},caller='+34600123456',conversation='other-person')[1]['bookings'],[])

    def test_enabled_preview_requires_whatsapp_decision(self):
        from unittest.mock import patch
        b={'action':'create','serviceId':'physio','professionalId':'p4','start':self.start('16:00'),'customerName':'Decision Demo'}
        with patch.dict(os.environ,{'NOTIFICATION_WEBHOOK_URL':'https://notify.invalid','NOTIFICATION_TOKEN_FILE':'/missing-test-file'}):
            status,x=self.req('/api/voice/v1/prepare',b,caller='',conversation='decision-test');self.assertEqual(status,409);self.assertIn('whatsapp_recipient_required',x['error']['message'])
            b['whatsappConsent']=False
            status,x=self.req('/api/voice/v1/prepare',b,caller='',conversation='decision-test');self.assertEqual(status,200)
            status,y=self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},caller='',conversation='decision-test');self.assertEqual(status,200);self.assertEqual(y['whatsapp']['reason'],'user_declined')

    def test_old_preparation_cannot_bypass_required_phone(self):
        from unittest.mock import patch
        b={'action':'create','serviceId':'physio','professionalId':'p4','start':self.start('17:00'),'customerName':'Old Demo'}
        with patch.dict(os.environ,{'NOTIFICATION_WEBHOOK_URL':'','NOTIFICATION_TOKEN_FILE':''}):
            status,x=self.req('/api/voice/v1/prepare',b,caller='',conversation='old-decision');self.assertEqual(status,200)
        with patch.dict(os.environ,{'NOTIFICATION_WEBHOOK_URL':'https://notify.invalid','NOTIFICATION_TOKEN_FILE':'/missing-test-file'}):
            status,y=self.req('/api/voice/v1/confirm',{'confirmationToken':x['confirmationToken']},caller='',conversation='old-decision');self.assertEqual(status,409)
        self.assertEqual(self.req('/api/voice/v1/upcoming',{},caller='',conversation='old-decision')[1]['bookings'],[])
