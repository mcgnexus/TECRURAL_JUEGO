"""Fase 1: partida, edición, campaña, reinicio, equivalencia semanal, consistencia."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from services.api.main import app

c = TestClient(app)


def new_gid():
    return c.post("/games", json={}).json()["game_id"]


def test_nueva_editar_reiniciar():
    gid = new_gid()
    r = c.put(f"/games/{gid}", json={"parcels": {"P1": {"area_ha": 2.5}}})
    assert r.status_code == 200
    assert next(p for p in r.json()["parcels"] if p["id"] == "P1")["area_ha"] == 2.5
    r = c.put(f"/games/{gid}", json={"parcels": {"P1": {"area_ha": 99}}})
    assert r.status_code == 422  # restricción de interfaz 0.1-10 ha
    r = c.post(f"/games/{gid}/advance", json={"actions": [{"parcel_id": "P1", "irrigation_mm": 4}]})
    assert r.status_code == 200
    r = c.post(f"/games/{gid}/restart")
    assert r.status_code == 200
    assert r.json()["cash_eur"] == 5000.0


def test_misma_semilla_mismos_resultados():
    a, b = new_gid(), new_gid()
    body = {"actions": [{"parcel_id": "P1", "irrigation_mm": 3, "scout": True}]}
    r1 = c.post(f"/games/{a}/advance", json=body).json()
    r2 = c.post(f"/games/{b}/advance", json=body).json()
    assert r1["indicators"] == r2["indicators"]  # misma semilla inicial 1234


def test_semana_equivale_7_dias():
    g1, g2 = new_gid(), new_gid()
    body = {"actions": [{"parcel_id": "P1", "irrigation_mm": 2}]}
    w = c.post(f"/games/{g1}/advance_week", json=body).json()
    for _ in range(7):
        d = c.post(f"/games/{g2}/advance", json=body).json()
    g2state = c.get(f"/games/{g2}").json()
    assert abs(w["indicators"]["cash_eur"] - g2state["cash_eur"]) < 0.05
    assert w["indicators"]["soil_mm"] == {p["id"]: p["soil_water_mm"] for p in g2state["parcels"]}


def test_rechaza_riego_sin_agua_y_sin_negativos():
    gid = new_gid()
    r = c.post(f"/games/{gid}/advance", json={"actions": [{"parcel_id": "P1", "irrigation_mm": 100}]})
    assert r.status_code == 422  # 100mm×1ha=1000m³ > depósito 200
    for _ in range(5):
        r = c.post(f"/games/{gid}/advance", json={"actions": [{"parcel_id": "P2", "irrigation_mm": 1}]})
        assert r.status_code == 200
        assert r.json()["indicators"]["cash_eur"] >= 0
        assert r.json()["indicators"]["reservoir_m3"] >= 0
        for v in r.json()["indicators"]["soil_mm"].values():
            assert v >= 0


def test_historial_explica():
    gid = new_gid()
    c.post(f"/games/{gid}/advance", json={"actions": [{"parcel_id": "P1", "irrigation_mm": 4, "scout": True}]})
    h = c.get(f"/games/{gid}/history").json()
    assert len(h["history"]) >= 1
    tipos = {e["type"] for e in h["history"][-1]["events"]}
    assert "riego" in tipos and "labor" in tipos
