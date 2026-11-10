"""Repetición exacta desde instantánea + acciones + versiones + semilla (prioridad 2)."""
from __future__ import annotations
import copy


def replay_from_snapshot(snapshot: dict, initial_state, parameters: dict, seed: int) -> dict:
    """Re-ejecuta los días guardados en la instantánea con las acciones y semilla
    originales. Devuelve el `out` del último paso para comparar eventos,
    indicadores, estado, ledger y previsión."""
    from packages.simulator.engine import step, step_week, WeatherDay, ParcelAction
    dias = snapshot.get("dias_usados") or snapshot.get("serie", {}).get("points", [])
    acciones = snapshot.get("acciones", [])
    acts = {}
    for a in acciones:
        acts[a["parcel_id"]] = ParcelAction(
            irrigation_mm=a.get("irrigation_mm", 0.0), harvest=a.get("harvest", False),
            prune=a.get("prune", False), scout=a.get("scout", False),
            fertilize_abstract=a.get("fertilize_abstract", False),
            sell_kg=a.get("sell_kg"), channel=a.get("channel", "base"),
            fertilizer_id=a.get("fertilizer_id"), fertilizer_kg=a.get("fertilizer_kg", 0.0),
            spray_id=a.get("spray_id"))
    week = [WeatherDay(date=d["date"], precip_mm=d["precip_mm"], et0_mm=d["et0_mm"],
                       tmin_c=d.get("tmin_c") or 15.0, tmax_c=d.get("tmax_c") or 25.0,
                       kind=d.get("kind") or "pronostico",
                       station_id=d.get("station") or snapshot.get("serie", {}).get("station_id", ""))
            for d in dias]
    st = copy.deepcopy(initial_state)
    if len(week) == 1:
        return step(st, acts, week[0], parameters, rng_seed=seed)
    return step_week(st, acts, week, parameters, rng_seed=seed)


def comparar_ejecuciones(a: dict, b: dict) -> dict:
    """Compara eventos, indicadores, estado, ledger y previsión."""
    difs = []
    if a.get("events") != b.get("events"):
        difs.append("events")
    if a.get("indicators") != b.get("indicators"):
        difs.append("indicators")
    if a.get("state") != b.get("state"):
        difs.append("state")
    if a.get("water_ledger") != b.get("water_ledger"):
        difs.append("water_ledger")
    if a.get("forecast") != b.get("forecast"):
        difs.append("forecast")
    return {"identicas": not difs, "diferencias": difs}
