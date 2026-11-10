"""Fase 4: cultivos, producción y economía (juego, profesional desactivado)."""
import sys, json, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.simulator.engine import (SimState, ParcelState, ParcelAction, WeatherDay,
    step, step_week, forecast_interval, phenology_stage, age_factor)

def params():
    base = json.loads((Path(__file__).resolve().parents[1] / "packages/content/default_game_params.json").read_text(encoding="utf-8"))
    base["infra_game"]["breakdown_prob_per_day"] = 0.0
    return base

def st(**kw):
    d = dict(crop="aguacate", area_ha=1.0, soil_water_mm=45.0, pending_fruit_kg=500.0)
    d.update(kw)
    return SimState(cash_eur=5000.0, reservoir_m3=200.0, reservoir_max_m3=500.0,
                    parcels=[ParcelState(id="P1", planting_year=2018, **d)])

def test_fenologia_y_edad_juego():
    assert phenology_stage("aguacate", "2026-04-10") == "floracion"
    assert phenology_stage("mango", "2026-09-01") == "cosecha"
    assert age_factor(2024, "2026-01-02") == 0.5 and age_factor(2018, "2026-01-02") == 1.0
    assert age_factor(1990, "2026-01-02") == 0.7

def test_cosecha_a_inventario_y_autoventa_compatible():
    p = params()
    s = st()
    w = WeatherDay(date="2026-09-10", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    out = step(s, {"P1": ParcelAction(harvest=True)}, w, p, rng_seed=3)
    assert any(e["type"] == "cosecha" for e in out["events"])
    assert any(e["type"] == "venta" for e in out["events"])  # auto-venta compat.
    assert s.cash_eur > 5000.0 - 50  # ingreso menos costes

def test_venta_explicita_sin_existencias_no_negativa():
    p = params()
    s = st()
    s.parcels[0].inventory_kg = 10.0
    s.parcels[0].pending_fruit_kg = 0.0
    w = WeatherDay(date="2026-09-10", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    out = step(s, {"P1": ParcelAction(sell_kg=100.0, channel="mercado")}, w, p, rng_seed=3)
    assert s.parcels[0].inventory_kg >= 0
    assert any(e["type"] == "venta_parcial" for e in out["events"])

def test_coherencia_arboles_recorta():
    p = params()
    s = st(area_ha=0.1, pending_fruit_kg=999999.0)  # 0.1ha*400*120=4800 max
    s.parcels[0].density_trees_ha = 400.0
    w = WeatherDay(date="2026-09-10", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    out = step(s, {}, w, p, rng_seed=1)
    assert s.parcels[0].pending_fruit_kg <= 4800.0 + 1e-9
    assert any(e["type"] == "coherencia_limitada" for e in out["events"])

def test_forecast_intervalos_y_canales():
    p = params()
    s = st()
    f = forecast_interval(s.parcels[0], p, "2026-09-10")
    assert f["low_kg"] <= f["mid_kg"] <= f["high_kg"] and f["evidence_level"] == "juego"
    w = WeatherDay(date="2026-09-10", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    s1 = st(); s2 = st()
    o1 = step(s1, {"P1": ParcelAction(harvest=True, channel="cooperativa")}, w, copy.deepcopy(p), rng_seed=9)
    o2 = step(s2, {"P1": ParcelAction(harvest=True, channel="mercado")}, w, copy.deepcopy(p), rng_seed=9)
    v1 = next(e for e in o1["events"] if e["type"] == "venta")["ingreso_eur"]
    v2 = next(e for e in o2["events"] if e["type"] == "venta")["ingreso_eur"]
    assert v2 > v1  # mercado 1.1 > cooperativa 0.95

def test_conciliacion_caja_e_inventario():
    p = params()
    s = st()
    w = WeatherDay(date="2026-09-10", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    cash0 = s.cash_eur
    out = step(s, {"P1": ParcelAction(harvest=True, sell_kg=0.0)}, w, p, rng_seed=4)
    assert abs(out["mass_balance"]["conciliacion_caja"]) <= 0.05
    assert out["indicators"]["inventory_kg"]["P1"] >= 0

def test_api_forecast_y_precios_y_deuda_bloqueo_tratamiento():
    from fastapi.testclient import TestClient
    from services.api.main import app
    c = TestClient(app)
    gid = c.post("/games", json={}).json()["game_id"]
    assert c.get(f"/games/{gid}/forecast").json()["forecast"]["P1"]["evidence_level"] == "juego"
    assert len(c.get("/prices/historic").json()["precios"]) >= 7
    d = c.post(f"/games/{gid}/debt", json={"amount_eur": 100.0}).json()
    assert d["debt_eur"] == 100.0
    r = c.post("/treatments", json={"parcel_id": "P1", "producto_id": "aceite_parafinico_juego", "cultivo": "aguacate"})
    assert r.status_code == 422  # ficha caducada bloquea
    r = c.post(f"/games/{gid}/advance", json={"actions": [{"parcel_id": "P1", "spray_id": "x_juego"}]})
    assert r.status_code == 200
    assert any(e["type"] == "tratamiento_bloqueado" for e in r.json()["events"])
