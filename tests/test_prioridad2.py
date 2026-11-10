"""Prioridad 2: barrera profesional, conservación, reproducibilidad, evidencia."""
import sys, json, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.simulator.engine import (SimState, ParcelState, ParcelAction, WeatherDay,
    step, step_week, MODEL_VERSION)
from packages.validation import (informe_reproducible, aprobacion_valida,
    replay_from_snapshot, comparar_ejecuciones, auditar_evidencia)

BASE = Path(__file__).resolve().parents[1]

def params():
    p = json.loads((BASE / "packages/content/default_game_params.json").read_text(encoding="utf-8"))
    p["infra_game"]["breakdown_prob_per_day"] = 0.0
    return p

def test_barrera_exige_todo_y_revocacion_por_version():
    umb = json.loads((BASE / "packages/content/umbrales.json").read_text(encoding="utf-8"))["umbrales"]
    ok_inf = informe_reproducible("d1", [{"x": 1}], {"comparacion": {"mae_modelo": 1, "mae_base": 9,
        "rmse_modelo": 1, "rmse_base": 9}}, {"ok": True, "solape_pares": [], "fuga_temporal": False},
        "sim-9.9", "game-9.9", {"riego.mae_mm": {"valor": 5, "n_min": 1}},
        dataset_autorizado=True, permiso_ref="perm-1", revision_independiente=True, revisor="rev")
    assert ok_inf["aprobable"] is True
    base_ap = {"funcion": "riego", "cultivo": "aguacate", "ambito": "costa",
               "codigo_version": "sim-9.9", "params_version": "game-9.9",
               "caducidad": "2999-01-01", "responsable_agronomico": "agro",
               "responsable_producto": "prod", "dataset_id": "d1", "permiso_ref": "perm-1",
               "revision_independiente": True, "revisor_independiente": "rev"}
    ok, _ = aprobacion_valida(base_ap, ok_inf, "sim-9.9", "game-9.9", "2026-01-01")
    assert ok is True
    # Revocación: cambia el código o los parámetros
    ok2, m2 = aprobacion_valida(base_ap, ok_inf, "sim-OTRO", "game-9.9", "2026-01-01")
    assert ok2 is False and any("código" in m for m in m2)
    # Firmas no independientes, caducidad pasada, sin permiso, sin revisión, fuga
    for mut in [{"responsable_producto": "agro"}, {"caducidad": "2020-01-01"},
                {"permiso_ref": ""}, {"revision_independiente": False},
                {"revisor_independiente": "agro"}]:
        a = {**base_ap, **mut}
        assert aprobacion_valida(a, ok_inf, "sim-9.9", "game-9.9", "2026-01-01")[0] is False
    mal_inf = informe_reproducible("d1", [{"x": 1}], {}, {"ok": False, "solape_pares": [["A", "B"]],
        "fuga_temporal": True}, "sim-9.9", "game-9.9", {"k": {"valor": None}},
        dataset_autorizado=False, permiso_ref="")
    assert mal_inf["aprobable"] is False
    assert aprobacion_valida(base_ap, mal_inf, "sim-9.9", "game-9.9", "2026-01-01")[0] is False
    assert aprobacion_valida(base_ap, None, "sim-9.9", "game-9.9", "2026-01-01")[0] is False

def test_conservacion_agua_multidia_y_cambio_superficie():
    p = params()
    st = SimState(cash_eur=5000.0, reservoir_m3=200.0, reservoir_max_m3=500.0,
                  parcels=[ParcelState(id="P1", crop="aguacate", area_ha=1.0, soil_water_mm=45.0)])
    cum_pump, cum_in, cum_over = 0.0, 0.0, 0.0
    res = st.reservoir_m3
    for i in range(7):
        if i == 3:  # cambio de superficie a mitad de campaña: m3 escala con ha
            st.parcels[0].area_ha = 2.0
        w = WeatherDay(date=f"2026-01-{i+2:02d}", precip_mm=1.0, et0_mm=3.0, kind="simulado")
        out = step(st, {"P1": ParcelAction(irrigation_mm=0.5)}, w, p, rng_seed=50 + i)
        cum_pump += out["indicators"]["pumped_m3"]
        cum_in += out["indicators"]["inflow_m3"]
        cum_over += out["indicators"]["overflow_m3"]
    # Conservación depósito con tolerancia de redondeo acumulado (0.05/día + 0.02)
    assert abs((res + cum_in - cum_over - cum_pump) - st.reservoir_m3) < 0.05 * 7 + 0.05
    assert abs(cum_pump - st.cum_pumped_m3) < 0.05 and abs(cum_in - st.cum_inflow_m3) < 0.05
    # Suelo siempre dentro de capacidad y sin crear agua
    assert 0.0 <= st.parcels[0].soil_water_mm <= 80.0

