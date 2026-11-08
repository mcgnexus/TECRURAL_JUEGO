# Motor TecRural — puro, sin red ni reloj global.
# Balance por zona radicular (mm):
#   S_final = S_inicial + lluvia_efectiva + riego_infiltrado - ET_real - drenaje - escorrentia
# Todo etiquetado JUEGO/EXPERIMENTAL salvo que pase barrera profesional (desactivada por defecto).
from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from typing import Literal

MODEL_VERSION = "sim-0.1.0"
SCHEMA_VERSION = 1

CropKind = Literal["aguacate", "mango", "chirimoyo"]
WaterSourceKind = Literal["observacion", "pronostico", "estimacion", "simulado"]


@dataclass
class WeatherDay:
    date: str  # ISO YYYY-MM-DD
    precip_mm: float
    et0_mm: float
    tmin_c: float = 15.0
    tmax_c: float = 25.0
    kind: WaterSourceKind = "simulado"
    station_id: str = "ficticia-costa-tropical"
    station_distance_km: float | None = None


@dataclass
class ParcelAction:
    irrigation_mm: float = 0.0  # lámina solicitada
    fertilize_abstract: bool = False  # abstracta, sin dosis real
    prune: bool = False
    scout: bool = False
    harvest: bool = False


@dataclass
class ParcelState:
    id: str
    crop: str
    variety: str = "sin-documentar"
    planting_year: int = 2018
    density_trees_ha: float = 400.0
    area_ha: float = 1.0
    soil_water_mm: float = 40.0  # almacenamiento zona radicular
    max_storage_mm: float = 80.0
    health_0_1: float = 0.9
    phenology: str = "produccion"
    pending_fruit_kg: float = 500.0
    cum_costs_eur: float = 0.0
    cum_yield_kg: float = 0.0


@dataclass
class SimState:
    schema_version: int = SCHEMA_VERSION
    day: str = "2026-01-01"
    cash_eur: float = 5000.0
    reservoir_m3: float = 200.0
    reservoir_max_m3: float = 500.0
    parcels: list[ParcelState] = field(default_factory=list)
    difficulty: str = "normal"
    realism: str = "simplificado"


def _validate(state: SimState, actions: dict[str, ParcelAction], weather: WeatherDay) -> list[str]:
    errors: list[str] = []
    if weather.precip_mm < 0 or weather.precip_mm > 500:
        errors.append(f"precip_mm fuera de rango físico: {weather.precip_mm}")
    if weather.et0_mm < 0 or weather.et0_mm > 15:
        errors.append(f"et0_mm fuera de rango físico: {weather.et0_mm}")
    for p in state.parcels:
        a = actions.get(p.id, ParcelAction())
        if a.irrigation_mm < 0 or a.irrigation_mm > 100:
            errors.append(f"riego imposible en {p.id}: {a.irrigation_mm} mm")
        if p.area_ha <= 0:
            errors.append(f"superficie inválida en {p.id}")
    return errors


