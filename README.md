# Manuel Cuenca — demo de reservas Weedex

Web y sistema de reservas independientes. Sin conexión a P de Paula ni Archivex.

## Alcance

Seis calendarios: Manuel Cuenca, Fernando López, Álvaro Hurtado, Víctor González, Alex Velasco y José David López (entrenador). Horarios, duraciones y asignaciones de la demo no constituyen disponibilidad oficial del centro. Nutrición y Psicología no admiten reservas sin profesionales asignados.

Las citas se persisten en SQLite y se comparten entre reserva web y recepción. Utilizar solo identidades y teléfonos ficticios. No se envían mensajes ni se confirma atención clínica real. El asistente ElevenLabs se conectará en otra fase.

## Desarrollo

```sh
npm ci
npm run build
python -m server.app
```

Frontend servido por el backend en puerto 8080. `DATABASE_PATH` selecciona el archivo SQLite; `STATIC_DIR` la carpeta de compilación. Los secretos no se guardan en Git: `ADMIN_PASSWORD_FILE` y `WEBHOOK_TOKEN_FILE` son rutas a archivos protegidos. Si faltan, los accesos correspondientes quedan cerrados.

## Validación

```sh
npm run lint
npm test
npm run build
python -m unittest -v server.test_server
```

## Despliegue

KVM2, servicio dedicado `manuelcuenca-web`, una réplica, 0,5 CPU, 256 MiB, puerto interno 8080 en `dokploy-network`. Volumen persistente para la base de datos, sin compartir información con otros clientes. Mantener una sola réplica para esta implementación SQLite.

Ruta Traefik aislada: `/etc/dokploy/traefik/dynamic/manuelcuenca-web.yml`. No sustituir configuraciones compartidas. HTTPS y noindex activos en https://manuelcuenca.weedex.es/ . Panel: `/admin`.

Repositorio: https://github.com/aparrarc/Manuel-Cuenca — rama `main`, clave SSH de despliegue exclusiva.

## Pendiente de producción

Validar horarios, servicios y profesionales con el cliente; integrar identidad del llamante y confirmación verbal en ElevenLabs; definir notificaciones y copias de seguridad con restauración; completar autenticación operativa y revisión de datos antes de utilizar pacientes reales. Esta entrega no sustituye historia clínica, facturación ni consentimientos clínicos.

## Evidencia de verificación (13/09/2026)

- 11 pruebas HTTP/SQLite: seis agendas, compatibilidad, concurrencia, solapamientos, reintentos, cambio/cancelación, liberación, autorización, horarios y respuestas inválidas.
- 2 pruebas de visualización horaria Madrid y cambio de hora.
- Lint y compilación del frontend correctos.
- Navegador local: alta desde web, cambio a otro profesional, recuperación tras recarga, seis columnas de recepción, cancelación administrativa y lectura de la cancelación en la web. Móvil 390 px sin desbordamiento; sin errores JS.
- Contraseña del panel pendiente de provisionar por el operador desde terminal interactivo KVM2; ver `docs/BOOKING_API.md`. Los secretos no se entregan por chat.

### Despliegue verificado

Imagen `manuelcuenca-web:bookings-v2-20260913`, volumen `manuelcuenca-bookings`, secretos montados solo lectura desde `/opt/manuelcuenca-web/secrets`. Contenedor saludable; aproximadamente 2,6 GiB de RAM disponible tras desplegar.

Comprobado sobre HTTPS público: catálogo de seis profesionales, alta de prueba, persistencia de cita y capacidad de gestión tras reinicio, cancelación posterior y renderizado móvil/login sin errores JavaScript. La cita de prueba quedó cancelada. El panel administrativo se probó autenticado localmente; el acceso público permanece cerrado hasta provisionar contraseña. ElevenLabs continúa sin conectar.
