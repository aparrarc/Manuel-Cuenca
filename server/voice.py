"""Caller-scoped, two-step voice booking API (deliberately no external SDK)."""
import hashlib, hmac, json, os, re, secrets
from datetime import datetime, timedelta
from pathlib import Path
try: from . import server
except ImportError: import server

def _caller(h):
    raw=h.headers.get('X-ElevenLabs-Caller-Id',''); conv=h.headers.get('X-ElevenLabs-Conversation-Id','')
    if not conv or not re.fullmatch(r'[A-Za-z0-9._:-]{1,160}',conv): raise PermissionError('conversation identity required')
    # Browser previews may supply a non-telephone system placeholder. Never
    # interpret it as a real caller: restrict it to this conversation's demo scope.
    digits=raw[1:] if re.fullmatch(r'\+[1-9]\d{7,14}',raw) else ''
    if not digits:
        if os.environ.get('VOICE_PREVIEW_ENABLED')!='true': raise PermissionError('caller identity required')
        phone='demo:'+hashlib.sha256(conv.encode()).hexdigest()[:20]
    else: phone=digits
    return phone,conv
def _norm_phone(v):
    if isinstance(v,str) and v.startswith('demo:'): return v
    d=''.join(x for x in str(v) if x.isdigit())
    return '34'+d if len(d)==9 and d[0] in '6789' else d
def _auth(h):
    p=os.environ.get('VOICE_TOKEN_FILE',''); a=h.headers.get('Authorization','')
    if not p or not a.startswith('Bearer '): return False
    try: expected=Path(p).read_text().strip()
    except OSError: return False
    return bool(expected) and hmac.compare_digest(a[7:],expected) and h.headers.get('X-ElevenLabs-Agent-Id','')==os.environ.get('ELEVENLABS_AGENT_ID','') and bool(os.environ.get('ELEVENLABS_AGENT_ID'))
def _db():
    c=server.conn(); c.create_function('voice_phone',1,_norm_phone); c.execute('''CREATE TABLE IF NOT EXISTS voice_operations(id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL, agent TEXT NOT NULL, conversation TEXT NOT NULL, caller TEXT NOT NULL, action TEXT NOT NULL, payload TEXT NOT NULL, expires REAL NOT NULL, consumed TEXT)'''); c.commit(); return c
