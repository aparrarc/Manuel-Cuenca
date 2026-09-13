#!/usr/bin/env python3
"""Small, dependency-free booking server for the Manuel Cuenca demo."""
import hashlib, hmac, json, os, re, secrets, sqlite3, threading, uuid, mimetypes
from datetime import datetime, date, time, timedelta, timezone
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Madrid")
MAX_BODY = 32 * 1024
WRITE_LIMIT = 30
_rate_lock = threading.Lock(); _writes = {}
_sessions = {}; _session_lock = threading.Lock()
_connections = threading.local()

PROS = [("p1", "Manuel Cuenca", "physio"), ("p2", "Fernando López", "physio"),
        ("p3", "Álvaro Hurtado", "physio"), ("p4", "Víctor González", "physio"),
        ("p5", "Alex Velasco", "physio"), ("p6", "José David López", "trainer")]
SERVICES = [("physio", "Fisioterapia", "physiotherapy", 45, "p1,p2,p3,p4,p5"),
            ("osteo", "Osteopatía", "osteopathy", 60, "p1,p2"),
            ("training", "Entrenamiento personal", "training", 60, "p6")]
DEPTS = [("physiotherapy", "Fisioterapia", 1), ("osteopathy", "Osteopatía", 1),
         ("training", "Entrenamiento", 1), ("nutrition", "Nutrición", 0),
         ("psychology", "Psicología", 0)]

def db_path(): return os.environ.get("DATABASE_PATH", "/data/manuel-cuenca.sqlite3")
def conn():
    p = Path(db_path()); p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(p), timeout=10, check_same_thread=False)
    c.row_factory = sqlite3.Row; c.execute("PRAGMA foreign_keys=ON")
    if not hasattr(_connections, "items"): _connections.items = []
    _connections.items.append(c)
    return c
def init_db(c=None):
    own = c is None; c = c or conn()
    token_key()
    c.executescript("""CREATE TABLE IF NOT EXISTS bookings(
      id TEXT PRIMARY KEY, service_id TEXT NOT NULL, professional_id TEXT NOT NULL,
      start TEXT NOT NULL, end TEXT NOT NULL, customer_name TEXT NOT NULL, phone TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'confirmed', management_token_hash TEXT NOT NULL,
      management_token TEXT NOT NULL DEFAULT '', idempotency_key TEXT, idempotency_payload TEXT, created_at TEXT NOT NULL);
      CREATE UNIQUE INDEX IF NOT EXISTS booking_idem ON bookings(idempotency_key) WHERE idempotency_key IS NOT NULL;
      CREATE INDEX IF NOT EXISTS booking_prof_time ON bookings(professional_id,start,end);
      CREATE TABLE IF NOT EXISTS booking_operations(idempotency_key TEXT PRIMARY KEY, booking_id TEXT NOT NULL, payload TEXT NOT NULL, result TEXT NOT NULL);""")
    cols={r[1] for r in c.execute("PRAGMA table_info(bookings)")}
    if "management_token" not in cols: c.execute("ALTER TABLE bookings ADD COLUMN management_token TEXT NOT NULL DEFAULT ''")
    if own: c.commit(); c.close()


def token_key():
    path = Path(os.environ.get('MANAGEMENT_KEY_FILE', str(Path(db_path()).parent / 'management.key')))
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(secrets.token_bytes(32))
    key = path.read_bytes()
    if len(key) != 32: raise RuntimeError('management key unavailable')
    return key

def management_token(booking_id):
    return hmac.new(token_key(), booking_id.encode(), hashlib.sha256).hexdigest()

def catalog():
    return {"professionals":[{"id":i,"name":n,"role":r} for i,n,r in PROS],
      "services":[{"id":i,"name":n,"department":d,"duration":du,"professionalIds":ps.split(',')} for i,n,d,du,ps in SERVICES],
      "departments":[{"id":i,"name":n,"enabled":bool(e)} for i,n,e in DEPTS], "demo":True,
      "whatsappEnabled": bool(os.environ.get('NOTIFICATION_WEBHOOK_URL','').startswith('https://') and os.environ.get('NOTIFICATION_TOKEN_FILE'))}
