# Matriz evidencias · permisos · riesgos · decisiones (Fase 0, 2026-11-08)

## Evidencias
- Motor juego verificado: balance agua, determinismo, semana=7×día, rechazo unidades (pytest 4 passed).
- Persistencia Neon verificada (tablas accounts/games, roundtrip API).
- AEMET/Open-Meteo/DeepSeek verificados sin exponer claves (ver 0004).
- SiAR/RIA y RAIF: webs oficiales localizadas, sin clave ni cobertura subtropical confirmada → pendientes.
- Parámetros: todo valor numérico es `juego` o `desconocido` (fichas_parametros.md, varieties.json). Ningún `validado`.

## Permisos
- Fincas/técnicos: bloqueado hasta acuerdo firmado (plantilla lista en data/fincas/).
- Datos personales: mínimos, .env gitignored, DeepSeek solo resúmenes anonimizados de juego.
- Marketing/SMS/pagos: no activos, requieren revisión y autorización de lanzamiento.

## Riesgos
- Presentar juego como recomendación real → mitigado con etiquetas, provenance y profesional desactivado.
- ET0 estación / aviso regional tomados como parcela → mitigado con clasificación 0006.
- Clave en logs (incidencia 0004, prefijo URL) → corregido con redacción; rotar si se compartió.
- Cierre visual prematuro en PixiJS → mitigado: Canvas 2D inicial, objetivos POCO, prueba real pendiente.

## Decisiones
0001 arquitectura · 0002 reglas · 0003 neon · 0004 claves · 0005 visual/POCO M7 Pro · 0006 clasificación.
Falta de datos no es aprobación científica: lo no evidenciado queda en `desconocido` y el juego lo etiqueta.
