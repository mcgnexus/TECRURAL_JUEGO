"""Graba fixture Open-Meteo (2 días) sanitizado para tests."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.ingestion.openmeteo import fetch_daily_forecast
d = fetch_daily_forecast(days=2)
d.pop("_procedencia", None)
Path("data/fixtures/openmeteo_motril_2d.json").write_text(json.dumps(d, ensure_ascii=False, indent=1)[:6000], encoding="utf-8")
print("fixture_ok daily_keys=", sorted(d.get("daily", {}).keys()))
