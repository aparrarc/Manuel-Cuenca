# Manuel Cuenca Fisioterapia — demo Weedex

Web nueva e independiente para Manuel Cuenca. Se reutiliza la estructura React/Vite del trabajo previo de Forja, sin datos, APIs, credenciales, despliegues ni historial Git de P de Paula.

## Desarrollo

```sh
npm ci
npm run dev -- --host 127.0.0.1
npm run build
```

## Alcance

Landing personalizada y recorrido de reserva simulado. No crea citas reales ni envía notificaciones. Cinco áreas propuestas: fisioterapia/rehabilitación, osteopatía, nutrición, psicología y entrenamiento (pendiente de confirmar).

La agenda transaccional y el asistente telefónico se construirán después. Se reutilizará el patrón de consulta, alta, modificación y cancelación de citas, nunca las conexiones de otro cliente. Archivex permanece como sistema clínico principal; no hay integración confirmada.

Imágenes y logo proceden de la web pública del cliente. Esta demo no debe indexarse como web oficial.

## Contenedor

Construir `dist` localmente; el contenedor sirve exclusivamente estáticos en el puerto interno 8080. Sin bases de datos, credenciales ni volúmenes de otros clientes.

```sh
docker build -t manuel-cuenca-web:demo .
```

## Estado de entrega — 13/09/2026

- Fuente independiente en `/home/casa/projects/manuel-cuenca-web`; sin historial del proyecto base.
- Validación: lint, 3 tests y build correctos.
- KVM4: servicio Swarm `manuelcuenca-web`, imagen `manuelcuenca-web:demo-20260913`, release `/opt/manuelcuenca-web/releases/demo-20260913`.
- Una réplica, límites 0,5 CPU y 256 MiB, sin puertos publicados y Traefik desactivado para este servicio.
- Verificados HTTP 200 en `/booking` y JS, healthz `ok`, cabecera noindex.
- Acceso público activo: https://manuelcuenca.weedex.es/ . DNS creado por el usuario hacia KVM4. Ruta aislada en `/etc/dokploy/traefik/dynamic/manuelcuenca-web.yml`, sin modificar rutas existentes. HTTPS válido y HTTP → HTTPS 308; portada y `/booking` devuelven 200 (13/09/2026).
- GitHub: usuario confirma repositorio creado (Manuel-Cuenca); pendiente URL exacta y autenticación del agente para subir el código.
- Navegador abre la portada pública con título correcto; captura bloqueada por timeout del navegador. Revisión visual/interactiva completa todavía pendiente.
