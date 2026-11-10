# 0015 — Evolución hacia gemelo digital de finca real (Fase 9, diseño + piloto simulado)

Fecha: 2026-11-10. Estado: diseño y piloto con sensores simulados; real solo tras validación+acuerdos.

- Solo tras Fase 7 y acuerdos: importar límites y datos del propietario con
  autorización verificable por parcela (`packages/twin/`).
- Sensores por adaptador explícito (identidad, calibración, frecuencia, fallos,
  calidad); simulados hoy, reales solo autorizados. Datos duplicados/retrasados/
  erróneos se aíslan, no se mezclan; recuperación de conectividad por reintento
  con historial, sin sobrescribir originales.
- Separación estricta: copia observada / estado inferido / escenarios hipotéticos;
  sincronización con historial de cambios. Juego separado de flujos reales.
- Deriva: comparación continua predicción/medición por finca, alarma + revisión
  humana; cada recomendación desactivable individualmente. Extensión de alcance
  solo con seguimiento prospectivo y aprobación expresa.
