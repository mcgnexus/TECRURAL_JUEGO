# Fichas de parámetros — juego v0.3 (2026-11-10, revisor: pendiente)

Leyenda grado: `juego` = regla explícita no calibrada · `desconocido` = sin evidencia, no usar · `validado` = solo tras barrera profesional (ninguno aún).

| Variable | Unidad | Valor/rango juego | Fuente | Grado | Ámbito | Fecha | Revisor |
|---|---|---|---|---|---|---|---|
| runoff_coef | fracción | 0.15 | elección juego | juego | Costa Tropical aprox | 2026-11-08 | pendiente |
| irrigation_efficiency | fracción | 0.85 | elección juego | juego | goteo ficticio | 2026-11-08 | pendiente |
| kc aguacate/mango/chirimoyo | — | 0.8/0.75/0.7 | elección juego | juego | ficticio | 2026-11-08 | pendiente |
| max_storage_mm zona radicular | mm | 80 | elección juego | juego | ficticio | 2026-11-08 | pendiente |
| precio aguacate/mango/chirimoyo | €/kg | 2.2/1.6/2.8 | elección juego | juego | ficticio | 2026-11-08 | pendiente |
| coste riego | €/m³ | 0.25 | elección juego | juego | ficticio | 2026-11-08 | pendiente |
| aporte dotación ficticia | m³/día | 8.0 | elección juego, sin derecho real | juego | ficticio | 2026-11-10 | pendiente |
| capacidad bombeo | m³/día | 60.0 | elección juego | juego | ficticio | 2026-11-10 | pendiente |
| tope suministro configurable | m³/día | 50.0 | elección juego, sin derecho real | juego | ficticio | 2026-11-10 | pendiente |
| eficiencia red | fracción | 0.92 | elección juego | juego | ficticia | 2026-11-10 | pendiente |
| energía bombeo | kWh/m³ | 0.4 | elección juego | juego | ficticio | 2026-11-10 | pendiente |
| coste energía | €/kWh | 0.25 | elección juego | juego | ficticio | 2026-11-10 | pendiente |
| prob. avería juego | fracción/día | 0.02 | elección juego determinista | juego | ficticia | 2026-11-10 | pendiente |
| tolerancia masa | mm/m³ | 1e-9 (almacenado 0.02) | fijada Fase 3 | juego | — | 2026-11-10 | pendiente |
| Kc real por variedad/edad/manejo | — | — | — | desconocido | — | — | pendiente |
| Umbrales estrés hídrico reales | — | — | — | desconocido | — | — | pendiente |
| ETc / necesidades riego reales | mm/día | — | — | desconocido | ET0 estación ≠ ET parcela | — | pendiente |
| Fenología detallada por variedad | — | — | — | desconocido | — | — | pendiente |
| Dosis fertilización | — | — | — | desconocido | abstracta en juego, sin dosis | — | pendiente |
| Diagnóstico / dosis fitosanitaria | — | — | — | desconocido | aviso regional ≠ diagnóstico; requiere etiqueta+MAPA+técnico | — | pendiente |
| Previsión cosecha calibrable | kg | — | — | desconocido | requiere fincas colaboradoras | — | pendiente |
| factor edad juego | — | joven 0.5 / adulto 1.0 / viejo 0.7 | elección juego | juego | ficticio | 2026-11-10 | pendiente |
| merma juego | fracción | 0.05 | elección juego | juego | ficticio | 2026-11-10 | pendiente |
| tope kg/árbol juego | kg | 120 | elección juego | juego | ficticio | 2026-11-10 | pendiente |
| canal cooperativa/mercado | factor | 0.95 / 1.1 | escenario juego | juego | ficticio | 2026-11-10 | pendiente |
| coste fijo | €/ha/día | 0.0 | elección juego | juego | ficticio | 2026-11-10 | pendiente |
| interés deuda juego | fracción/día | 0.0002 | escenario juego | juego | ficticio | 2026-11-10 | pendiente |
| NPK15/NK juego | fracción N | 0.15 / 0.10 | elección juego | juego | ficticio | 2026-11-10 | pendiente |
| exportación N fruta juego | kg/kg | 0.002 | supuesto juego | juego | ficticio | 2026-11-10 | pendiente |
| prob. observación plaga juego | fracción | 0.15 | sin calibrar | juego | ficticia | 2026-11-10 | pendiente |

Próximo paso: agrónomo colaborador rellena o confirma cada fila con publicación primaria o ensayo (IFAPA u otro) con rangos aplicables, o la deja en `desconocido`.
