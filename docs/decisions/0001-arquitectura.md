# 0001 — Arquitectura y stack inicial (Fase 0)

Fecha: 2026-11-08. Estado: propuesta en prueba.

- Web: React + TypeScript + Vite PWA, móvil primero. Representación inicial SVG/Canvas DOM (sin dependencia pesada) para validar bucle de juego en móvil con conexión débil. PixiJS (MIT) queda como opción principal para isométrica 2.5D táctil, pendiente de prueba de rendimiento/tamaño vs alternativa ligera. No se impone si la prueba demuestra alternativa mejor.
- API: Python FastAPI (MIT). Contratos vía OpenAPI, tipos generados para cliente. Sin duplicar lógica científica en cliente.
- Motor: Python puro en `packages/simulator`, sin red ni reloj global, determinista por `rng_seed`.
- Persistencia: PostgreSQL (licencia PostgreSQL) + S3-compatible en despliegue (contenedores). En local/desarrollo sin Docker: SQLite por defecto conmutable por `DATABASE_URL`. Migraciones versionadas de partidas.
- Contenedores: `docker-compose.yml` para api+db aunque en esta máquina no hay Docker — no verificado localmente, registrado como laguna.
- Licencias pendientes de re-verificación en Fase 0: AEMET OpenData (clave y condiciones por producto), SiAR (alta API), Open-Meteo (contrato comercial/productos), RAIF (cobertura/método acceso), FAO AquaCrop/FAO-56 (aplicabilidad, no asumir calibración en aguacate/mango/chirimoyo), MAPA (verificación por fecha/cultivo/plaga), precios/mercados y cartografía/suelos (licencia y precisión).

Decisión: adaptar organización a tecnología elegida; no obligar a monorepo concreto si existe uno adecuado (aquí se crea desde cero).
