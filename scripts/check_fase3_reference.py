"""Referencia independiente Fase 3: replica ecuaciones sin importar el motor."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.simulator.engine import SimState, ParcelState, ParcelAction, WeatherDay, step

def make(params_override=None):
    params = {"version": "game-0.2", "runoff_coef": 0.15, "irrigation_efficiency": 0.85,
              "kc_game": {"aguacate": 0.8}, "price_eur_kg_game": {"aguacate": 2.2},
              "costs_eur_game": {"irrigation_eur_per_m3": 0.25},
              "infra_game": {"supply_inflow_m3_day": 8.0, "pump_capacity_m3_day": 60.0,
                             "supply_max_m3_day": 50.0, "network_efficiency": 0.92,
                             "energy_kwh_per_m3": 0.4, "energy_eur_per_kwh": 0.25,
                             "breakdown_prob_per_day": 0.0}}
    if params_override: params["infra_game"].update(params_override)
    st = SimState(cash_eur=5000.0, reservoir_m3=200.0, reservoir_max_m3=500.0,
                  parcels=[ParcelState(id="P1", crop="aguacate", area_ha=1.0, soil_water_mm=45.0)])
    return st, params

def ref_day(soil, rain, et0, irr_mm, area=1.0):
    runoff_coef, eff_app, eff_net, kc = 0.15, 0.85, 0.92, 0.8
    rain_eff = rain * (1 - runoff_coef)
    infil = irr_mm * eff_net * eff_app
    etc = et0 * kc
    ratio = soil / 80.0
    stress = max(0.3, min(1.0, ratio * 1.5))
    et = min(etc * stress, soil + rain_eff + infil)
    s = soil + rain_eff + infil - et
    drain = max(0.0, s - 80.0)
    return round(min(s, 80.0), 2), round(et, 3), round(drain, 3)

cases = [
    ("base", dict(), 45.0, 2.0, 3.5, 4.0, 1.0),
    ("lluvia_cero", dict(), 40.0, 0.0, 4.0, 0.0, 1.0),
    ("exceso_lluvia", dict(), 79.0, 60.0, 2.0, 0.0, 1.0),
    ("tope_bombeo", {"pump_capacity_m3_day": 10.0, "supply_max_m3_day": 10.0}, 40.0, 0.0, 3.0, 4.0, 1.0),
    ("superficie_doble", dict(), 40.0, 0.0, 3.0, 2.0, 2.0),
]
ok = True
for name, over, soil0, rain, et0, irr, area in cases:
    st, params = make(over)
    st.parcels[0].soil_water_mm = soil0
    st.parcels[0].area_ha = area
    w = WeatherDay(date="2026-01-02", precip_mm=rain, et0_mm=et0, kind="simulado")
    out = step(st, {"P1": ParcelAction(irrigation_mm=irr)}, w, params, rng_seed=99)
    # referencia: prorrateo por tope
    cap = min(params["infra_game"]["pump_capacity_m3_day"], params["infra_game"]["supply_max_m3_day"])
    req = irr * area * 10.0
    applied = min(req, cap) / (area * 10.0) if req > 0 else 0.0
    exp_soil, exp_et, exp_drain = ref_day(soil0, rain, et0, applied, area)
    got_soil = out["indicators"]["soil_mm"]["P1"]
    # ledger bombeo esperado
    exp_pumped = round(applied * area * 10.0, 2)
    got_pumped = out["indicators"]["pumped_m3"]
    match = abs(got_soil - exp_soil) <= 0.02 and abs(got_pumped - exp_pumped) <= 0.02
    print(f"{name}: suelo got={got_soil} exp={exp_soil} bombeo got={got_pumped} exp={exp_pumped} -> {'OK' if match else 'FALLO'}")
    ok = ok and match
print("REFERENCIA OK" if ok else "REFERENCIA FALLO")
sys.exit(0 if ok else 1)
