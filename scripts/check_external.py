"""Chequeo externos sin exponer secretos. Imprime estados, jamás claves ni URLs con clave."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

for line in Path(".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

print("aemet_configurada=", bool(os.getenv("AEMET_API_KEY")), "longitud=", len(os.getenv("AEMET_API_KEY", "")))
print("deepseek_configurada=", bool(os.getenv("DEEPSEEK_API_KEY")), "longitud=", len(os.getenv("DEEPSEEK_API_KEY", "")))

from services.ingestion.openmeteo import fetch_daily_forecast
om = fetch_daily_forecast(days=2)
print("openmeteo_ok=", "daily" in om, "dias=", len(om.get("daily", {}).get("time", [])))

from services.ingestion.aemet import fetch_json
try:
    r = fetch_json("/prediccion/especifica/municipio/diaria/18140")
    datos = r.get("datos")
    n = len(datos) if isinstance(datos, list) else (1 if datos else 0)
    print("aemet_ok=True", "endpoint=", r.get("endpoint"), "registros=", n)
except Exception as e:
    # Redactado: nunca imprimir la excepción cruda (httpx incluye la URL con api_key).
    print("aemet_error=", type(e).__name__, str(e)[:160].split("api_key")[0])

from services.api.assistant import explain_game_event
try:
    t = explain_game_event("aguacate", "estres_hidrico", "suelo 18mm")
    print("deepseek_ok=True", "texto_longitud=", len(t), "texto=", t[:220])
except Exception as e:
    print("deepseek_error=", type(e).__name__, str(e)[:160])
