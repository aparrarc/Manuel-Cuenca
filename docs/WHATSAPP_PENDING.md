# Confirmaciones WhatsApp — preparación pendiente de proveedor

Antonio solicitó enviar desde el número Weedex al teléfono de quien reserva. No hay cuenta WhatsApp conectada a OpenClaw y el proveedor del número no está identificado. Esta preparación NO está desplegada ni envía mensajes.

Se añade un evento de confirmación a SQLite en la misma transacción que la cita vocal. La operación repetida no vuelve a encolarlo. Destinos demo sin teléfono se omiten. Mensaje identificado como Weedex / demostración Manuel Cuenca, sin detalles clínicos. No se usa la cola de P de Paula.

El adaptador HTTPS es solo un contrato pendiente de conectar al proveedor real. NOTIFICATION_WEBHOOK_URL y NOTIFICATION_TOKEN_FILE sin configurar lo mantienen desactivado. No sigue redirecciones con la credencial. HTTP 2xx significa aceptación por el intermediario, no entrega WhatsApp. Timeout es unknown y no se reintenta automáticamente. Hay que revisar manualmente eventos sending/unknown tras reinicios y nunca reenviar ciegamente.

Pendiente para completar:
- Identificar plataforma y cuenta emisora Weedex y acceso seguro.
- Adaptar transporte, plantilla cuando corresponda y confirmación de entrega según proveedor.
- Añadir teléfono de notificación y autorización conversacional para preview sin caller; mantener separado ese teléfono de la identidad de acceso a citas.
- Probar envío a número controlado, desplegar y actualizar el prompt solo tras habilitar envío.
- No enviar retroactivamente eventos pendientes sin revisar vigencia y destinatario.