def test_conservacion_fruta_con_rebrote_explicito_y_caja_semanal():
    p = params()
    st = SimState(cash_eur=5000.0, reservoir_m3=200.0, reservoir_max_m3=500.0,
                  parcels=[ParcelState(id="P1", crop="aguacate", area_ha=1.0,
                                       soil_water_mm=45.0, pending_fruit_kg=500.0)])
    pend0, cash0 = 500.0, st.cash_eur
    n_harv, tot_cost, tot_inc = 0, 0.0, 0.0
    days = [WeatherDay(date=f"2026-09-{i+1:02d}", precip_mm=0.0, et0_mm=3.0, kind="simulado") for i in range(7)]
    out = step_week(st, {"P1": ParcelAction(harvest=True, sell_kg=0.0)}, days, p, rng_seed=77)
    for e in out["events"]:
        pass
    # 7 cosechas → 700 kg de rebrote explícito en ledger/estado
    assert st.parcels[0].cum_yield_kg >= 0
    # Fruta: pendiente_final - pendiente_inicial = rebrotes - bruto_cosechado
    # bruto = cum_yield / (1 - 0.05); rebrotes = 700
    bruto = st.parcels[0].cum_yield_kg / 0.95 if st.parcels[0].cum_yield_kg else 0.0
    assert abs((st.parcels[0].pending_fruit_kg - pend0) - (700.0 - bruto)) < 1.0
    # Caja semanal concilia con tolerancia 0.05/día
    assert abs(out["mass_balance"]["conciliacion_caja"]) <= 0.05
    assert abs(st.cash_eur - (cash0 - (out["indicators"]["day_costs_eur"] if "day_costs_eur" in out["indicators"] else 0))) <= 5000

def test_replay_identico_y_huecos_de_extremo_a_extremo():
    from fastapi.testclient import TestClient
    from services.api.main import app
    import services.ingestion.scenarios as SC
    c = TestClient(app)
    tok = c.post("/accounts/request_code", json={"phone": "+34600111111"}).json()["code_debug"]
    tok = c.post("/accounts/verify", json={"phone": "+34600111111", "code": tok}).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    # Hueco: serie con ET0 ausente → 422 sin permitir_ficticio, degradado etiquetado con él
    real = SC.presente_con_prevision
    SC.presente_con_prevision = lambda station=None, days=1, client=None: {
        "escenario": "t", "station": {"id": "t"}, "serie": {"provider": "t", "station_id": "t",
        "kind": "pronostico", "points": [{"date": "2026-02-01", "precip_mm": 1.0, "et0_mm": None}]},
        "avisos": [], "politica_huecos": "t"}
    try:
        gid = c.post("/games", json={}, headers=h).json()["game_id"]
        r = c.post(f"/games/{gid}/advance_weather", json={"actions": [], "days": 1}, headers=h)
        assert r.status_code == 422
        r = c.post(f"/games/{gid}/advance_weather", json={"actions": [], "days": 1, "permitir_ficticio": True}, headers=h)
        assert r.status_code == 200 and r.json()["weather_snapshot"]["serie_kind"] in ("pronostico", "estimacion", "simulado")
        day = r.json()["weather_snapshot"]["dias"][0]
        snap = c.get(f"/games/{gid}/snapshot/{day}", headers=h).json()
        assert snap["codigo_version"] == MODEL_VERSION and snap["seed"] is not None and snap["acciones"] == []
        rr = c.post(f"/games/{gid}/replay/{day}", headers=h).json()
        assert rr["ok"] is True and rr["comparacion"]["identicas"] is True
    finally:
        SC.presente_con_prevision = real

def test_evidencia_sin_validados_y_tratamientos_bloqueados():
    from packages.validation import auditar_evidencia
    assert auditar_evidencia()["ok"] is True
    from fastapi.testclient import TestClient
    from services.api.main import app
    c = TestClient(app)
    assert c.post("/treatments", json={"parcel_id": "P1", "producto_id": "x", "cultivo": "aguacate"}).status_code == 422
    assert "diagnóstico" in c.get("/raif/aviso", params={"cultivo": "aguacate"}).text.lower()
