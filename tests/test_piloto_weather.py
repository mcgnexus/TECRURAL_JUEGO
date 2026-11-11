from datetime import date
import pytest
from services.ingestion.pilot_weather import parse_forecast


def test_forecast_requires_complete_consecutive_days():
    today = date(2026, 1, 1)
    data = {'daily': {'time': ['2026-01-01', '2026-01-02'],
                      'precipitation_sum': [0, 1], 'et0_fao_evapotranspiration': [2, 3]}}
    result = parse_forecast(data, today, 2)
    assert [d.date for d in result] == ['2026-01-01', '2026-01-02']
    assert all(d.kind == 'pronostico' for d in result)


def test_forecast_rejects_missing_or_gapped_weather():
    today = date(2026, 1, 1)
    data = {'daily': {'time': ['2026-01-01', '2026-01-03'],
                      'precipitation_sum': [0, None], 'et0_fao_evapotranspiration': [2, 3]}}
    with pytest.raises(ValueError):
        parse_forecast(data, today, 2)


def test_pilot_municipality_search_filters_non_spanish_results(monkeypatch):
    from fastapi.testclient import TestClient
    from services.api.main import app
    from services.ingestion import pilot_weather
    monkeypatch.setattr(pilot_weather, 'search_municipalities', lambda q: [
        {'name': 'Motril', 'admin1': 'Andalucía', 'latitude': 36.75, 'longitude': -3.52, 'country_code': 'ES'}])
    response = TestClient(app).get('/pilot/municipios', params={'q': 'Motril'})
    assert response.status_code == 200
    assert response.json()['municipios'][0]['name'] == 'Motril'


def test_pilot_comparison_fails_closed_when_weather_unavailable(monkeypatch):
    from fastapi.testclient import TestClient
    from services.api.main import app
    from services.ingestion import openmeteo
    def unavailable(*args, **kwargs):
        raise OSError('offline')
    monkeypatch.setattr(openmeteo, 'raw_daily', unavailable)
    response = TestClient(app).post('/pilot/comparar', json={
        'latitude': 36.75, 'longitude': -3.52, 'crop': 'aguacate', 'area_ha': 1,
        'usual_mm': 4, 'alternative_mm': 2})
    assert response.status_code == 503


def test_pilot_comparison_uses_forecast_and_equal_inputs(monkeypatch):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from fastapi.testclient import TestClient
    from services.api.main import app
    from services.ingestion import openmeteo
    today = datetime.now(ZoneInfo('Europe/Madrid')).date()
    monkeypatch.setattr(openmeteo, 'raw_daily', lambda *args, **kwargs: {'daily': {
        'time': [(today + timedelta(days=i)).isoformat() for i in range(5)],
        'precipitation_sum': [0] * 5, 'et0_fao_evapotranspiration': [3] * 5}})
    response = TestClient(app).post('/pilot/comparar', json={
        'latitude': 36.75, 'longitude': -3.52, 'crop': 'aguacate', 'area_ha': 1,
        'usual_mm': 4, 'alternative_mm': 4})
    assert response.status_code == 200
    result = response.json()
    assert len(result['meteorologia']['dias']) == 5
    assert result['escenarios']['habitual'] == result['escenarios']['alternativa']
