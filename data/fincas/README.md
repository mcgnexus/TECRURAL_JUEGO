# Inventario fincas colaboradoras — plantilla y reglas

Sin acuerdo firmado de uso, consentimiento/base aplicable, control de acceso y permiso de publicación de métricas: NO se registra ningún dato real aquí. Estado actual: bloqueado hasta acuerdo.

Cuando exista acuerdo, una fila por finca×parcela×campaña:

`finca_id,parcela_id,campaña,fecha,especie,variedad,edad_anios,superficie_ha,marco,riego_tipo,riego_medido_m3,suelo_textura,cosecha_comercial_kg,clima_estacion_id,distancia_m,altitud_m,manejo_notas,cambios_relevantes,responsable,permiso_ref`

Limpieza pactada antes de cargar: unidades coherentes (mm, m³, ha, €), zona horaria, observación/pronóstico con fecha emisión, valores imposibles rechazados, procedencia por dato.

Ver `data/fixtures/weather_week.csv` como ejemplo sintético (no son datos reales).
