# Métodos de agua y riego — juego v0.2 (Fase 3, 2026-11-10, revisor: pendiente)

Grado: todo `juego`. Nada validado para explotación real. Profesional desactivado.

## 1. Ecuaciones (unidades explícitas)

- Conversión: `m3 = mm × area_ha × 10` ; `mm = m3 / (area_ha × 10)`.
- Lluvia efectiva: `lluvia_ef = precip_mm × (1 − runoff_coef)` (defecto 0.15).
- Infiltrado: `infiltrado_mm = aplicada_mm × eficiencia_red × eficiencia_aplicación`
  (defectos 0.92 × 0.85). Pérdida red por parcela: `bombeo − bombeo×eficiencia_red`.
- Necesidad: `ETc = ET0 × kc_juego` (aguacate 0.8, mango 0.75, chirimoyo 0.7).
- Estrés juego: `estrés = clamp(ratio_suelo×1.5, 0.3, 1)` ; `ET_real = min(ETc×estrés, suelo+lluvia_ef+infiltrado)`.
- Suelo: `S' = S + lluvia_ef + infiltrado − ET_real − drenaje`, `drenaje = max(0, S−Smax)`,
  `Smax = 80 mm` (juego), escorrentía = `precip × runoff_coef`.
- Depósito: `R_disp = min(Rmax, R + aporte)` ; `desborde = max(0, R+aporte−Rmax)` ;
  `R' = R_disp − bombeo_total`. Aporte defecto 8 m3/día (juego).
- Energía: `kWh = bombeo × 0.4` ; coste = `bombeo×0.25 + kWh×0.25` (+20 € labor abstracta si poda/vigilancia/abono).

## 2. Parámetros por cultivo (juego, sin calibrar)

| Variable | Aguacate | Mango | Chirimoyo | Grado |
|---|---|---|---|---|
| kc juego | 0.8 | 0.75 | 0.7 | juego |
| Smax zona radicular | 80 mm | 80 mm | 80 mm | juego |
| eficiencia aplicación | 0.85 | 0.85 | 0.85 | juego |
| ETc real / necesidades | — | — | — | desconocido (ET0 estación ≠ ET parcela) |
| Umbrales estrés reales | — | — | — | desconocido |
| Dosis / frecuencia reales | — | — | — | desconocido |

## 3. Cálculo de referencia independiente

`scripts/check_fase3_reference.py` replica las ecuaciones sin importar el motor
(duplicación intencional) y compara 5 casos: día base, lluvia cero, exceso lluvia,
tope bombeo, cambio superficie. Criterio: diferencias ≤ tolerancia fijada.
Ejecutar: `python scripts/check_fase3_reference.py`.

## 4. Comparación observada y caso técnico (pendiente)

- Plantilla pendiente: técnico aporta serie observada (fecha, precip_mm, ET0_SiAR,
  riego_m3 aplicado, humedad medida si existe) → se reproduce con
  `historico_cerrado` + instantáneas por día. Comparación solo con datos
  disponibles hasta cada fecha (sin fuga temporal: prohibido usar futuro).
- Estado: sin técnico colaborador aún; todo escenario permanece en juego experimental.
- Formato esperado (CSV): `fecha,precip_mm,et0_mm,riego_m3,soil_medida_mm?`.

## 5. Límites y no-afirmaciones

- Ninguna dotación, pozo, red o turno afirma derecho real de agua.
- Estación ≠ microclima parcela; ET0 estación ≠ ET parcela.
- Aviso regional fitosanitario ≠ diagnóstico.
