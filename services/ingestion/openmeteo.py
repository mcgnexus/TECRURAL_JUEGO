"""Open-Meteo — complementario modelizado, sin clave para uso estándar (Fase 2: contrato común).

Contrato comercial/productos/licencia por verificar. Siempre modelizado, nunca observación.
Costa Tropical por defecto: Motril 36.75,-3.87. Zona: Europe/Madrid.
"""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo

from services.ingestion import provider as P
from services.ingestion.validate import validate

TZ = "Europe/Madrid"
LAT, LON = 36.75, -3.87


def _client(timeout: int = 25):
    import httpx
    return httpx.Client(timeout=timeout)


def raw_daily(lat: float = LAT, lon: float = LON, days: int = 7, past_days: int = 0, client=None) -> dict:
    import httpx
    close = False
    c = client or _client()
    if client is None:
        close = True
    try:
        r = c.get("https://api.open-meteo.com/v1/forecast",
                  params={"latitude": lat, "longitude": lon,
                          "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
                          "forecast_days": max(1, min(days, 16)), "past_days": max(0, min(past_days, 92)),
                          "timezone": TZ})
        r.raise_for_status()
        return r.json()
    finally:
        if close:
            c.close()


def fetch_daily_forecast(lat: float = LAT, lon: float = LON, days: int = 7) -> dict:
    """Compatibilidad Fase 0/1."""
    data = raw_daily(lat, lon, days)
    data["_procedencia"] = {"fuente": "Open-Meteo (modelizado, no observación)",
                            "lat": lat, "lon": lon, "aviso": "licencia/contrato comercial por verificar"}
    return data


def _to_points(data: dict, station_id: str, kind: str, issued: str | None) -> P.SeriesResult:
    d = data.get("daily", {})
    times = d.get("time", [])
    pts = [P.SeriesPoint(date=t,
                         precip_mm=(d.get("precipitation_sum") or [None])[i] if i < len(d.get("precipitation_sum") or []) else None,
                         et0_mm=(d.get("et0_fao_evapotranspiration") or [None])[i] if i < len(d.get("et0_fao_evapotranspiration") or []) else None,
                         tmin_c=(d.get("temperature_2m_min") or [None])[i] if i < len(d.get("temperature_2m_min") or []) else None,
                         tmax_c=(d.get("temperature_2m_max") or [None])[i] if i < len(d.get("temperature_2m_max") or []) else None,
                         kind=kind, station_id=station_id,
                         issued_at=issued, tz=TZ) for i, t in enumerate(times)]
    ok, q = validate(pts)
    return P.SeriesResult(provider="openmeteo", station_id=station_id, kind=kind, points=ok,
                          gaps=q["gaps"], dropped_invalid=q["dropped_invalid"],
                          duplicates_removed=q["duplicates_removed"], issued_at=issued,
                          provenance={"fuente": "Open-Meteo (modelizado)", "tz": TZ,
                                      "aviso": "modelo, no observación; licencia comercial por verificar"})


def forecast(station: dict, days: int = 7, client=None) -> P.SeriesResult:
    from services.ingestion.cache import fetch_with_cache
    params = {"lat": station["lat"], "lon": station["lon"], "days": days}
    issued = datetime.now(ZoneInfo(TZ)).isoformat(timespec="minutes")

    def run():
        return raw_daily(station["lat"], station["lon"], days, client=client)

    payload, obsolete = fetch_with_cache("openmeteo", station["id"], "pronostico", params, run)
    res = _to_points(payload, station["id"], "pronostico", issued)
    res.obsolete = obsolete
    return res


def past(station: dict, past_days: int = 7, client=None) -> P.SeriesResult:
    """Días previos del modelo (estimación modelizada, NO observación)."""
    from services.ingestion.cache import fetch_with_cache
    params = {"lat": station["lat"], "lon": station["lon"], "past": past_days}
    issued = datetime.now(ZoneInfo(TZ)).isoformat(timespec="minutes")

    def run():
        return raw_daily(station["lat"], station["lon"], 1, past_days=past_days, client=client)

    payload, obsolete = fetch_with_cache("openmeteo", station["id"], "estimacion", params, run)
    res = _to_points(payload, station["id"], "estimacion", issued)
    res.obsolete = obsolete
    res.provenance["aviso"] = "pasado del modelo: estimación, no observación"
    return res
