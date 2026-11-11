"""Fase 7 marco general: métricas, fugas, umbrales pendientes, profesional desactivado."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.validation import (mae, rmse, sesgo, cobertura_intervalos,
    sensibilidad_especificidad, comparar_con_base, separar_calibracion_prueba,
    comprobar_fuga, informe_reproducible)

def test_metricas_correctas_y_base():
    obs, pred, base = [10.0, 20.0, 30.0], [12.0, 18.0, 33.0], [15.0, 15.0, 15.0]
    assert abs(mae(obs, pred) - 7 / 3) < 1e-9 and rmse(obs, pred) > 0
    assert abs(sesgo(obs, pred) - (2 - 2 + 3) / 3) < 1e-9
    assert cobertura_intervalos(obs, [9, 19, 29], [13, 21, 34]) == 1.0
    assert comparar_con_base(obs, pred, base)["mejora_mae"] > 0
    assert sensibilidad_especificidad([1, 0, 1, 0], [1, 0, 0, 0])["sensibilidad"] == 0.5

def test_separacion_sin_fuga_y_deteccion():
    filas = [
        {"finca_id": "A", "campaña": "2025", "fecha": "2026-01-01"},
        {"finca_id": "A", "campaña": "2025", "fecha": "2026-01-02"},
        {"finca_id": "B", "campaña": "2026", "fecha": "2026-09-01"},
    ]
    cal, pru = separar_calibracion_prueba(filas, {"B"}, {"2026"})
    f = comprobar_fuga(cal, pru)
    assert f["ok"] and f["n_cal"] == 2 and f["n_pru"] == 1
    # Solape y fuga temporal detectados
    f2 = comprobar_fuga(filas[:2], filas[1:])
    assert not f2["ok"] and (f2["solape_pares"] or f2["fuga_temporal"])

def test_umbrales_pendientes_bloquean_e_informe_reproducible():
    import json
    umb = json.loads((Path(__file__).resolve().parents[1] / "packages/content/umbrales.json").read_text(encoding="utf-8"))["umbrales"]
    assert all(v.get("valor") is None for v in umb.values())  # no inventar precisiones
    inf = informe_reproducible("t", [{"x": 1}], {"mae": 1.0}, {"ok": True, "solape_pares": [], "fuga_temporal": False},
                               "sim-test", "game-test", umb)
    assert inf["aprobable"] is False and inf["profesional"] == "desactivado"
    assert "gemelo digital" in inf["nota"]

def test_api_profesional_desactivado_y_prospectivo():
    from fastapi.testclient import TestClient
    from services.api.main import app
    c = TestClient(app)
    assert c.get("/professional/status").json()["activo"] is False
    assert "pendientes" in c.get("/validation/protocolo").json()["nota"]
    c.post("/accounts/register", json={"email": "fase7-2@ejemplo.es", "password": "Secreta01"})
    tok = c.post("/accounts/login", json={"email": "fase7-2@ejemplo.es", "password": "Secreta01"}).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    inf = c.post("/validation/run", headers=h).json()
    assert inf["profesional"] == "desactivado" and inf["aprobable"] is False
    r = c.post("/approvals", json={"funcion": "riego", "cultivo": "aguacate", "ambito": "costa",
        "codigo_version": "sim-0.3.0", "params_version": "game-0.3", "caducidad": "2020-01-01",
        "responsable_agronomico": "a", "responsable_producto": "p"}, headers=h)
    assert r.status_code == 422  # caducidad pasada bloquea
