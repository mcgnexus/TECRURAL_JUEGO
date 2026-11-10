"""Carga Fase 8: 50 avances miden tiempo; sin umbral inventado, informa."""
import time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.simulator.engine import SimState, ParcelState, ParcelAction, WeatherDay, step
import json
p = json.loads(Path("packages/content/default_game_params.json").read_text(encoding="utf-8"))
p["infra_game"]["breakdown_prob_per_day"] = 0.0
st = SimState(cash_eur=5000.0, reservoir_m3=200.0, reservoir_max_m3=500.0,
              parcels=[ParcelState(id="P1", crop="aguacate", area_ha=1.0, soil_water_mm=45.0)])
t0 = time.perf_counter()
for i in range(50):
    w = WeatherDay(date=f"2026-01-{i+2:02d}" if i < 29 else f"2026-02-{(i-29)+1:02d}",
                   precip_mm=2.0, et0_mm=3.5, kind="simulado")
    step(st, {"P1": ParcelAction(irrigation_mm=0.5)}, w, p, rng_seed=i)
ms = (time.perf_counter() - t0) * 1000 / 50
print(f"media_ms_por_avance={ms:.2f} n=50")
