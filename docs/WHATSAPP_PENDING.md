# WhatsApp Meta + n8n — activado; prueba de entrega pendiente

Confirmado 2026-09-13:
- Emisor comunicado por Antonio: Weedex +34 683 498 975.
- n8n: https://n8n.parritabrava.com, host 187.127.233.41, contenedor n8n_kvm4_production.
- Credencial existente: Weedex WhatsApp Oficial (TT3XRZGlxpZZwMp3).
- Phone ID 1149142188289476; WABA 1433438295214319.
- GET autenticado Meta desde n8n confirmó plantilla APPROVED confirmacion_reserva_pagina_weedex, español, cinco parámetros: nombre, centro, fecha, hora, servicio.
- Flujo independiente publicado por UI: mcWhatsappConfirm20260913. Fuente integrations/n8n/whatsapp-confirmation.json.
- Credencial de entrada propia mcWhatsappIngress20260913 importada sin exponer valor. Archivo protegido /opt/manuelcuenca-web/secrets/notification_token en KVM2. Meta token permanece en n8n.

Estado 19h: flujo n8n publicado por UI sin reinicio. Backend desplegado como manuelcuenca-web:whatsapp-v1-20260913 con variables NOTIFICATION_*; herramienta y prompt publicados en ElevenLabs. Catálogo devuelve whatsappEnabled=true. Outbox vacía: ninguna cita antigua encolada. No se ha enviado WhatsApp de prueba porque falta un número controlado indicado por Antonio.

Comprobaciones completadas:
- n8n sesión autenticada y publicación por UI.
- Webhook sin credencial devuelve 403; con credencial y payload inválido no devuelve aceptación Meta. n8n puede responder HTTP 200 vacío ante error, por lo que el backend exige accepted y messageId y no interpreta 200 aislado como envío.
- KVM2 servicio saludable, catálogo voz autenticado responde WhatsApp activo y preview sin caller.
- Herramienta preparar guarda móvil WhatsApp con consentimiento sin modificar ownership de citas; prompt publicado.

Pendiente: una reserva nueva con número controlado confirmado por usuario; verificar aceptación Meta y recepción real. No forzar reenvíos con otra cita si hay resultado unknown.

Outbox: una entrada por operación confirmada; reintentos de confirmación no duplican mensajes. HTTP 2xx con accepted/messageId significa aceptación Meta, NO entrega al móvil. Timeout/unverified es unknown, sin reintento automático. Worker solo consume cuando hay URL y credencial configuradas. No hay notificaciones de modificación/cancelación todavía. Revisar vigencia de eventos pendientes antes de habilitar.

Prueba de preflight Meta mcMetaRead20260913 quedó inactiva; solo GET a plantillas, sin envíos.

## Corrección 20h — web y ElevenLabs
Se diagnosticaron las reservas reportadas por usuario: web sin outbox por ausencia de integración en create público, y voz con whatsapp.status=skipped por falta de móvil de preview. No eran rechazos Meta.

Cambios whatsapp-v2-20260913:
- Alta web encola en la misma transacción solo con casilla WhatsApp aceptada, normaliza móvil español y deduplica reintentos. UI muestra solicitud, no entrega.
- Preview voz con WhatsApp activo exige móvil+aceptación o rechazo explícito whatsappConsent=false; prepare y confirm bloquean omisión silenciosa. Ownership sigue siendo la conversación.
- Prompt prioritario y herramienta actualizados/publicados.
- 26 tests backend, lint y build correctos. Prueba real navegador contra servidor local aislado guardó reserva y exactamente un evento pending, sin envío externo.
- No se reenviaron las dos reservas previas. Prueba externa de dos mensajes solicitada a Antonio; no realizar sin su respuesta.
