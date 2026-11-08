# TecRural — Simulador agrario (especificación inicial v0.1 en construcción)

Base para gemelo digital futuro. **Juego + experimental por defecto. Modo profesional DESACTIVADO.**

> Regla: ninguna salida del juego es recomendación para explotación real sin barreras profesionales del plan maestro.

## Estructura

- `apps/web/` interfaz móvil PWA (React+TS, isométrica 2.5D táctil — PixiJS pendiente de prueba Fase 0)
- `services/api/` cuentas, partidas, permisos (FastAPI)
- `packages/simulator/` motor diario puro `step(state, actions, weather_day, parameters, rng_seed)`
- `packages/domain/` contratos y unidades (fuente para OpenAPI)
- `services/ingestion/` adaptadores, calidad, caché, procedencia (AEMET/SiAR/Open-Meteo/RAIF — solo con clave y licencia verificada)
- `packages/content/` parámetros y fichas de evidencia versionados (etiquetados JUEGO/EXPERIMENTAL)
- `tests/` unitarias, integración, aceptación
- `data/fixtures/` sintéticos o públicos autorizados, sin secretos
- `docs/evidence/` fuentes, modelos, supuestos, validación
- `docs/decisions/` decisiones técnicas y aprobaciones

## Modos

| Modo | Estado |
|------|--------|
| juego | activo (reglas explícitas, no son prácticas reales) |
| experimental | activo con etiqueta e incertidumbre |
| profesional validado | DESACTIVADO por cultivo/función/zona |

Riego, nutrición, diagnóstico, tratamientos y previsión de cosecha requieren aprobaciones independientes.

## Arranque rápido (sin Docker — Docker no disponible en esta máquina)

```powershell
python -m venv .venv; .\.venv\Scripts\Activate
pip install -r services/api/requirements.txt -r packages/simulator/requirements.txt
pytest -q
uvicorn services.api.main:app --reload --port 8000
```

Web (requiere npm):
```powershell
cd apps/web; npm install; npm run dev
```

## Trazabilidad

Cada resultado conserva: fecha cálculo y de datos, zona, unidades, procedencia, versiones modelo/parámetros, supuestos, incertidumbre y limitaciones. Distinguir observación / pronóstico / estimación / simulado.
