# Gemelo piloto — reglas (Fase 9, simulado; real solo autorizado)

- Autorización por parcela: `owner_id` + `permiso_ref`; sin ambas no hay importación.
- Adaptadores: cada sensor declara id, magnitud, unidad, frecuencia, calibración y
  fecha; fallos y calidad se registran, no se ocultan.
- Capas: `observada` (solo lectura) / `inferida` (modelo+versión) / `escenarios`
  (hipótesis etiquetadas). Sincronizar añade versión, jamás sobrescribe original.
- Robustez: duplicados (misma id+fecha se conservan una vez), retrasados (se marcan),
  erróneos (fuera de rango físico se aíslan). Conectividad: cola + reintento.
- Deriva: |pred−med| acumulado por finca; alarma si supera umbral pendiente de
  definir con técnico; revisión humana obligatoria; kill-switch por recomendación.
