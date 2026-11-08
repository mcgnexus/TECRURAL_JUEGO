"""Smoke Fase 2 contra Neon + red real (AEMET con reserva OM)."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for line in Path(".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
from fastapi.testclient import TestClient
from services.api.main import app
c = TestClient(app)
print("stations=", c.get("/weather/stations").json()["por_defecto"])
print("historic=", c.get("/weather/scenario/historic").json()["escenario"],
      len(c.get("/weather/scenario/historic").json()["serie"]["points"]), "puntos")
gid = c.post("/games", json={}).json()["game_id"]
r = c.post(f"/games/{gid}/advance_weather", json={"actions": [], "provider": "auto", "days": 1})
print("advance_weather=", r.status_code, r.json().get("weather_snapshot") if r.status_code == 200 else r.text[:200])
print("snapshot=", c.get(f"/games/{gid}/snapshot/{r.json()['weather_snapshot']['dias'][0]}").status_code if r.status_code == 200 else "-")