def handle(h):
    u=h.path.split('?',1)[0]
    if not u.startswith('/api/voice/v1/'): return False
    if not _auth(h): h.error(401,'authentication required'); return True
    try: caller,conversation=_caller(h)
    except PermissionError as e: h.error(403,str(e)); return True
    if h.command!='POST': h.error(405,'POST required'); return True
    try: b=h.body()
    except ValueError as e: h.error(400,str(e)); return True
    if u.endswith('/catalog'):
        x=server.catalog(); n=server.now_local(); x.update({'timezone':'Europe/Madrid','now':n.isoformat(timespec='minutes'),'date':n.date().isoformat(),'mode':'voice'}); h.send_json(200,x); return True
    if u.endswith('/availability'):
        sid=b.get('serviceId'); day=b.get('date'); pid=b.get('professionalId'); svc=next((x for x in server.SERVICES if x[0]==sid),None)
        try:
            if not svc: raise ValueError('unknown service')
            d=server.date.fromisoformat(day)
            if d<server.now_local().date() or d>(server.now_local()+server.timedelta(days=90)).date(): raise ValueError('date outside booking window')
            if pid and pid not in svc[4].split(','): raise ValueError('professional is not compatible')
            c=server.conn(); slots=[]
            for p in ([pid] if pid else svc[4].split(',')):
                t=server.datetime.combine(d,server.time(8),server.TZ)
                while t.time()<server.time(20):
                    e=t+server.timedelta(minutes=svc[3])
                    try: server.rules(sid,p,t)
                    except ValueError: t+=server.timedelta(minutes=15); continue
                    if not server.overlap(c,p,t,e): slots.append({'professionalId':p,'start':server.iso(t),'end':server.iso(e)})
                    t+=server.timedelta(minutes=15)
            c.close(); h.send_json(200,{'slots':slots}); return True
        except (ValueError,TypeError) as e: h.error(400,str(e)); return True
    if u.endswith('/upcoming'):
        c=_db(); rows=c.execute("SELECT * FROM bookings WHERE voice_phone(phone)=? AND status='confirmed' AND start>=? ORDER BY start LIMIT 20",(caller,server.iso(server.now_local()))).fetchall(); c.close(); rows=[x for x in rows if _norm_phone(x['phone'])==caller]; h.send_json(200,{'bookings':[server.booking_json(x) for x in rows[:20]]}); return True
    if u.endswith('/prepare'):
        action=b.get('action');
        if action not in ('create','reschedule','cancel'): h.error(400,'invalid action'); return True
        c=_db(); p=dict(b); p['phone']=caller
        try:
            if action=='create':
                server.validate_person(p); s=server.parse_start(p['start']); e=server.rules(p['serviceId'],p['professionalId'],s); sid, pid=p['serviceId'],p['professionalId']
                if server.overlap(c,pid,s,e): raise ValueError('time slot unavailable')
            else:
                r=c.execute('SELECT * FROM bookings WHERE id=?',(p.get('bookingId'),)).fetchone()
                if not r or _norm_phone(r['phone'])!=caller: raise ValueError('booking not found')
                if r['status']!='confirmed': raise ValueError('booking is cancelled')
                sid, pid=r['service_id'],p.get('professionalId',r['professional_id'])
                if action=='reschedule': s=server.parse_start(p['start']); e=server.rules(sid,pid,s); 
                if action=='reschedule' and server.overlap(c,pid,s,e,r['id']): raise ValueError('time slot unavailable')
            svc=next(x for x in server.SERVICES if x[0]==sid); pro=next(x for x in server.PROS if x[0]==pid); summary={'action':action,'service':svc[1],'professional':pro[1],'durationMinutes':svc[3],**({'start':p['start']} if 'start' in p else {}),**({'bookingId':p['bookingId']} if 'bookingId' in p else {})}
            if action!='create': summary['originalStart']=r['start']; summary['start']=server.iso(s) if action=='reschedule' else r['start']
        except (ValueError,KeyError,StopIteration,TypeError) as ex: c.close(); h.error(409,str(ex)); return True
        payload=json.dumps(b,sort_keys=True,separators=(',',':')); token=secrets.token_urlsafe(32); op=secrets.token_hex(16); c.execute('INSERT INTO voice_operations VALUES(?,?,?,?,?,?,?,?,?)',(op,hashlib.sha256(token.encode()).hexdigest(),os.environ['ELEVENLABS_AGENT_ID'],conversation,caller,action,payload,datetime.now().timestamp()+300,None)); c.commit(); c.close()
        h.send_json(200,{'confirmationToken':token,'summary':summary,'expiresInSeconds':300}); return True
    if u.endswith('/confirm'):
        tok=b.get('confirmationToken'); c=_db(); c.execute('BEGIN IMMEDIATE'); op=c.execute('SELECT * FROM voice_operations WHERE token_hash=?',(hashlib.sha256(str(tok).encode()).hexdigest(),)).fetchone()
        if not op or op['agent']!=os.environ['ELEVENLABS_AGENT_ID'] or op['conversation']!=conversation or op['caller']!=caller or op['expires']<datetime.now().timestamp(): c.rollback(); c.close(); h.error(403,'invalid or expired confirmation'); return True
        if op['consumed']:
            result=json.loads(op['consumed']); c.commit(); c.close(); h.send_json(200,result); return True
        p=json.loads(op['payload']); p['phone']=caller; action=op['action']
        try: result=_apply(c,caller,action,p,op['id'])
        except (ValueError,KeyError) as e: c.rollback(); c.close(); h.error(409,str(e)); return True
        if action=='create':
            from . import notifications
            result['whatsapp']=notifications.enqueue(c,op['id'],result['booking'])
        c.execute('UPDATE voice_operations SET consumed=? WHERE id=?',(json.dumps(result),op['id'])); c.commit(); c.close(); h.send_json(200,result); return True
    h.error(404,'not found'); return True
def _apply(c,caller,action,p,opid):
    if action=='create':
        server.validate_person(p); s=server.parse_start(p['start']); e=server.rules(p['serviceId'],p['professionalId'],s)
        if server.overlap(c,p['professionalId'],s,e): raise ValueError('time slot unavailable')
        bid=secrets.token_hex(16); c.execute("INSERT INTO bookings (id,service_id,professional_id,start,end,customer_name,phone,status,management_token_hash,management_token,idempotency_key,idempotency_payload,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(bid,p['serviceId'],p['professionalId'],server.iso(s),server.iso(e),p['customerName'].strip(),caller,'confirmed','', '',opid,None,datetime.now().isoformat())); r=c.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone(); return {'booking':server.booking_json(r),'action':action}
    bid=p.get('bookingId'); r=c.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()
    if r and _norm_phone(r['phone'])!=caller: r=None
    if not r: raise ValueError('booking not found')
    if r['status']!='confirmed': raise ValueError('booking is cancelled')
    if action=='cancel': c.execute("UPDATE bookings SET status='cancelled' WHERE id=?",(bid,)); return {'booking':dict(server.booking_json(r),status='cancelled'),'action':action}
    s=server.parse_start(p['start']); pid=p.get('professionalId',r['professional_id']); e=server.rules(r['service_id'],pid,s)
    if server.overlap(c,pid,s,e,bid): raise ValueError('time slot unavailable')
    c.execute('UPDATE bookings SET professional_id=?,start=?,end=? WHERE id=?',(pid,server.iso(s),server.iso(e),bid)); n=c.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone(); return {'booking':server.booking_json(n),'action':action}
