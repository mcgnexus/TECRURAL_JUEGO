# Protocolo de validación — marco general (Fase 7, juego; profesional desactivado)

## 1. Métricas por uso
Magnitudes: MAE, RMSE, sesgo (unidades de la variable). Intervalos: cobertura
vs nominal. Clasificación (p. ej. estrés): sensibilidad/especificidad.
Siempre con método simple actual como base y mejora informada.

## 2. Umbrales
Por escrito con expertos y usuarios: valor, unidad, muestra mínima y límites de
aplicabilidad (`content/umbrales.json`). Hoy todos pendientes → bloquean aprobación.
Prohibido inventar porcentajes o aprobar con datos insuficientes.

## 3. Datos
Separar por finca y campaña; prueba nunca usada en calibración; sin fuga temporal
(prueba posterior) ni espacial (fincas disjuntas). Subgrupos: seco/húmedo, edad,
suelo, variedad. Informar n, incertidumbre y errores por subgrupo.

## 4. Ensayo prospectivo
Con técnicos en paralelo: predicción emitida y fechada antes de medir; comparar con
medición posterior; documentar desacuerdos, riesgos, supervisión humana y negativos.

## 5. Aprobación
Una por función/cultivo/ámbito con versión exacta, firmas agronómica y producto,
caducidad, controles de cambios, seguimiento y retirada. Sin ella, profesional
desactivado; el juego no se bloquea.

## 6. Reproducibilidad y deriva
Informe desde datos autorizados + código/versiones congeladas (`scripts/run_validation.py`);
revisión independiente; deriva, incidentes y revocación ante cambios de datos,
fuentes o modelo. Sin finca concreta evaluada no declarar gemelo digital validado.
