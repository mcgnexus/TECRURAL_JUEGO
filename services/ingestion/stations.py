"""Registro de estaciones (Fase 2). Default: Motril. Selección manual permitida.

Estación cercana ≠ microclima parcela: distancia y altitud siempre visibles.
"""
from __future__ import annotations

STATIONS = {
    "motril-18140": {
        "id": "motril-18140", "label": "Motril (municipio INE 18140)", "por_defecto": True,
        "aemet_municipio": "18140", "lat": 36.75, "lon": -3.87, "altitud_m": 30,
        "altitud_estado": "aproximada, pendiente verificar",
        "distancia_estado": "municipio de referencia, no parcela concreta",
        "observacion_aemet": "pendiente: requiere id de estación convencional (no municipio)",
        "cobertura": {"aemet_forecast": True, "openmeteo": True, "siar": "pendiente alta"},
    },
}

DEFAULT_STATION = "motril-18140"


def get_station(sid: str | None) -> dict:
    sid = sid or DEFAULT_STATION
    st = STATIONS.get(sid)
    if not st:
        raise ValueError(f"estación desconocida: {sid}. Disponibles: {sorted(STATIONS)}")
    return st


def list_stations() -> list[dict]:
    return list(STATIONS.values())
