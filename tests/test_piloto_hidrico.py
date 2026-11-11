from copy import deepcopy

from packages.simulator.engine import ParcelState, SimState, WeatherDay
from packages.simulator.water_comparison import compare_water


def test_comparison_uses_independent_copies_and_identical_weather():
    state = SimState(parcels=[ParcelState(id='P1', crop='aguacate')])
    original = deepcopy(state)
    weather = [WeatherDay(date='2026-01-02', precip_mm=1, et0_mm=3, kind='pronostico')]
    result = compare_water(state, 'P1', weather, {}, 4, 4)
    assert result['habitual'] == result['alternativa']
    assert state == original
    assert result['habitual'][0]['fecha'] == '2026-01-02'


def test_comparison_rejects_simulated_weather():
    state = SimState(parcels=[ParcelState(id='P1', crop='aguacate')])
    weather = [WeatherDay(date='2026-01-02', precip_mm=1, et0_mm=3, kind='simulado')]
    import pytest
    with pytest.raises(ValueError):
        compare_water(state, 'P1', weather, {}, 4, 2)
