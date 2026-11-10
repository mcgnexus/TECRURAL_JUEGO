# 0014 — Calidad visual, accesibilidad y lanzamiento (Fase 8)

Fecha: 2026-11-10. Estado: ensayo preparado, lanzamiento pendiente de puerta.

- Estilo y recursos: `GUIA_ESTILO.md` + `recursos.json` con licencias; Canvas 2D
  isométrico apto pantallas 360px y 3G; PWA con manifest + offline primero.
- Ensayo con 3 públicos (agricultores subtropicales, técnicos/estudiantes,
  público general/educación), ≥2 por grupo; objetivos fijados antes de reclutar,
  metas no presentadas como mediciones; resultados (incluidos negativos) aparte.
- Seguridad/carga/recuperación: límites OTP y sesiones Fase 6, aislamiento por
  propietario, sin secretos en respuestas; carga con `check_carga.py`; recuperación
  por versionado/backup Fase 6. Monitorización `/monitoring/health` sin sensibles:
  disponibilidad, antigüedad/calidad fuentes, tiempos cálculo y errores.
- Puerta de lanzamiento: checklist aprobada, 0 críticas abiertas, riesgos y
  funciones experimentales visibles, revisiones legal y agronómica completadas
  para lo publicado. Sin eso, solo entorno de ensayo.
