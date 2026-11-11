"""Previsión de Open-Meteo para el piloto, sin sustitución por datos ficticios."""
from datetime import date, timedelta
import math

from packages.simulator.engine import WeatherDay


def search_municipalities(query: str) -> list[dict]:
    import httpx
    response = httpx.get('https://geocoding-api.open-meteo.com/v1/search',
                         params={'name': query, 'count': 20, 'language': 'es', 'format': 'json'}, timeout=12)
    response.raise_for_status()
    return [{k: item.get(k) for k in ('name', 'admin1', 'admin2', 'latitude', 'longitude', 'country_code')}
            for item in response.json().get('results', [])
            if item.get('country_code') == 'ES' and item.get('latitude') is not None and item.get('longitude') is not None]


def parse_forecast(payload: dict, start: date, days: int) -> list[WeatherDay]:
    daily = payload.get('daily') or {}
    dates = daily.get('time') or []
    rain = daily.get('precipitation_sum') or []
    et0 = daily.get('et0_fao_evapotranspiration') or []
    result = []
    for i in range(days):
        expected = (start + timedelta(days=i)).isoformat()
        if i >= len(dates) or i >= len(rain) or i >= len(et0) or dates[i] != expected:
            raise ValueError('Previsión incompleta o con fechas ausentes.')
        r, e = rain[i], et0[i]
        if (not isinstance(r, (int, float)) or isinstance(r, bool) or not math.isfinite(r) or not 0 <= r <= 500
                or not isinstance(e, (int, float)) or isinstance(e, bool) or not math.isfinite(e) or not 0 <= e <= 15):
            raise ValueError('Previsión meteorológica incompleta o inválida.')
        result.append(WeatherDay(date=expected, precip_mm=float(r), et0_mm=float(e), kind='pronostico'))
    return result
