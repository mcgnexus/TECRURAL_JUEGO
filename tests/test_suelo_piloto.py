import pytest
from services.api.pilot_soil import resolve_soil


def test_textures_have_distinct_game_capacities():
    sandy = resolve_soil('arenoso')
    clay = resolve_soil('arcilloso')
    assert sandy['capacity_mm'] != clay['capacity_mm']
    assert sandy['capacity_source'] == 'supuesto de juego no validado'


def test_local_data_overrides_defaults_without_claiming_measurement():
    soil = resolve_soil('franco', capacity_mm=120, initial_mm=30)
    assert soil['capacity_mm'] == 120 and soil['initial_mm'] == 30
    assert soil['capacity_source'] == 'introducido por el usuario, sin verificar'


def test_initial_water_cannot_exceed_capacity():
    with pytest.raises(ValueError):
        resolve_soil('arenoso', capacity_mm=30, initial_mm=40)
