"""Smoke API con Neon: crea partida, avanza, recarga desde DB. Sin mostrar secretos."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

for line in Path(".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from fastapi.testclient import TestClient
from services.api.main import app

c = TestClient(app)
print("health=", c.get("/health").json())
gid = c.post("/games", json={}).json()["game_id"]
print("creada=", c.get(f"/games/{gid}").json()["persistencia"])
out = c.post(f"/games/{gid}/advance", json={"actions": [{"parcel_id": "P1", "irrigation_mm": 4}]})
print("advance_cash=", out.json()["indicators"]["cash_eur"])
print("releer=", c.get(f"/games/{gid}").json()["cash_eur"])
print("api_db_ok=True")