def step(
    state: SimState,
    actions: dict[str, ParcelAction],
    weather: WeatherDay,
    parameters: dict,
    rng_seed: int,
) -> dict:
    """Un paso diario puro y determinista. No hace red ni usa reloj global."""
    errs = _validate(state, actions, weather)
    if errs:
        raise ValueError("; ".join(errs))

    rng = random.Random(f"{rng_seed}:{weather.date}")
    pset_version = str(parameters.get("version", "game-0.1"))
    events: list[dict] = []

    # Parámetros EXPLÍCITOS DE JUEGO — no son prácticas reales.
    runoff_coef = float(parameters.get("runoff_coef", 0.15))  # fracción lluvia que escurre
    irr_efficiency = float(parameters.get("irrigation_efficiency", 0.85))
    kc = parameters.get("kc_game", {"aguacate": 0.8, "mango": 0.75, "chirimoyo": 0.7})
    price = parameters.get("price_eur_kg_game", {"aguacate": 2.2, "mango": 1.6, "chirimoyo": 2.8})
    cost = parameters.get("costs_eur_game", {"irrigation_eur_per_m3": 0.25, "labor_day_eur": 60.0})

    total_irr_m3 = 0.0
    for p in state.parcels:
        a = actions.get(p.id, ParcelAction())
        k = float(kc.get(p.crop, 0.75)) if isinstance(kc, dict) else 0.75

        rain_eff = max(0.0, weather.precip_mm * (1.0 - runoff_coef))
        # mm -> m3: 1 mm sobre 1 ha = 10 m3
        irr_m3 = a.irrigation_mm * p.area_ha * 10.0
        total_irr_m3 += irr_m3
        irr_infiltrated_mm = a.irrigation_mm * irr_efficiency

        etc_mm = weather.et0_mm * k
        # Estrés hídrico de juego: si suelo bajo, ET real limitada.
        soil_ratio = p.soil_water_mm / max(p.max_storage_mm, 1e-6)
        stress = max(0.3, min(1.0, soil_ratio * 1.5))  # regla de juego explícita
        et_real = min(etc_mm * stress, p.soil_water_mm + rain_eff + irr_infiltrated_mm)

        s = p.soil_water_mm + rain_eff + irr_infiltrated_mm - et_real
        drainage = max(0.0, s - p.max_storage_mm)
        s = min(s, p.max_storage_mm)
        runoff = weather.precip_mm * runoff_coef
        p.soil_water_mm = round(max(0.0, s), 2)

        # Costes de juego
        irr_cost = irr_m3 * float(cost.get("irrigation_eur_per_m3", 0.25) if isinstance(cost, dict) else 0.25)
        day_cost = irr_cost
        if a.prune or a.scout or a.fertilize_abstract:
            day_cost += 20.0  # mano de obra abstracta de juego
        p.cum_costs_eur = round(p.cum_costs_eur + day_cost, 2)

        # Sanidad simplificada de juego (no diagnóstico real)
        if soil_ratio < 0.25:
            p.health_0_1 = round(max(0.2, p.health_0_1 - 0.03), 3)
            events.append({"type": "estres_hidrico", "parcel": p.id, "level": "juego"})
        if a.scout:
            events.append({"type": "vigilancia", "parcel": p.id, "nota": "información general, no diagnóstico"})

        # Cosecha de juego
        harvested = 0.0
        income = 0.0
        if a.harvest and p.pending_fruit_kg > 0:
            harvested = round(p.pending_fruit_kg * 0.5 * p.health_0_1, 1)
            p.pending_fruit_kg = round(p.pending_fruit_kg - harvested, 1)
            p.cum_yield_kg = round(p.cum_yield_kg + harvested, 1)
            unit = float(price.get(p.crop, 1.5) if isinstance(price, dict) else 1.5)
            # Pequeña variación determinista de mercado de juego
            unit *= 1.0 + (rng.random() - 0.5) * 0.1
            income = round(harvested * unit, 2)
            events.append({"type": "cosecha", "parcel": p.id, "kg": harvested, "ingreso_eur": income})
            # Rebrote ficticio siguiente ciclo
            p.pending_fruit_kg = round(p.pending_fruit_kg + 100.0, 1)

        state.cash_eur = round(state.cash_eur - day_cost + income, 2)

    # Depósito: recarga con lluvia efectiva ficticia proporcional + consumo riego
    state.reservoir_m3 = round(max(0.0, min(state.reservoir_max_m3, state.reservoir_m3 - total_irr_m3 + weather.precip_mm * 2.0)), 1)
    if total_irr_m3 > state.reservoir_max_m3:
        events.append({"type": "riego_excesivo", "m3": total_irr_m3})

    indicators = {
        "cash_eur": state.cash_eur,
        "reservoir_m3": state.reservoir_m3,
        "soil_mm": {p.id: p.soil_water_mm for p in state.parcels},
    }
    provenance = {
        "model_version": MODEL_VERSION,
        "parameter_set": pset_version,
        "evidence_level": "juego",
        "weather_kind": weather.kind,
        "weather_station": weather.station_id,
        "calculation_date": state.day,
        "data_date": weather.date,
        "units": {"agua": "mm", "volumen": "m3 (1mm/ha=10m3)", "dinero": "EUR"},
        "limitations": "Valores de juego, no calibrados. Profesional desactivado. Humedad estimada, no medida.",
        "rng_seed": rng_seed,
    }
    # Avanza fecha (sin reloj global: +1 día aritmético simple sobre ISO)
    state.day = weather.date
    return {"state": asdict(state), "events": events, "indicators": indicators, "provenance": provenance}


def step_week(state: SimState, actions: dict[str, ParcelAction], week: list[WeatherDay], parameters: dict, rng_seed: int) -> dict:
    """7 pasos diarios con mismas acciones programadas."""
    out = None
    for i, w in enumerate(week):
        out = step(state, actions, w, parameters, rng_seed + i)
        # rehidrata estado dict->objeto para siguiente día
        s = out["state"]
        state.cash_eur = s["cash_eur"]
        state.reservoir_m3 = s["reservoir_m3"]
        state.day = s["day"]
        for ps, p in zip(s["parcels"], state.parcels):
            for k, v in ps.items():
                setattr(p, k, v)
    assert out is not None
    return out
