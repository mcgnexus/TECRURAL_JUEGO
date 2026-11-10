# 0016 — Prioridad 2: barrera profesional y conservación verificada

Fecha: 2026-11-10. Estado: implementado en juego, profesional desactivado.

- Barrera: `aprobacion_valida` exige firmas distintas, caducidad futura,
  dataset + permiso verificables, revisión independiente con revisor distinto
  de quien calibró, versiones exactas de código y parámetros, informe
  reproducible aprobable y alcance coincidente. Cualquier cambio de versión,
  fuente o modelo revoca. `POST /approvals` persiste borradores y rechaza lo
  incompleto; `GET /professional/status` solo activa con informe vinculado.
- Conservación: ledger con `rebrote` explícito (+100 kg/cosecha); pruebas de
  agua multdía con cambio de superficie, fruta (pendiente + rebrotes − bruto,
  neto con merma 5%) y caja semanal con tolerancias de redondeo documentadas.
  Sin entradas explícitas no se crea agua, fruta ni dinero.
- Reproducibilidad: la instantánea guarda acciones, semilla y versiones más
  estado inicial y resultado; `POST /games/{id}/replay/{day}` compara eventos,
  indicadores, estado, ledger y previsión; huecos 422 salvo `permitir_ficticio`
  con ficticio etiquetado; versiones distintas → 409.
- Cultivos/sanidad: auditoría `auditar_evidencia` (sin `validado`, sin vigentes,
  aviso ≠ diagnóstico); supuestos juego etiquetados; tratamientos bloqueados.
  Sin fuente primaria nueva no hay sustitución de modelos.
