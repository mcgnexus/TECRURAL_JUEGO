# 0011 — Nutrición y sanidad vegetal (Fase 5)

Fecha: 2026-11-10. Estado: juego/experimental, profesional bloqueado.

- Análisis suelo/hoja: registro (`POST /games/{id}/analyses`) sin diagnóstico.
  Balance N juego (entradas fertilizante − exportación 0.002 kg/kg fruta) etiquetado
  explícitamente NO foliar.
- Fertilizantes juego (`fertilizantes.json`): NPK15/NK con coste; sin análisis no hay
  dosis válida. Supuestos e incertidumbre documentados.
- RAIF (`services/ingestion/raif.py`): sin API inferida; `aviso()` devuelve zona,
  antigüedad semanal e `aviso regional ≠ diagnóstico`. `observacion()` lanza
  FuenteNoDisponible. No se infiere tratamiento desde alerta.
- Plagas juego: inspección (scout) genera observación con prob. 0.15 sin calibrar
  (`observacion_plaga`); requiere campo + técnico.
- Fitosanitarios (`fitosanitarios.json`): 2 productos juego CADUCADO/PENDIENTE.
  `POST /treatments` bloquea siempre: 422 si ficha obsoleta/uso sin confirmar,
  403 profesional desactivado en otro caso. Exige MAPA vigente + técnico.
