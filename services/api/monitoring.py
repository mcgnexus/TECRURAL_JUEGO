"""Monitorización Fase 8: disponibilidad, fuentes, tiempos y errores. Sin secretos ni personales."""
from __future__ import annotations
import time
_START = time.time()
CALC_MS: list[float] = []
ERRORES: list[dict] = []

def registrar_calculo(ms: float) -> None:
    CALC_MS.append(ms)
    del CALC_MS[:-100]

def registrar_error(tipo: str) -> None:
    ERRORES.append({"tipo": tipo, "at": time.time()})
    del ERRORES[:-100]

def estado() -> dict:
    import statistics
    return {
        "uptime_s": round(time.time() - _START, 1),
        "fuentes": {"aemet": "intermitente 401/500", "siar": "caído 500", "open-meteo": "reserva",
                     "raif": "portal/app sin API", "antiguedad": "ver instantánea por día"},
        "calculo_ms": {"n": len(CALC_MS),
                       "p50": round(statistics.median(CALC_MS), 2) if CALC_MS else 0},
        "errores_100": len(ERRORES),
        "nota": "sin secretos, claves ni datos personales",
    }
