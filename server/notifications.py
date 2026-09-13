"""Transactional notification outbox; transport is intentionally provider-neutral."""
import json, os, re, sqlite3, urllib.request, urllib.error
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from pathlib import Path

def init(c):
    c.execute("""CREATE TABLE IF NOT EXISTS notification_outbox(
      event_key TEXT PRIMARY KEY,event_id TEXT NOT NULL,kind TEXT NOT NULL,
      recipient_phone TEXT NOT NULL,booking_id TEXT NOT NULL,payload TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending',attempted_at TEXT,finished_at TEXT,
      error TEXT)""")

def _phone(v):
    if not isinstance(v,str) or v.startswith('demo:'): return None
    v=v.strip()
    if not re.fullmatch(r'\+?[1-9][0-9]{7,14}',v): return None
    return '+'+v.lstrip('+')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl): return None


def enqueue(c,event_key,booking):
    """Insert one confirmation event in caller's current transaction."""
    init(c); recipient=_phone(booking.get('phone',''))
    if not recipient: return {'status':'skipped','reason':'demo_or_invalid_recipient'}
    try:
        when=datetime.fromisoformat(booking['start']).astimezone(ZoneInfo('Europe/Madrid')).strftime('%d/%m/%Y a las %H:%M')
    except (KeyError,ValueError,TypeError): return {'status':'skipped','reason':'invalid_date'}
    text=f"Weedex · Demo Manuel Cuenca\nTu cita de prueba está confirmada para el {when} (hora de Madrid). Este mensaje forma parte de una demostración; no es una cita clínica real."
    payload=json.dumps({'eventId':event_key,'type':'booking_confirmation','recipientPhone':recipient,'bookingId':booking.get('id'),'text':text},ensure_ascii=False)
    try: c.execute("INSERT INTO notification_outbox(event_key,event_id,kind,recipient_phone,booking_id,payload) VALUES(?,?,?,?,?,?)",(event_key,event_key,'booking_confirmation',recipient,booking.get('id',''),payload)); return {'status':'queued','eventId':event_key}
    except sqlite3.IntegrityError: return {'status':'already_queued','eventId':event_key}

def process_pending(c,limit=20):
    url=os.environ.get('NOTIFICATION_WEBHOOK_URL',''); token_file=os.environ.get('NOTIFICATION_TOKEN_FILE','')
    if not url or not url.lower().startswith('https://') or not token_file: return {'status':'disabled','processed':0}
    try: token=Path(token_file).read_text().strip()
    except OSError: return {'status':'disabled','processed':0}
    if not token: return {'status':'disabled','processed':0}
    init(c); done=0
    for _ in range(limit):
        c.execute('BEGIN IMMEDIATE'); row=c.execute("SELECT * FROM notification_outbox WHERE status='pending' ORDER BY rowid LIMIT 1").fetchone()
        if not row: c.rollback(); break
        c.execute("UPDATE notification_outbox SET status='sending',attempted_at=? WHERE event_key=? AND status='pending'",(datetime.now(timezone.utc).isoformat(),row['event_key'])); c.commit()
        try:
            req=urllib.request.Request(url,data=row['payload'].encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+token},method='POST')
            with urllib.request.build_opener(NoRedirect).open(req,timeout=8) as response: code=response.status
            c.execute("UPDATE notification_outbox SET status=?,finished_at=? WHERE event_key=?",('accepted' if 200<=code<300 else 'failed',datetime.now(timezone.utc).isoformat(),row['event_key'])); c.commit(); done+=1
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError, OSError) as e:
            # Network ambiguity is never automatically retried; explicit HTTP failure is failed.
            status='failed' if isinstance(e,urllib.error.HTTPError) else 'unknown'
            c.execute("UPDATE notification_outbox SET status=?,finished_at=?,error=? WHERE event_key=?",(status,datetime.now(timezone.utc).isoformat(),type(e).__name__,row['event_key'])); c.commit(); done+=1
    return {'status':'ok','processed':done}
