# 0017 — Prioridad 3: juego usable y lanzamiento de ensayo

Fecha: 2026-11-10. Estado: flujos web completos en ensayo; publicación condicionada.

- Web (`apps/web`): finca y avance (día/semana/clima real), agua/inventario/
  economía (riego, cosecha, venta por canal, fertilizante, bloqueo spray),
  historial con ledger, previsión por intervalos, cuenta con correo y contraseña, guardado
  versionado/backup, sistema (privacidad, profesional, monitorización, checklist).
  API configurable por `VITE_API_URL`; offline deshabilita avanzar/guardar sin
  fingir datos; limitaciones visibles (efímera temporal, ensayo sin garantía).
- PWA: manifest con iconos, `sw.js` solo app-shell (nunca inventa juego),
  registro en `main.tsx`; build 163 kB js (< 300 kB). Accesibilidad: teclado,
  lector, foco, contraste y etiquetas verificados por script.
- Ensayo: 3 públicos (agricultores, técnicos/estudiantes, general/educación),
  objetivos previos en `ENSAYO_USUARIOS.md`; resultados aparte.
- Puerta: checklist en ensayo, 0 críticas, riesgos visibles, revisiones legal y
  agronómica pendientes → sin lanzamiento a producción.
