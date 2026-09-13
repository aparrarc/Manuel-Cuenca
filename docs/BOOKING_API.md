# Agenda propia — demo Manuel Cuenca

Todos los endpoints son independientes de P de Paula y Archivex. Las fechas ISO incluyen zona horaria y se interpretan en Europe/Madrid. El catálogo y los horarios son configuración de demo: lunes a viernes 08–14 y 16–20, horizonte 90 días, intervalos de inicio de 15 minutos.

## Web y recepción

- GET `/api/catalog`: seis profesionales, departamentos y servicios compatibles.
- GET `/api/availability?serviceId=physio&professionalId=p1&date=YYYY-MM-DD`: huecos sin solapamiento.
- POST `/api/bookings`: `serviceId`, `professionalId`, `start`, `customerName`, `phone`, `idempotencyKey`.
- GET `/api/bookings/:id`: consultar cita propia.
- PATCH `/api/bookings/:id`: `start`, `professionalId`, `idempotencyKey`.
- DELETE `/api/bookings/:id`: cancelar y liberar disponibilidad.

La creación devuelve una capacidad privada de gestión, conservada exclusivamente en sessionStorage. No ponerla en URLs ni registros. GET/PATCH/DELETE requieren `X-Management-Token` o sesión administrativa. La clave de idempotencia debe mantenerse en los reintentos de una misma operación; un cambio de contenido exige otra clave. Un conflicto responde 409; el frontend debe consultar de nuevo la disponibilidad.

- POST `/api/admin/login`: contraseña por HTTPS, sesión HttpOnly/Secure/SameSite=Strict.
- POST `/api/admin/logout`: revoca sesión.
- GET `/api/admin/session`: estado de sesión.
- GET `/api/admin/bookings?date=YYYY-MM-DD`: agenda autenticada, filtro opcional `professionalId`.

## Preparación de ElevenLabs (sin conectar todavía)

POST `/api/tools/availability`, `/api/tools/book`, `/api/tools/reschedule`, `/api/tools/cancel`.

Deshabilitados sin `WEBHOOK_TOKEN_FILE`. Las mutaciones requieren identidad del llamante en `X-ElevenLabs-Caller-Id` y autenticación bearer; la identidad debe proceder de la plataforma telefónica, nunca de un argumento inventado por el modelo. El alta toma el teléfono de esa cabecera. Cambio/cancelación requieren `bookingId` y pertenencia al llamante. No se ha creado ni conectado un agente ElevenLabs.

Antes de la conexión: registrar herramientas con esquemas concretos, verificación del llamante, confirmación explícita antes de escribir, búsqueda segura de citas propias, gestión de errores y transferencias. Validar estos flujos con llamadas de prueba; no asumir compatibilidad directa con las herramientas actuales de P de Paula.

## Operación en KVM4

Base SQLite persistente en volumen dedicado. No subir base ni secretos al repositorio. Una sola réplica del servicio; las transacciones serializan escrituras y evitan solapamientos dentro de cada profesional.

El operador puede provisionar la contraseña desde un terminal interactivo de KVM4:

```sh
python3 /opt/manuelcuenca-web/provision_admin.py
```

El programa solicita la contraseña con entrada oculta, no como argumento ni en chat. La ruta `/opt/manuelcuenca-web/secrets` se monta solo lectura dentro del contenedor. El panel permanece cerrado si no existe contraseña.

Para volver al frontend anterior, restaurar la imagen previa mediante actualización de servicio; no eliminar el volumen. Antes de producción deberán incorporarse política de retención, copias automáticas probadas y controles operativos apropiados para datos reales.
