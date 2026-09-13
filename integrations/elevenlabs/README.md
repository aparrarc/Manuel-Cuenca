# Manuel Cuenca — ElevenLabs

Agente: `agent_1401m2d1c9zyexj80g977sa27twk`. Español, Europe/Madrid; se conservan Raquel y Claude Haiku 4.5.

`prompt.md` y `first-message.txt` son los textos del agente. Los cinco JSON usan el formato del editor de herramientas del dashboard (properties como array), no el payload directo de la API ElevenLabs.

Endpoints POST bajo `/api/voice/v1/`: catalog, availability, upcoming, prepare, confirm. El asistente consulta y prepara, lee el resumen, espera confirmación del usuario en otro turno y confirma. Crear/cambiar/cancelar comparten prepare y confirm. Una preparación caduca a los cinco minutos; la confirmación se aplica una sola vez mediante transacción SQLite. La exigencia de un turno afirmativo es una regla conversacional del prompt, no una prueba criptográfica de consentimiento.

Autenticación: secreto dedicado en ElevenLabs, nunca incluido en el repositorio. Headers Authorization, X-ElevenLabs-Agent-Id, X-ElevenLabs-Conversation-Id y X-ElevenLabs-Caller-Id. Las identidades proceden de variables de sistema, no del modelo.

Servidor: **KVM2, 31.97.156.146**, alojamiento temporal autorizado; no KVM4. Servicio manuelcuenca-web, imagen voice-v2-20260913. Variables VOICE_TOKEN_FILE, ELEVENLABS_AGENT_ID, VOICE_PREVIEW_ENABLED; se preserva la contraseña del panel. WEBHOOK_TOKEN_FILE permanece sin configurar para mantener cerrados los endpoints legacy /api/tools.

El preview sin número usa identidad demo aislada por conversación. No recupera citas de otra sesión. En telefonía, el número recibido identifica las citas; esto no es verificación fuerte de identidad de pacientes y no debe usarse como tal para un despliegue clínico. No hay número de teléfono conectado por este trabajo, SMS, WhatsApp ni integración Archivex.

Las pruebas de demostración usan nombres ficticios. El backend comparte la misma SQLite con web y recepción, sin conexiones con P de Paula.