def now_local(): return datetime.now(TZ)
def parse_start(v):
    if not isinstance(v,str): raise ValueError("start must be ISO datetime")
    x = datetime.fromisoformat(v.replace("Z", "+00:00"))
    if x.tzinfo is None: raise ValueError("start timezone required")
    return x.astimezone(TZ)
def iso(x): return x.isoformat(timespec="minutes")
def rules(service, pid, s):
    if not any(x[0]==service for x in SERVICES): raise ValueError("unknown service")
    row = next(x for x in SERVICES if x[0]==service)
    if pid not in row[4].split(','): raise ValueError("professional is not compatible")
    if s <= now_local(): raise ValueError("start must be in the future")
    if s.date() > (now_local()+timedelta(days=90)).date(): raise ValueError("date exceeds 90 days")
    if s.second or s.microsecond or s.minute % 15: raise ValueError("start must be on 15 minute grid")
    if s.weekday() >= 5: raise ValueError("outside business hours")
    end=s+timedelta(minutes=row[3]); a=time(8); b=time(14); c=time(16); d=time(20)
    if end.date() != s.date(): raise ValueError("outside business hours")
    if not ((a <= s.timetz().replace(tzinfo=None) < b and a < end.timetz().replace(tzinfo=None) <= b) or (c <= s.timetz().replace(tzinfo=None) < d and c < end.timetz().replace(tzinfo=None) <= d)): raise ValueError("outside business hours")
    return end
def validate_person(body):
    n=body.get("customerName"); p=body.get("phone"); k=body.get("idempotencyKey")
    if not isinstance(n,str) or not 2<=len(n.strip())<=120: raise ValueError("invalid customerName")
    if not isinstance(p,str) or not 3<=len(p.strip())<=40: raise ValueError("invalid phone")
    if k is not None and (not isinstance(k,str) or not 1<=len(k)<=128): raise ValueError("invalid idempotencyKey")
    if body.get('whatsappConsent') is not None and not isinstance(body['whatsappConsent'],bool): raise ValueError("invalid whatsappConsent")
def overlap(c,pid,s,e,exclude=None):
    q="SELECT * FROM bookings WHERE professional_id=? AND status='confirmed' AND start < ? AND end > ?"; args=[pid,iso(e),iso(s)]
    if exclude: q += " AND id != ?"; args.append(exclude)
    return c.execute(q,args).fetchone()
