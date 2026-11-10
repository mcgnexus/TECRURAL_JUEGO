# Métodos nutrición y sanidad — juego v0.3 (Fase 5, revisor: pendiente)

Grado: todo `juego`. Profesional bloqueado.

## 1. Nutrición

Registro análisis suelo/hoja sin diagnóstico. Balance N juego:
`cum_N += kg×n_frac − cosecha_kg×0.002`. Supuesto explícito, incertidumbre total.
Sin análisis no hay dosis válida.

## 2. Sanidad

- RAIF: aviso regional con zona/antigüedad; nunca diagnóstico parcela.
- Inspección juego: prob. 0.15 sin calibrar → `observacion_plaga`.
- Tratamientos: `POST /treatments` siempre bloquea. Exige registro MAPA vigente,
  uso autorizado por cultivo y revisión por técnico competente.
- Ensayos con datos históricos separados: plantilla CSV
  `fecha,parcela,plaga_obs,tratamiento,resultado` (pendiente técnico).

## 3. Textos revisables

Cualquier texto agronómico requiere revisión agronómica + control de versiones.
Cambios de versión documentados en decisiones 0010/0011.
