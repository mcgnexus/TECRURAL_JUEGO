# 0013 — Validación científica y activación profesional (Fase 7, marco general)

Fecha: 2026-11-10. Estado: marco definido, sin datos autorizados, profesional desactivado.

- Protocolo y métricas por cultivo/zona/variable/estación/uso (`packages/validation/`):
  MAE/RMSE/sesgo en magnitudes, cobertura de intervalos, sensibilidad/especificidad
  en clasificación, siempre contra método simple actual (media calibración).
- Umbrales (`content/umbrales.json`): todos pendientes; sin valor no hay aprobación.
  Requieren unidades, n mínimo y aplicabilidad por escrito con expertos y usuarios.
- Separación finca×campaña con prueba reservada, sin fuga temporal ni espacial
  (`splits.py`); subgrupos año seco/húmedo, edad, suelo, variedad con n e incertidumbre.
- Ensayo prospectivo en paralelo con técnicos: predicción fechada antes del resultado,
  desacuerdos/riesgos/supervisión y negativos documentados (plantilla `data/validation/`).
- Registro (`content/aprobaciones.json`, vacío): exige función/cultivo/ámbito, versión
  exacta código+parámetros, firmas agronómica y producto, caducidad, cambios,
  seguimiento y retirada. Hasta entonces profesional desactivado sin bloquear el juego.
- Informe reproducible desde datos autorizados y versiones congeladas; revisión por
  quien no calibró; deriva/incidentes/revocación si cambian datos, fuentes o modelo.
  Sin finca concreta vinculada y evaluada no existe gemelo digital validado.
