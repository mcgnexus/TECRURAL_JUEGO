import pytest
from services.api.irrigation_inputs import irrigation_mm_per_event


def test_volume_and_duration_are_converted_to_mm_per_event():
    assert irrigation_mm_per_event(area_ha=1, volume_m3=10) == pytest.approx(1)
    assert irrigation_mm_per_event(area_ha=1, flow_m3_hour=5, duration_hours=2) == pytest.approx(1)


def test_duration_without_flow_is_not_assumed():
    with pytest.raises(ValueError):
        irrigation_mm_per_event(area_ha=1, duration_hours=2)


def test_negative_flow_and_duration_are_invalid():
    with pytest.raises(ValueError):
        irrigation_mm_per_event(area_ha=1, flow_m3_hour=-5, duration_hours=-2)


def test_conversion_endpoint_rejects_missing_flow():
    from fastapi.testclient import TestClient
    from services.api.main import app
    response = TestClient(app).post('/pilot/convertir-riego', json={'area_ha': 1, 'duration_hours': 2})
    assert response.status_code == 422
