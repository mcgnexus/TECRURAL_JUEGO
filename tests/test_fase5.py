"""Fase 5: nutrición y sanidad (juego, profesional bloqueado)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.simulator.engine import SimState, ParcelState, ParcelAction, WeatherDay, step

def params():
    base = json.loads((Path(__file__).resolve().parents[1] / "packages/content/default_game_params.json").read_text(encoding="utf-8"))
    base["infra_game"]["breakdown_prob_per_day"] = 0.0
    return base

def st():
    return SimState(cash_eur=5000.0, reservoir_m3=200.0, reservoir_max_m3=500.0,
                    parcels=[ParcelState(id="P1", crop="aguacate", area_ha=1.0, soil_water_mm=45.0)])

def test_fertilizante_registra_n_y_coste_con_aviso():
    p = params()
    s = st()
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    out = step(s, {"P1": ParcelAction(fertilizer_id="NPK15_juego", fertilizer_kg=10.0)}, w, p, rng_seed=1)
    assert abs(s.parcels[0].cum_n_kg - 1.5) < 1e-9
    ev = next(e for e in out["events"] if e["type"] == "fertilizacion")
    assert "NO es diagnóstico" in ev["nota"] or "sin análisis" in ev["nota"]

def test_fertilizante_desconocido_rechaza():
    p = params()
    s = st()
    w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
    try:
        step(s, {"P1": ParcelAction(fertilizer_id="inventado", fertilizer_kg=5.0)}, w, p, rng_seed=1)
        raise AssertionError("debió rechazar")
    except ValueError as e:
        assert "desconocido" in str(e)

def test_raif_no_infiere_tratamiento():
    from services.ingestion import raif as R
    from services.ingestion.provider import FuenteNoDisponible
    a = R.aviso("aguacate", "Costa Tropical (aprox.)", "2026-01-02")
    assert a["nivel"].startswith("aviso regional")
    assert "diagnóstico" in a["nivel"].lower() or "diagnóstico" in a["nota"].lower()
    assert "MAPA" in a["nota"]
    try:
        R.observacion()
        raise AssertionError("debió fallar")
    except FuenteNoDisponible:
        pass

def test_inspeccion_probabilistica_determinista_y_no_diagnostica():
    p = params()
    def run(seed):
        s = st()
        w = WeatherDay(date="2026-01-02", precip_mm=0.0, et0_mm=3.0, kind="simulado")
        return step(s, {"P1": ParcelAction(scout=True)}, w, p, rng_seed=seed)
    o1, o2 = run(11), run(11)
    assert o1["events"] == o2["events"]  # determinista
    assert any(e["type"] == "vigilancia" for e in o1["events"])
    for e in o1["events"]:
        if e["type"] == "observacion_plaga":
            assert "no" in e["nota"].lower() or "≠" in e["nota"] or "juego" in e["nota"].lower()

def test_api_analyses_y_tratamiento_bloqueado():
    from fastapi.testclient import TestClient
    from services.api.main import app
    c = TestClient(app)
    gid = c.post("/games", json={}).json()["game_id"]
    r = c.post(f"/games/{gid}/analyses", json={"parcel_id": "P1", "date": "2026-01-02", "ph": 6.5})
    assert r.status_code == 200
    assert len(c.get(f"/games/{gid}/analyses").json()["analyses"]) == 1
    r = c.post("/treatments", json={"parcel_id": "P1", "producto_id": "bacillus_juego", "cultivo": "mango"})
    assert r.status_code in (403, 422)  # uso sin confirmar o profesional desactivado
    r = c.get("/raif/aviso", params={"cultivo": "mango"})
    assert "diagnóstico" in r.text or "diagnostico" in r.text.lower() or "diagnóstico" in r.json()["nota"]
