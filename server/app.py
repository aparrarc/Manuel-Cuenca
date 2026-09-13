"""Container/module entrypoint."""
import threading
from .server import main, conn
from . import notifications

def dispatch_loop():
    while True:
        try:
            c=conn()
            try: notifications.process_pending(c,limit=5)
            finally: c.close()
        except Exception:
            # No payloads or credentials in logs; booking service stays independent.
            pass
        threading.Event().wait(3)

if __name__ == "__main__":
    threading.Thread(target=dispatch_loop,daemon=True).start()
    main()
