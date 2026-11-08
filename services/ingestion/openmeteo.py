"""Open-Meteo — complementario modelizado, sin clave para uso estándar.

Contrato comercial/productos/licencia por verificar (ver docs/evidence/SOURCES.md).
Distinguir siempre modelo de medición. Costa Tropical aprox: Motril 36.75,-3.87.
"""
from __future__ import annotations

LAT, LON = 36.75, -3.87


def fetch_daily_forecast(lat: float = LAT, lon: float = LON, days: int = 7) -> dict:
    import httpx
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
              "forecast_days": max(1, min(days, 16)), "timezone": "Europe/Madrid"}
    with httpx.Client(timeout=25) as c:
        r = c.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    data["_procedencia"] = {"fuente": "Open-Meteo (modelizado, no observación)",
                            "lat": lat, "lon": lon, "aviso": "licencia/contrato comercial por verificar"}
    return data
