import os, sqlite3, tempfile, threading, unittest
from unittest.mock import patch
from . import notifications

class NotificationTests(unittest.TestCase):
    def setUp(self): self.c=sqlite3.connect(':memory:',check_same_thread=False); self.c.row_factory=sqlite3.Row; notifications.init(self.c)
    def tearDown(self): self.c.close()
    def test_enqueue_unique_and_demo_skip(self):
        b={'id':'b1','phone':'34600123123','start':'2026-10-01T09:00+02:00'}
        b['phone']='demo:abc'; self.assertEqual(notifications.enqueue(self.c,'op0',b)['status'],'skipped')
        b['phone']='34600123123'; self.assertEqual(notifications.enqueue(self.c,'op1',b)['status'],'queued'); self.assertEqual(notifications.enqueue(self.c,'op1',b)['status'],'already_queued'); self.c.commit(); self.assertEqual(self.c.execute('select count(*) from notification_outbox').fetchone()[0],1)
    def test_missing_config_does_not_consume(self):
        os.environ.pop('NOTIFICATION_WEBHOOK_URL',None); os.environ.pop('NOTIFICATION_TOKEN_FILE',None); notifications.enqueue(self.c,'op2',{'id':'b2','phone':'+34600123123','start':'2026-10-01T09:00+02:00'}); self.c.commit(); self.assertEqual(notifications.process_pending(self.c)['status'],'disabled'); self.assertEqual(self.c.execute("select status from notification_outbox").fetchone()[0],'pending')
    def test_ambiguous_no_retry(self):
        self.c.execute("insert into notification_outbox values('x','x','booking_confirmation','+34600123123','b','{}','pending',null,null,null)"); self.c.commit();
        old=dict(os.environ); os.environ['NOTIFICATION_WEBHOOK_URL']='https://notify.invalid'; f=tempfile.NamedTemporaryFile(mode='w'); f.write('secret'); f.flush(); os.environ['NOTIFICATION_TOKEN_FILE']=f.name
        def fail(*a,**k): raise TimeoutError('ambiguous')
        with patch('urllib.request.OpenerDirector.open',fail): self.assertEqual(notifications.process_pending(self.c)['processed'],1)
        self.assertEqual(self.c.execute("select status from notification_outbox").fetchone()[0],'unknown'); os.environ.clear(); os.environ.update(old)
