# 0009 — Agua, riego e infraestructura (Fase 3)

Fecha: 2026-11-10. Estado: implementado juego/experimental, pendiente revisión técnica.

- Motor `sim-0.2.0`: balance diario por parcela (mm) + depósito/extración/red (m3) con
  libro `water_ledger`. Sin recarga ficticia por lluvia: aporte configurable
  `supply_inflow_m3_day` (defecto 8 m3/día, juego, sin derecho real).
- Diferenciación: depósito (R_max 500 m3) → extracción (bombeo limitado) → red
  (pérdidas 1-eficiencia_red, defecto 0.92) → parcela (infiltración = aplicada ×
  eficiencia_red × eficiencia_aplicación 0.85). Energía = bombeo × kWh/m3 (0.4),
  coste = agua (0.25 €/m3) + energía (0.25 €/kWh) + labor abstracta.
- Restricciones: rangos físicos (422), agua/caja insuficiente (422 con disponible
  tras aporte), capacidad bombeo + tope suministro por prorrateo proporcional con
  eventos `bombeo_limitado`/`suministro_limitado`, avería determinista
  (prob. 0.02/día, semilla:fecha) con riego 0 y pendiente registrada.
- Conservación de masa verificada en cada paso pre-redondeo con tolerancia fijada
  1e-9 (mm y m3); almacenado redondeado (suelo 2 dec, depósito 1 dec) con
  descuadre máximo documentado 0.02. Descuadre mayor → AssertionError.
- Planificación: mismas acciones día/semana; si la demanda supera bombeo/suministro
  se aplica parcial proporcional y el resto queda pendiente (evento explícito).
  Riego > agua disponible tras aporte se rechaza entero (422), no se finge.
- Sin derechos reales: ninguna dotación afirma derecho de agua; fuente actual y
  revisión requeridas para cualquier uso fuera del juego (ver METODOS_AGUA).
