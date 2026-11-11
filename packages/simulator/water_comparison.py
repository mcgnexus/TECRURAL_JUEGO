"""Comparación orientativa no destructiva con una misma previsión meteorológica."""
from copy import deepcopy

from packages.simulator.engine import ParcelAction, SimState, WeatherDay, step


def compare_water(state: SimState, parcel_id: str, weather: list[WeatherDay],
                  parameters: dict, usual_mm: float, alternative_mm: float) -> dict:
    if not weather or any(day.kind != 'pronostico' for day in weather):
        raise ValueError('Se necesita una previsión meteorológica completa; no se admite clima ficticio.')
    if not any(parcel.id == parcel_id for parcel in state.parcels):
        raise ValueError('Parcela no encontrada.')
    results = {}
    for label, irrigation in [('habitual', usual_mm), ('alternativa', alternative_mm)]:
        scenario = deepcopy(state)
        points = []
        for day in weather:
            step(scenario, {parcel_id: ParcelAction(irrigation_mm=irrigation)}, day, parameters, rng_seed=1234)
            parcel = next(p for p in scenario.parcels if p.id == parcel_id)
            points.append({'fecha': day.date, 'agua_estimada_mm': parcel.soil_water_mm})
        results[label] = points
    return results
