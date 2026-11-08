# 0007 — Clima real y trazabilidad (Fase 2)

Fecha: 2026-11-09. Estado: verificado con dobles; AEMET en vivo intermitente.

- Contrato común `provider.py` (SeriesPoint/SeriesResult, tz Europe/Madrid) para AEMET, SiAR y Open-Meteo.
- Estación por defecto `motril-18140` (municipio INE 18140, 36.75/-3.87, alt. ~30 m aprox.); selección manual por id; distancia/altitud visibles; estación ≠ microclima.
- Caché archivo con TTL (pronóstico 1 h, observación 6 h), 3 reintentos con retroceso; fallo con caché expirada → obsoleta marcada; sin caché → `FuenteNoDisponible` (503), nunca inventar.
- Validación: unidades mm, fechas ISO, duplicados (conserva último), huecos listados, imposibles descartados con conteo.
- Escenarios: `presente_con_prevision` (AEMET + reserva Open-Meteo, sustitución ET0 etiquetada con fecha) e `historico_cerrado` reproducible (CSV grabado, kind honesto `estimacion`).
- Instantáneas por partida/día en `data/snapshots/` (gitignored): la campaña se reproduce aunque la fuente cambie.
- Incidencia: AEMET intermitente con la clave actual (401 / 500 en URL de datos / respuestas vacías en días distintos) → serie vacía también dispara la reserva Open-Meteo etiquetada. Pendiente verificar activación/producto en portal AEMET. SiAR: alta pendiente, adaptador conforme que declara no-disponibilidad.
