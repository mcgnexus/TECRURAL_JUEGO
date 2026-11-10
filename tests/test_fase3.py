"""Fase 3: agua, riego e infraestructura. Sin red en vivo."""
import sys, json, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.simulator.engine import (SimState, ParcelState, ParcelAction, WeatherDay,
    step, step_week, mm_to_m3, MASS_TOL_MM, MASS_TOL_M3)

def params(**infra_over):
    base = json.loads((Path(__file__).resolve().parents[1] / "packages/content/default_game_params.json").read_text(encoding="utf-8"))
    base["infra_game"]["breakdown_prob_per_day"] = 0.0  # determinista salvo test avería
    for k, v in infra_over.items():
        base["infra_game"][k] = v
    return base

def state(area=1.0, soil=45.0, res=200.0, cash=5000.0):
    return SimState(cash_eur=cash, reservoir_m3=res, reservoir_max_m3=500.0,
                    parcels=[ParcelState(id="P1", crop="aguacate", area_ha=area, soil_water_mm=soil)])

def test_unidades_mm_m3_y_superficie():
    assert mm_to_m3(1.0, 1.0) == 10.0 and mm_to_m3(2.0, 0.5) == 10.0
    p = params()
    s1 = state(area=1.0); s2 = state(area=2.0)
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    o1 = step(s1, {"P1": ParcelAction(irrigation_mm=2.0)}, w, p, rng_seed=1)
    o2 = step(s2, {"P1": ParcelAction(irrigation_mm=2.0)}, w, copy.deepcopy(p), rng_seed=1)
    assert abs(o2["indicators"]["pumped_m3"] - 2 * o1["indicators"]["pumped_m3"]) < 0.05

def test_lluvia_cero_no_crea_agua():
    p = params()
    st = state()
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=4.0, kind="simulado")
    before = st.reservoir_m3
    out = step(st, {}, w, p, rng_seed=5)
    # depósito solo sube por aporte configurado (8), nunca por lluvia ficticia
    assert out["indicators"]["reservoir_m3"] <= before + 8.0 + 0.01
    assert out["indicators"]["soil_mm"]["P1"] < 45.0  # ET consume

def test_deposito_vacio_rechaza():
    p = params()
    st = state(res=5.0)
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    try:
        step(st, {"P1": ParcelAction(irrigation_mm=10.0)}, w, p, rng_seed=1)  # 100 m3 > 13 disp
        raise AssertionError("debió rechazar")
    except ValueError as e:
        assert "agua insuficiente" in str(e)

def test_exceso_lluvia_capa_y_drenaje():
    p = params()
    st = state(soil=79.0)
    w = WeatherDay(date="2026-01-02", precip_mm=60.0, et0_mm=2.0, kind="simulado")
    out = step(st, {}, w, p, rng_seed=1)
    assert out["indicators"]["soil_mm"]["P1"] <= 80.0 + 1e-9
    tipos = [e["tipo"] for e in out["water_ledger"]]
    assert "drenaje" in tipos and "escorrentia" in tipos

def test_riego_superior_disponible_rechaza():
    p = params()
    st = state(res=200.0)
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    try:
        step(st, {"P1": ParcelAction(irrigation_mm=100.0)}, w, p, rng_seed=1)
        raise AssertionError("debió rechazar")
    except ValueError as e:
        assert "agua insuficiente" in str(e)

def test_bombeo_limitado_prorratea_y_evento():
    p = params(pump_capacity_m3_day=10.0, supply_max_m3_day=10.0)
    st = state()
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    out = step(st, {"P1": ParcelAction(irrigation_mm=4.0)}, w, p, rng_seed=1)  # pide 40, cap 10
    assert abs(out["indicators"]["pumped_m3"] - 10.0) < 0.05
    assert any(e["type"] in ("bombeo_limitado", "suministro_limitado") for e in out["events"])

def test_suministro_limitado_evento():
    p = params(pump_capacity_m3_day=100.0, supply_max_m3_day=5.0)
    st = state()
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    out = step(st, {"P1": ParcelAction(irrigation_mm=4.0)}, w, p, rng_seed=1)
    assert abs(out["indicators"]["pumped_m3"] - 5.0) < 0.05
    assert any(e["type"] == "suministro_limitado" for e in out["events"])

def test_averia_detiene_bombeo():
    p = params()
    p["infra_game"]["breakdown_prob_per_day"] = 1.0  # avería segura
    st = state()
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    out = step(st, {"P1": ParcelAction(irrigation_mm=4.0)}, w, p, rng_seed=7)
    assert out["indicators"]["pumped_m3"] == 0.0
    assert any(e["type"] == "averia" for e in out["events"])
    # determinista: misma semilla+fecha, mismo resultado
    st2 = state()
    out2 = step(st2, {"P1": ParcelAction(irrigation_mm=4.0)}, w, p, rng_seed=7)
    assert out2["indicators"] == out["indicators"]

def test_costes_agua_y_energia_y_ledger():
    p = params()
    st = state()
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    cash0 = st.cash_eur
    out = step(st, {"P1": ParcelAction(irrigation_mm=4.0)}, w, p, rng_seed=1)
    pumped = out["indicators"]["pumped_m3"]  # 40
    exp = pumped * 0.25 + pumped * 0.4 * 0.25
    assert abs((cash0 - out["indicators"]["cash_eur"]) - exp) < 0.05
    tipos = {e["tipo"] for e in out["water_ledger"]}
    assert {"aporte", "bombeo", "perdidas_red", "infiltrado", "ET_real"} <= tipos
    assert out["mass_balance"]["ok"] and MASS_TOL_M3 == 1e-9 and MASS_TOL_MM == 1e-9

def test_desborde_sobre_capacidad():
    p = params(supply_inflow_m3_day=50.0)
    st = state(res=490.0)
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=1.0, kind="simulado")
    out = step(st, {}, w, p, rng_seed=1)
    assert out["indicators"]["overflow_m3"] > 0
    assert out["indicators"]["reservoir_m3"] <= 500.0 + 1e-9

def test_semana_equivale_dias_con_infra():
    p = params()
    import copy as cp
    s1 = state(); s2 = cp.deepcopy(s1)
    days = [WeatherDay(date=f"2026-01-0{d}", precip_mm=1.0, et0_mm=3.0, kind="simulado") for d in range(2, 9)]
    acts = {"P1": ParcelAction(irrigation_mm=1.0)}
    ow = step_week(s1, acts, days, p, rng_seed=11)
    for i, w in enumerate(days):
        step(s2, acts, w, p, rng_seed=11 + i)
    assert abs(ow["indicators"]["cash_eur"] - s2.cash_eur) < 0.05
    assert abs(ow["indicators"]["reservoir_m3"] - s2.reservoir_m3) < 0.05
