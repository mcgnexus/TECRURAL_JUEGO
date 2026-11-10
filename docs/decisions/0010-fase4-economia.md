# 0010 — Cultivos, producción y economía (Fases 4)

Fecha: 2026-11-10. Estado: juego/experimental, profesional desactivado.

- Fenología juego por especie (tabla mes-día en motor): aguacate/mango/chirimoyo con
  etapas reposo/floración/cuajado/cosecha. Sin valor agronómico real; bienalidad u
  otros efectos NO modelados (no documentados).
- Producción por intervalos: `forecast_interval` low/mid/high = 0.7/1.0/1.3 ×
  pendiente×0.5×salud×factor_edad (joven<5:0.5, adulto:1.0, viejo>25:0.7).
  Coherencia: tope `árboles×120 kg` recorta pendiente con evento.
- Cosecha → inventario por lotes (`fecha-parcela-semilla`), merma juego 5%,
  venta por canales base/cooperativa(0.95)/mercado(1.1) como escenarios.
  Sin stock no hay venta (venta_parcial). Auto-venta por defecto preserva F1-3.
- Economía juego: costes agua+energía+fijo/ha(0.0)+fertilizante+20 € labor,
  deuda opcional con interés 0.0002/día, conciliación caja tolerancia 0.05.
  Precios históricos en `data/fixtures/precios_historicos.csv` (fecha/canal/nivel).
- Previsión profesional DESACTIVADA: endpoint `/forecast` solo intervalos juego;
  umbral de activación pendiente (campañas/fincas no usadas para calibrar + técnico).
