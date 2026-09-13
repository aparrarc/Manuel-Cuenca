#!/usr/bin/env python3
"""Run interactively on KVM4. Password entry is masked, never logged."""
import getpass
import os
import tempfile
from pathlib import Path

root = Path('/opt/manuelcuenca-web/secrets')
if not os.isatty(0):
    raise SystemExit('Run in an interactive terminal; password input must be masked.')
password = getpass.getpass('Nueva contraseña del panel (mínimo 14 caracteres): ')
if len(password) < 14:
    raise SystemExit('Contraseña demasiado corta; no se cambió nada.')
if password != getpass.getpass('Repetir contraseña: '):
    raise SystemExit('No coinciden; no se cambió nada.')
root.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chown(root, 10001, 10001)
os.chmod(root, 0o700)
fd, temporary = tempfile.mkstemp(dir=root, prefix='.admin-')
try:
    os.fchmod(fd, 0o400)
    os.fchown(fd, 10001, 10001)
    with os.fdopen(fd, 'w') as stream:
        stream.write(password)
    os.replace(temporary, root / 'admin_password')
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
print('Contraseña instalada. Accede al panel /admin por HTTPS.')