def booking_json(r): return {"id":r["id"],"serviceId":r["service_id"],"professionalId":r["professional_id"],"start":r["start"],"end":r["end"],"customerName":r["customer_name"],"phone":r["phone"],"status":r["status"]}

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(15)
    def handle_one_request(self):
        try:
            super().handle_one_request()
        finally:
            for connection in getattr(_connections, 'items', []):
                connection.close()
            _connections.items = []

    server_version="ManuelBooking/1.0"
    def log_message(self, fmt,*args): pass
    def send_json(self,status,obj,extra=None):
        raw=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(raw))); self.send_header("Cache-Control","no-store"); self.send_header("X-Robots-Tag","noindex, nofollow")
        for k,v in (extra or {}).items(): self.send_header(k,v)
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(raw)
    def error(self,status,msg): self.send_json(status,{"error":{"code":HTTPStatus(status).phrase.lower().replace(' ','_'),"message":msg}})
    def body(self):
        try:
            n=int(self.headers.get("Content-Length","-1"))
            if n<0 or n>MAX_BODY: raise ValueError("invalid body size")
            x=json.loads(self.rfile.read(n));
            if not isinstance(x,dict): raise ValueError("JSON object required")
            return x
        except Exception as e: raise ValueError(str(e))
    def do_GET(self):
        try:
            u=urlparse(self.path); q=parse_qs(u.query)
            if u.path=="/healthz": return self.send_json(200,{"ok":True})
            if u.path=="/api/catalog": return self.send_json(200,catalog())
            if u.path=="/api/admin/session": return self.send_json(200,{"authenticated":self.admin_ok()})
            if u.path=="/api/admin/bookings":
                if not self.admin_ok(): return self.error(401,"authentication required")
                c=conn(); rows=c.execute("SELECT * FROM bookings WHERE (?='' OR substr(start,1,10)=?) AND (?='' OR professional_id=?) ORDER BY start",(q.get('date',[''])[0],q.get('date',[''])[0],q.get('professionalId',[''])[0],q.get('professionalId',[''])[0])).fetchall(); c.close(); return self.send_json(200,{"bookings":[booking_json(r) for r in rows]})
            if u.path=="/api/availability":
                sid=q.get("serviceId",[""])[0]; pid=q.get("professionalId",[""])[0]; day=date.fromisoformat(q.get("date",[""])[0]); svc=next((x for x in SERVICES if x[0]==sid),None)
                if not svc: raise ValueError("unknown service")
                if day < now_local().date() or day > (now_local()+timedelta(days=90)).date(): raise ValueError("date outside booking window")
                if pid and pid not in svc[4].split(','): raise ValueError("professional is not compatible")
                pids=[pid] if pid else svc[4].split(','); out=[]; c=conn()
                for p in pids:
                    if p not in svc[4].split(','): continue
                    t=datetime.combine(day,time(8),TZ)
                    while t.time()<time(20):
                        e=t+timedelta(minutes=svc[3]); local=t.time();
                        try: rules(sid,p,t)
                        except ValueError: t+=timedelta(minutes=15); continue
                        if not overlap(c,p,t,e): out.append({"professionalId":p,"start":iso(t),"end":iso(e)})
                        t+=timedelta(minutes=15)
                c.close(); return self.send_json(200,{"slots":out})
            if u.path.startswith("/api/bookings/"):
                bid=unquote(u.path.rsplit('/',1)[1]); c=conn(); r=c.execute("SELECT * FROM bookings WHERE id=?",(bid,)).fetchone(); c.close()
                if not r: return self.error(404,"booking not found")
                if not self.booking_auth(r): return self.error(401,"authentication required")
                return self.send_json(200,{"booking":booking_json(r)})
            if u.path.startswith('/api/'): return self.error(404,"not found")
            return self.static(u.path)
        except (ValueError,KeyError) as e: self.error(400,str(e))
        except Exception: self.error(500,"internal server error")
    def do_POST(self):
        try:
            try: from . import voice
            except ImportError: import voice
            if voice.handle(self): return
            self.mutate("POST")
        except ValueError as e: self.error(400,str(e))
        except Exception: self.error(500,"internal server error")
    def do_PATCH(self):
        try: self.mutate("PATCH")
        except ValueError as e: self.error(400,str(e))
        except Exception: self.error(500,"internal server error")
    def do_DELETE(self):
        try: self.mutate("DELETE")
        except ValueError as e: self.error(400,str(e))
        except Exception: self.error(500,"internal server error")
    def do_HEAD(self):
        self.do_GET()
    def admin_ok(self):
        sid=self.cookies().get("admin_session");
        with _session_lock: return bool(sid and _sessions.get(sid,0)>datetime.now().timestamp())
    def cookies(self):
        out={}
        for p in self.headers.get("Cookie","").split(';'):
            if '=' in p: k,v=p.strip().split('=',1); out[k]=v
        return out
    def booking_auth(self,r):
        if self.admin_ok(): return True
        token=self.headers.get("X-Management-Token",""); return bool(token) and hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(),r["management_token_hash"])
    def webhook_ok(self):
        auth=self.headers.get("Authorization",""); path=os.environ.get("WEBHOOK_TOKEN_FILE","")
        if not path or not auth.startswith("Bearer "): return False
        try: expected=Path(path).read_text().strip(); return bool(expected) and hmac.compare_digest(auth[7:],expected)
        except OSError: return False
    def mutate(self,method):
        u=urlparse(self.path); istool=u.path.startswith('/api/tools/'); isadmin=u.path=="/api/admin/login" or u.path=="/api/admin/logout"
        if method=="POST" and u.path=="/api/admin/login":
            if not self.rate_ok(): return self.error(429,"rate limit exceeded")
            b=self.body()
            try: pw=Path(os.environ.get("ADMIN_PASSWORD_FILE","/run/secrets/admin_password")).read_text().strip()
            except OSError: return self.error(401,"invalid credentials")
            if not pw: return self.error(401,"invalid credentials")
            if not hmac.compare_digest(str(b.get('password','')),pw): return self.error(401,"invalid credentials")
            sid=secrets.token_urlsafe(32)
            with _session_lock: _sessions[sid]=datetime.now().timestamp()+8*3600
            return self.send_json(200,{"authenticated":True},{"Set-Cookie":f"admin_session={sid}; Path=/; Max-Age=28800; HttpOnly; Secure; SameSite=Strict"})
        if method=="POST" and u.path=="/api/admin/logout":
            sid=self.cookies().get("admin_session");
            with _session_lock: _sessions.pop(sid,None)
            return self.send_json(200,{"authenticated":False},{"Set-Cookie":"admin_session=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict"})
        if istool and not self.webhook_ok(): return self.error(401,"authentication required")
        if method=="POST" and istool and u.path.endswith('/availability'):
            b=self.body(); sid=b.get('serviceId'); day=b.get('date');
            try:
                svc=next(x for x in SERVICES if x[0]==sid); d=date.fromisoformat(day)
                if d < now_local().date() or d > (now_local()+timedelta(days=90)).date(): raise ValueError("date outside booking window")
                pids=[b.get('professionalId')] if b.get('professionalId') else svc[4].split(','); c=conn(); out=[]
                for p in pids:
                    if p not in svc[4].split(','): raise ValueError("professional is not compatible")
                    t=datetime.combine(d,time(8),TZ)
                    while t.time()<time(20):
                        e=t+timedelta(minutes=svc[3]);
                        try: rules(sid,p,t)
                        except ValueError: t+=timedelta(minutes=15); continue
                        if not overlap(c,p,t,e): out.append({'professionalId':p,'start':iso(t),'end':iso(e)})
                        t+=timedelta(minutes=15)
                c.close(); return self.send_json(200,{'slots':out})
            except (ValueError,StopIteration,TypeError) as e: return self.error(400,str(e))
        if method=="POST" and u.path=="/api/bookings" or (method=="POST" and u.path=="/api/admin/bookings") or (method=="POST" and istool and u.path.endswith('/book')):
            if u.path=="/api/admin/bookings" and not self.admin_ok(): return self.error(401,"authentication required")
            if istool:
                caller=self.headers.get("X-ElevenLabs-Caller-Id","")
                if not re.fullmatch(r'\+?[0-9]{7,15}', caller): return self.error(403,"caller identity required")
            if not isadmin and not istool and not self.rate_ok(): return self.error(429,"rate limit exceeded")
            b=self.body()
            if istool: b['phone']=self.headers.get('X-ElevenLabs-Caller-Id','')
            return self.create(b,201)
        if method=="POST" and istool and u.path.endswith('/cancel'):
            b=self.body(); return self.tool_cancel(b)
        if method=="POST" and istool and u.path.endswith('/reschedule'):
            b=self.body(); return self.tool_reschedule(b)
        if u.path.startswith('/api/bookings/'):
            bid=unquote(u.path.rsplit('/',1)[1]); c=conn(); c.execute("BEGIN IMMEDIATE"); r=c.execute("SELECT * FROM bookings WHERE id=?",(bid,)).fetchone()
            if not r: c.rollback(); c.close(); return self.error(404,"booking not found")
            if not self.booking_auth(r): c.rollback(); c.close(); return self.error(401,"authentication required")
            if method=="DELETE" or (istool and u.path.endswith('/cancel')):
                if r['status']=='cancelled': c.commit(); c.close(); return self.send_json(200,{"booking":booking_json(r)})
                c.execute("UPDATE bookings SET status='cancelled' WHERE id=?",(bid,)); c.commit(); c.close(); return self.send_json(200,{"booking":dict(booking_json(r),status="cancelled")})
            if r['status'] != 'confirmed': c.close(); return self.error(409,"booking is cancelled")
            b=self.body(); s=parse_start(b.get('start')); pid=b.get('professionalId',r['professional_id']); end=rules(r['service_id'],pid,s); idem=b.get('idempotencyKey')
            if idem:
                op_payload=json.dumps({'bookingId':bid,'start':b.get('start'),'professionalId':pid},sort_keys=True)
                op=c.execute("SELECT * FROM booking_operations WHERE idempotency_key=?",(idem,)).fetchone()
                if op:
                    if op['payload']!=op_payload: c.rollback(); c.close(); return self.error(409,"idempotency payload mismatch")
                    fresh=c.execute("SELECT * FROM bookings WHERE id=?",(bid,)).fetchone(); c.commit(); c.close(); return self.send_json(200,{"booking":booking_json(fresh)})
            if overlap(c,pid,s,end,bid): c.rollback(); c.close(); return self.error(409,"time slot unavailable")
            c.execute("UPDATE bookings SET professional_id=?,start=?,end=? WHERE id=?",(pid,iso(s),iso(end),bid));
            if idem: c.execute("INSERT INTO booking_operations VALUES(?,?,?,?)",(idem,bid,op_payload,json.dumps({'bookingId':bid})))
            c.commit(); x=c.execute("SELECT * FROM bookings WHERE id=?",(bid,)).fetchone(); c.close(); return self.send_json(200,{"booking":booking_json(x)})
        return self.error(404,"not found")
    def rate_ok(self):
        now=datetime.now().timestamp(); ip=self.client_address[0]
        with _rate_lock:
            vals=[x for x in _writes.get(ip,[]) if x>now-60]; _writes[ip]=vals
            if len(vals)>=WRITE_LIMIT:return False
            vals.append(now); return True
    def create(self,b,status):
        try: validate_person(b); sid=b["serviceId"]; pid=b["professionalId"]; s=parse_start(b["start"]); end=rules(sid,pid,s)
        except (KeyError,ValueError) as e: return self.error(400,str(e))
        payload=json.dumps({k:b.get(k) for k in ('serviceId','professionalId','start','customerName','phone','whatsappConsent')},sort_keys=True); idem=b.get('idempotencyKey'); c=conn()
        c.execute("BEGIN IMMEDIATE")
        if idem:
            old=c.execute("SELECT * FROM bookings WHERE idempotency_key=?",(idem,)).fetchone()
            if old:
                c.rollback(); c.close()
                if old['idempotency_payload']!=payload:return self.error(409,"idempotency payload mismatch")
                try:
                    nc=conn()
                    try: wr=nc.execute("SELECT status FROM notification_outbox WHERE booking_id=? ORDER BY rowid DESC LIMIT 1",(old['id'],)).fetchone()
                    finally: nc.close()
                    ws={'status':wr['status']} if wr else {'status':'skipped','reason':'consent_not_given'}
                except Exception: ws={'status':'skipped','reason':'consent_not_given'}
                return self.send_json(200,{"booking":booking_json(old),"managementToken":management_token(old["id"]),"whatsapp":ws})
        if overlap(c,pid,s,end): c.rollback(); c.close(); return self.error(409,"time slot unavailable")
        bid=uuid.uuid4().hex; token=management_token(bid); c.execute("INSERT INTO bookings (id,service_id,professional_id,start,end,customer_name,phone,status,management_token_hash,management_token,idempotency_key,idempotency_payload,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(bid,sid,pid,iso(s),iso(end),b['customerName'].strip(),b['phone'].strip(),'confirmed',hashlib.sha256(token.encode()).hexdigest(),'',idem,payload,datetime.now(timezone.utc).isoformat()))
        whatsapp={'status':'skipped','reason':'consent_not_given'}
        if b.get('whatsappConsent') is True:
            from . import notifications
            recipient=notifications._phone(b['phone'])
            if not recipient: c.rollback(); c.close(); return self.error(400,'valid WhatsApp mobile required')
            whatsapp=notifications.enqueue(c,uuid.uuid4().hex,dict(booking_json(c.execute("SELECT * FROM bookings WHERE id=?",(bid,)).fetchone()),phone=recipient))
        c.commit(); r=c.execute("SELECT * FROM bookings WHERE id=?",(bid,)).fetchone(); c.close(); return self.send_json(status,{"booking":booking_json(r),"managementToken":token,"whatsapp":whatsapp})
    def tool_row(self,b,c):
        bid=b.get("bookingId") or b.get("id")
        if not isinstance(bid,str): raise ValueError("bookingId required")
        r=c.execute("SELECT * FROM bookings WHERE id=?",(bid,)).fetchone()
        if not r: raise LookupError("booking not found")
        caller=self.headers.get("X-ElevenLabs-Caller-Id","")
        # Caller identity is required for future telephony integration; until callers
        # are persisted, reject mutations rather than allowing bearer-wide access.
        if not caller: raise PermissionError("caller identity required")
        normalized=''.join(ch for ch in r['phone'] if ch.isdigit())
        if ''.join(ch for ch in caller if ch.isdigit()) != normalized: raise PermissionError("caller does not own booking")
        return r
    def tool_cancel(self,b):
        c=conn()
        try:
            c.execute('BEGIN IMMEDIATE'); r=self.tool_row(b,c); c.execute("UPDATE bookings SET status='cancelled' WHERE id=?",(r['id'],)); c.commit(); return self.send_json(200,{"booking":dict(booking_json(r),status="cancelled")})
        except PermissionError as e: return self.error(403,str(e))
        except LookupError as e: return self.error(404,str(e))
        finally: c.close()
    def tool_reschedule(self,b):
        c=conn()
        try:
            c.execute('BEGIN IMMEDIATE'); r=self.tool_row(b,c)
            if r['status'] != 'confirmed': return self.error(409,"booking is cancelled")
            s=parse_start(b.get('start')); pid=b.get('professionalId',r['professional_id']); end=rules(r['service_id'],pid,s)
            if overlap(c,pid,s,end,r['id']): c.rollback(); return self.error(409,"time slot unavailable")
            c.execute("UPDATE bookings SET professional_id=?,start=?,end=? WHERE id=?",(pid,iso(s),iso(end),r['id'])); c.commit(); n=c.execute("SELECT * FROM bookings WHERE id=?",(r['id'],)).fetchone(); return self.send_json(200,{"booking":booking_json(n)})
        except PermissionError as e: return self.error(403,str(e))
        except LookupError as e: return self.error(404,str(e))
        except (ValueError,KeyError) as e: return self.error(400,str(e))
        finally: c.close()
    def static(self,path):
        root=Path(os.environ.get("STATIC_DIR",str(Path(__file__).parent.parent/"dist"))).resolve(); rel=unquote(path.lstrip('/')) or 'index.html'; f=(root/rel).resolve()
        if root not in f.parents and f!=root: return self.error(404,"not found")
        if not f.is_file() and path in ('/', '/booking', '/admin'): f=root/'index.html'
        if not f.is_file(): return self.error(404,"not found")
        data=f.read_bytes(); self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(str(f))[0] or 'application/octet-stream'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Robots-Tag','noindex, nofollow'); self.send_header('Content-Length',str(len(data))); self.end_headers()
        if self.command != "HEAD": self.wfile.write(data)

def main():
    os.umask(0o077)
    c=conn(); init_db(c); c.commit(); c.close(); port=int(os.environ.get('PORT','8080')); ThreadingHTTPServer(('',port),Handler).serve_forever()
if __name__=='__main__': main()
