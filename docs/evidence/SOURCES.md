# Registro de fuentes y evidencia — rev. 2026-11-08 (Fase 0)

No inferir derechos de redistribución, calidad parcelaria ni existencia de API desde una web. Estación cercana ≠ microclima parcela. ET0 estación ≠ ET parcela.

| Fuente | Uso propuesto | URL oficial | Titular | Cobertura esp./temp. | Licencia / atribución / uso comercial | Frecuencia / latencia | Auth / límites / coste | Formato | Responsable | Fecha revisión | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AEMET OpenData | obs., predicción, avisos | https://opendata.aemet.es | AEMET | España/municipio (ej. Motril 18140) | condiciones por producto, verificar | diaria | AEMET_API_KEY solo servidor, verificado 2026-11-08 | JSON (meta→datos) | — | 2026-11-08 | verificado predicción diaria |
| RIA Andalucía / SiAR | series agroclimáticas, ET0 | https://servicio.mapa.gob.es/siarweb/ · manual PDF v2.2 | IFAPA / MAPA | 100 estaciones Andalucía desde 1999; horaria/diaria/semanal/mensual. Objetivo Motril: GR11 Almuñécar (pendiente confirmar) | datos abiertos web; API con token servidor (condiciones MAPA) | medio-horaria→mensual | SIAR_TOKEN solo servidor; 500 persistente lado servicio 2026-11-09 (verificado hasta con token ficticio) | JSON | — | 2026-11-09 | cliente conforme al manual, servicio caído; ET0 estación ≠ ET parcela |
| Open-Meteo | predicción/modelizado complementario | https://api.open-meteo.com | Open-Meteo | global, 16 días | según licencia, distinguir modelo de medición | horaria/diaria | sin clave uso estándar, verificado 2026-11-08 | JSON | — | 2026-11-08 | verificado complementario |
| RAIF Andalucía | contexto fitosanitario | https://www.juntadeandalucia.es/organismos/agriculturapescaaguaydesarrollorural/areas/agricultura/sanidad-vegetal/paginas/web-raif.html · ficha datos.gob.es | Junta Andalucía | cultivos Producción Integrada Andalucía; visor SIG semanal; 200+ estaciones clima | acceso web/app; sin API inferida | semanal | app RAIF; método permitido: portal/app | web/app | — | 2026-11-08 | pendiente cobertura subtropicales; aviso regional ≠ diagnóstico |
| FAO AquaCrop / FAO-56 | balance hídrico, ET | — | FAO | — | evaluar licencia; NO asumir calibración en estos frutales | — | — | — | — | 2026-11-08 | pendiente |
| IFAPA subtropicales | contraste local | — (publicación primaria concreta pendiente) | — | — | — | — | — | — | — | 2026-11-08 | laguna: sin publicación identificada |
| Registro MAPA fitosanitarios | estado/usos autorizados | — | MAPA | — | verificar fecha/cultivo/plaga/etiqueta | — | — | — | — | 2026-11-08 | pendiente, sin recomendación accionable |
| Fincas/técnicos | calibración | — | — | plantilla en data/fincas/ | requiere acuerdo firmado; sin acuerdo no hay datos | — | — | CSV | — | 2026-11-08 | bloqueado hasta acuerdo |
| Precios/mercados oficiales | ingresos históricos | — | — | producto/categoría/origen/unidad/fecha pendientes | históricos ≠ futuros | — | — | — | — | 2026-11-08 | pendiente |
| Cartografía/suelos oficiales | contexto geográfico | — | — | revisar precisión | regional ≠ análisis parcela | — | — | — | — | 2026-11-08 | pendiente |

Verificaciones sin exponer claves: AEMET (predicción 18140 OK), Open-Meteo (daily 2 días OK), DeepSeek (explicación juego OK). SiAR/RAIF: comprobadas web oficial y mecanismo de acceso, sin consultas con clave aún.
