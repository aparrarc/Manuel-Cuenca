import concurrent.futures
import json
import os
import secrets
import tempfile
import threading
import unittest
from datetime import datetime, timedelta
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from server import server as api

class BookingHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        os.environ['DATABASE_PATH'] = str(self.root / 'bookings.sqlite')
        os.environ['STATIC_DIR'] = str(self.root)
        (self.root / 'index.html').write_text('<h1>Demo</h1>')
        (self.root / 'app.js').write_text('export const ok = true;')
        self.password = secrets.token_urlsafe(24)
        self.tool = secrets.token_urlsafe(24)
        (self.root / 'admin').write_text(self.password)
        (self.root / 'tool').write_text(self.tool)
        os.environ['ADMIN_PASSWORD_FILE'] = str(self.root / 'admin')
        os.environ['WEBHOOK_TOKEN_FILE'] = str(self.root / 'tool')
        api._writes.clear(); api._sessions.clear()
        api.init_db()
        self.http = api.ThreadingHTTPServer(('127.0.0.1', 0), api.Handler)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        day = datetime.now(ZoneInfo('Europe/Madrid')).date() + timedelta(days=2)
        while day.weekday() >= 5: day += timedelta(days=1)
        self.day = day
    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.temp.cleanup()
    def req(self, method, path, body=None, headers=None):
        c=HTTPConnection('127.0.0.1', self.http.server_port, timeout=5)
        h={'Content-Type':'application/json'}; h.update(headers or {})
        c.request(method,path,json.dumps(body) if body is not None else None,h)
        r=c.getresponse(); raw=r.read(); self.last_headers=dict(r.getheaders()); code=r.status; c.close()
        try: data=json.loads(raw)
        except json.JSONDecodeError: data=raw.decode()
        return code,data
    def start(self,hour=9,minute=0,day=None):
        return datetime.combine(day or self.day, datetime.min.time(), ZoneInfo('Europe/Madrid')).replace(hour=hour,minute=minute).isoformat()
    def body(self,**kw):
        b=dict(serviceId='physio',professionalId='p1',start=self.start(),customerName='Persona Demo',phone='+34600000000',idempotencyKey=secrets.token_hex(16)); b.update(kw); return b
    def create(self,**kw):
        b=self.body(**kw); code,out=self.req('POST','/api/bookings',b); self.assertEqual(code,201,out); return b,out
    def test_six_calendars_service_compatibility(self):
        code,catalog=self.req('GET','/api/catalog'); self.assertEqual(code,200); self.assertEqual(len(catalog['professionals']),6)
        for pro in catalog['professionals']:
            service='training' if pro['id']=='p6' else 'physio'
            self.create(serviceId=service,professionalId=pro['id'])
        self.assertEqual(self.req('POST','/api/bookings',self.body(professionalId='p6'))[0],400)
    def test_concurrent_overlap_and_adjacent_slot(self):
        barrier=threading.Barrier(2)
        def attempt(i):
            b=self.body(customerName=f'Demo {i}'); barrier.wait(); return self.req('POST','/api/bookings',b)[0]
        with concurrent.futures.ThreadPoolExecutor(2) as pool: codes=list(pool.map(attempt,range(2)))
        self.assertEqual(sorted(codes),[201,409])
        self.assertEqual(self.req('POST','/api/bookings',self.body(start=self.start(9,15)))[0],409)
        self.create(start=self.start(9,45))
    def test_retry_preserves_management_capability_and_rejects_changed_payload(self):
        b,one=self.create(); code,two=self.req('POST','/api/bookings',b)
        self.assertEqual(code,200); self.assertEqual(one['booking']['id'],two['booking']['id'])
        self.assertTrue(two['managementToken']); self.assertTrue(secrets.compare_digest(one['managementToken'],two['managementToken']))
        self.assertEqual(self.req('POST','/api/bookings',dict(b,customerName='Changed Demo'))[0],409)
    def test_management_requires_token_move_cancel_and_releases(self):
        _,one=self.create(); bid=one['booking']['id']; path='/api/bookings/'+bid
        self.assertEqual(self.req('GET',path)[0],401)
        self.assertEqual(self.req('PATCH',path,{'start':self.start(11)})[0],401)
        headers={'X-Management-Token':one['managementToken']}
        move={'start':self.start(11),'professionalId':'p2','idempotencyKey':'move-1'}
        self.assertEqual(self.req('PATCH',path,move,headers)[0],200)
        self.assertEqual(self.req('PATCH',path,move,headers)[0],200)
        self.assertEqual(self.req('PATCH',path,dict(move,start=self.start(12)),headers)[0],409)
        self.create() # old slot released
        self.assertEqual(self.req('DELETE',path,headers=headers)[0],200)
        self.assertEqual(self.req('DELETE',path,headers=headers)[0],200)
        self.assertEqual(self.req('PATCH',path,dict(move,idempotencyKey='new'),headers)[0],409)
        self.create(start=self.start(11),professionalId='p2')
    def test_move_conflict_preserves_original(self):
        _,one=self.create(); self.create(start=self.start(11))
        headers={'X-Management-Token':one['managementToken']}; path='/api/bookings/'+one['booking']['id']
        self.assertEqual(self.req('PATCH',path,{'start':self.start(11),'idempotencyKey':'busy'},headers)[0],409)
        self.assertEqual(self.req('GET',path,headers=headers)[1]['booking']['start'][:16],self.start()[:16])
    def test_availability_has_no_weekends_or_past_and_hides_busy_slots(self):
        weekend=self.day
        while weekend.weekday()!=5: weekend+=timedelta(days=1)
        def slots(day,pro='p1'):
            return self.req('GET','/api/availability?'+urlencode(dict(serviceId='physio',professionalId=pro,date=str(day))))
        self.assertEqual(slots(weekend)[1]['slots'],[])
        self.assertEqual(slots(self.day,'missing')[0],400)
        self.assertEqual(slots(self.day-timedelta(days=100))[0],400)
        self.create(); code,out=slots(self.day); self.assertEqual(code,200)
        self.assertFalse(any(x['start'][:16]==self.start()[:16] for x in out['slots']))
        for slot in out['slots']: api.rules('physio','p1',api.parse_start(slot['start']))
        self.assertEqual(self.req('POST','/api/bookings',self.body(start=self.start(day=weekend)))[0],400)
        self.assertEqual(self.req('POST','/api/bookings',self.body(start=self.start(13,45)))[0],400)
        self.assertEqual(self.req('POST','/api/bookings',self.body(start=self.start(23,45)))[0],400)
    def test_admin_secure_cookie_logout_and_closed_missing_password(self):
        self.assertEqual(self.req('GET','/api/admin/bookings')[0],401)
        self.assertEqual(self.req('POST','/api/admin/login',{'password':'not-the-password'})[0],401)
        self.assertEqual(self.req('POST','/api/admin/login',{'password':self.password})[0],200)
        cookie=self.last_headers['Set-Cookie']; self.assertIn('Secure',cookie); self.assertIn('HttpOnly',cookie); self.assertIn('SameSite=Strict',cookie)
        headers={'Cookie':cookie.split(';')[0]}
        self.assertEqual(self.req('GET','/api/admin/bookings',headers=headers)[0],200)
        self.req('POST','/api/admin/logout',{},headers)
        self.assertEqual(self.req('GET','/api/admin/bookings',headers=headers)[0],401)
        (self.root/'admin').write_text('')
        self.assertEqual(self.req('POST','/api/admin/login',{'password':''})[0],401)
    def test_tools_require_auth_and_caller_ownership(self):
        self.assertEqual(self.req('POST','/api/tools/book',self.body())[0],401)
        auth={'Authorization':'Bearer '+self.tool,'X-ElevenLabs-Caller-Id':'+34600000000'}
        b=self.body(); b.pop('phone'); code,one=self.req('POST','/api/tools/book',b,auth); self.assertEqual(code,201,one)
        wrong=dict(auth,**{'X-ElevenLabs-Caller-Id':'+34600000001'})
        self.assertEqual(self.req('POST','/api/tools/cancel',{'bookingId':one['booking']['id']},wrong)[0],403)
        self.assertEqual(self.req('POST','/api/tools/cancel',{'bookingId':one['booking']['id']},auth)[0],200)
    def test_invalid_change_does_not_leave_database_locked(self):
        _,one=self.create(); path='/api/bookings/'+one['booking']['id']
        headers={'X-Management-Token':one['managementToken']}
        self.assertEqual(self.req('PATCH',path,{'start':'not-a-date'},headers)[0],400)
        self.create(start=self.start(12))
    def test_tools_weekend_availability_closed(self):
        weekend=self.day
        while weekend.weekday()!=5: weekend+=timedelta(days=1)
        auth={'Authorization':'Bearer '+self.tool}
        code,data=self.req('POST','/api/tools/availability',{'serviceId':'physio','date':str(weekend)},auth)
        self.assertEqual(code,200); self.assertEqual(data['slots'],[])
        (self.root/'tool').write_text('')
        self.assertEqual(self.req('POST','/api/tools/availability',{}, {'Authorization':'Bearer '})[0],401)
    def test_invalid_body_unknown_api_and_static_mime(self):
        self.assertEqual(self.req('POST','/api/bookings',[])[0],400)
        self.assertEqual(self.req('GET','/api/missing')[0],404)
        self.assertEqual(self.req('GET','/app.js')[0],200)
        self.assertIn('javascript',self.last_headers['Content-Type'])
        self.assertIn('noindex',self.last_headers.get('X-Robots-Tag',''))

if __name__=='__main__': unittest.main()
