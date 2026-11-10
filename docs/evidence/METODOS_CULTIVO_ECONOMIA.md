# Métodos cultivo y economía — juego v0.3 (Fases 4, revisor: pendiente)

Grado: todo `juego`. Profesional desactivado. Datos orientativos, no recomendación real.

## 1. Fenología juego (sin valor real)

Tabla mes-día en motor (`PHENO_GAME`). Bienalidad NO modelada (no documentada).

## 2. Producción por intervalos

`mid = pendiente×0.5×salud×factor_edad`; low=0.7×mid, high=1.3×mid.
Factor edad: <5 años 0.5, 5-25 1.0, >25 0.7 (juego). Merma juego 5%.
Tope coherencia: `densidad×superficie×120 kg/árbol`.

## 3. Economía juego

Canales: base 1.0, cooperativa 0.95, mercado 1.1 (escenarios, no cotizaciones).
Históricos: `data/fixtures/precios_historicos.csv` con fecha/canal/nivel.
Deuda opcional con interés 0.0002/día (escenario, no contrato).
Conciliación caja por paso: `|caja_prev−costes+ingresos−caja| ≤ 0.05`.

## 4. Validación pendiente

Estacionalidad por técnico, evaluación en campañas/fincas no usadas para calibrar,
umbral de activación profesional sin definir → profesional desactivado.
