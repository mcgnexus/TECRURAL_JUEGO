# 0004 — Claves externas (Fase 1)

Fecha: 2026-11-08. Estado: verificado parcial.

- `AEMET_API_KEY` (JWT OpenData) solo en `.env` servidor gitignored. Adapter `services/ingestion/aemet.py` con flujo metadatos→datos, errores redactados (nunca URL con clave en logs). Chequeo: predicción diaria Motril 18140 OK (1 registro). Primer intento dio 401 transitorio; reintento OK. Pendiente: fijar productos/cobertura/límites por producto en SOURCES.md.
- Open-Meteo sin clave para uso complementario estándar: verificado (`daily` 2 días). Uso comercial requiere contrato/licencia por verificar. Siempre etiquetar modelizado ≠ observación.
- `DEEPSEEK_API_KEY` solo servidor (`services/api/assistant.py`), solo redacción de eventos de juego, nunca valores científicos/dosis, nunca datos identificativos sin base jurídica. Verificado: explicación 352 caracteres.
- Incidencia: un log inicial mostró prefijo de la URL con clave; corregido redactando excepciones en adapter y script.
