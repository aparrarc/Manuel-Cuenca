# WhatsApp Meta + n8n — activación pendiente

Confirmado 2026-09-13:
- Emisor comunicado por Antonio: Weedex +34 683 498 975.
- n8n: https://n8n.parritabrava.com, host 187.127.233.41, contenedor n8n_kvm4_production.
- Credencial existente: Weedex WhatsApp Oficial (TT3XRZGlxpZZwMp3).
- Phone ID 1149142188289476; WABA 1433438295214319.
- GET autenticado Meta desde n8n confirmó plantilla APPROVED confirmacion_reserva_pagina_weedex, español, cinco parámetros: nombre, centro, fecha, hora, servicio.
- Flujo independiente importado INACTIVO: mcWhatsappConfirm20260913. Fuente integrations/n8n/whatsapp-confirmation.json.
- Credencial de entrada propia mcWhatsappIngress20260913 importada sin exponer valor. Archivo protegido /opt/manuelcuenca-web/secrets/notification_token en KVM2. Meta token permanece en n8n.

Estado: código y prompt de esta fase NO desplegados/publicados. Producción conserva voice-v2-20260913. No se han enviado WhatsApps.

Pendiente:
1. Abrir sesión en panel n8n. Publicar flujo por UI/API autenticada. El CLI instalado avisa que publicar por CLI exige reinicio del proceso; no reiniciar n8n compartido.
2. Probar webhook sin credencial (401) y payload inválido sin envío.
3. Desplegar nuevo backend en KVM2 con NOTIFICATION_WEBHOOK_URL=https://n8n.parritabrava.com/webhook/manuelcuenca-whatsapp-confirmation-v1 y NOTIFICATION_TOKEN_FILE=/run/secrets/notification_token. Preservar montajes y demás variables.
4. Publicar herramienta preparar con whatsappPhone y whatsappConsent, y prompt actualizado. Catálogo informa callerPhoneAvailable/whatsappEnabled. Teléfono manual no cambia ownership de citas.
5. Hacer una reserva nueva con número controlado confirmado por usuario, verificar aceptación Meta y recepción real. No enviar retrospectivamente citas previas.

Outbox: una entrada por operación confirmada; reintentos de confirmación no duplican mensajes. HTTP 2xx con accepted/messageId significa aceptación Meta, NO entrega al móvil. Timeout/unverified es unknown, sin reintento automático. Worker solo consume cuando hay URL y credencial configuradas. No hay notificaciones de modificación/cancelación todavía. Revisar vigencia de eventos pendientes antes de habilitar.

Prueba de preflight Meta mcMetaRead20260913 quedó inactiva; solo GET a plantillas, sin envíos.
