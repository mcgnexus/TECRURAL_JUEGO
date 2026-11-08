from packages.simulator.engine import SimState, ParcelState, ParcelAction, WeatherDay, step, step_week
import json


def make_state():
    with open("packages/content/default_game_params.json", encoding="utf-8") as f:
        params = json.load(f)
    parcels = [
        ParcelState(id=d["id"], crop=d["crop"], area_ha=d["area_ha"], soil_water_mm=d["soil_water_mm"])
        for d in params["default_farm"]["parcels"]
    ]
    st = SimState(cash_eur=params["default_farm"]["cash_eur"], reservoir_m3=params["default_farm"]["reservoir_m3"], parcels=parcels)
    return st, params


def test_balance_limits():
    st, params = make_state()
    w = WeatherDay(date="2026-01-02", precip_mm=10.0, et0_mm=4.0, kind="simulado")
    out = step(st, {"P1": ParcelAction(irrigation_mm=5.0)}, w, params, rng_seed=1)
    for v in out["indicators"]["soil_mm"].values():
        assert 0.0 <= v <= 80.0
    assert out["provenance"]["evidence_level"] == "juego"


def test_determinism():
    def run():
        st, params = make_state()
        w = WeatherDay(date="2026-01-02", precip_mm=5.0, et0_mm=3.0, kind="simulado")
        return step(st, {}, w, params, rng_seed=42)
    assert run()["indicators"] == run()["indicators"]


def test_rejects_bad_units():
    st, params = make_state()
    w = WeatherDay(date="2026-01-02", precip_mm=-3.0, et0_mm=3.0, kind="simulado")
    try:
        step(st, {}, w, params, rng_seed=1)
    except ValueError:
        return
    raise AssertionError("debió rechazar precipitación negativa")


def test_week_equals_7_days():
    st1, params = make_state()
    import copy
    st2 = copy.deepcopy(st1)
    days = [WeatherDay(date=f"2026-01-0{d}", precip_mm=2.0, et0_mm=3.0, kind="simulado") for d in range(2, 9)]
    acts = {"P1": ParcelAction(irrigation_mm=2.0)}
    out_w = step_week(st1, acts, days, params, rng_seed=7)
    for w in days:
        step(st2, acts, w, params, rng_seed=7 + days.index(w))
    assert abs(out_w["indicators"]["cash_eur"] - st2.cash_eur) < 0.01
