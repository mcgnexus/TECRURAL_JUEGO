# 0006 — Clasificación de resultados (Fase 0)

Fecha: 2026-11-08. Estado: norma vigente.

Todo valor mostrado lleva etiqueta obligatoria:
- `observacion`: medida de estación/red oficial (con estación, distancia, fecha emisión).
- `pronostico`: predicción oficial o modelizada (con fecha emisión y horizonte; nunca se presenta como hecho).
- `estimacion`: cálculo con incertidumbre (humedad de suelo estimada ≠ medida; ET parcela estimada ≠ ET0 estación).
- `simulado`: salida del juego/escenario ficticio (explícito "juego", modo profesional desactivado).

Proveniencia mínima: fecha cálculo y de datos, zona, unidades, procedencia, versión modelo/parámetros, supuestos, incertidumbre, limitaciones. Al agotarse datos se pide otro escenario; nunca se convierte pronóstico en observación ni futuro inventado en real.
