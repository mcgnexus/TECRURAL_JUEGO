# 0002 — Reglas científicas y de juego (Fase 0)

Fecha: 2026-11-08.

- Separación estricta: motor agronómico / reglas juego / presentación / conectores / cuentas.
- IA generativa nunca fuente de valores científicos ni dosis.
- Modos: juego y experimental activos y etiquetados; profesional desactivado por defecto por cultivo, función y zona.
- Sin umbrales ni Kc numéricos sin evidencia. Parámetros de `packages/content` llevan `evidence_level: juego|experimental` y nunca se presentan como práctica real.
- Fitosanitario: jamás receta real por alerta regional o síntomas. Sin autorización vigente + etiqueta + técnico, solo información general + derivar a profesional.
- Motor `step` determinista, rechaza unidades incompatibles, acciones imposibles y datos faltantes sin política explícita. Semana = 7 pasos diarios idénticos.
- Dificultad y realismo independientes. Dificultad: capital/objetivos/asistencia/tolerancia. Realismo: detalle y mecanismos documentados, nunca procedencia ni precisión declarada.
- Retención sin engaño: sin rachas coercitivas, compras encubiertas ni castigo por inactividad.
