"""Graba serie histórica cerrada desde el pasado modelizado (etiquetada como tal)."""
import sys, csv, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.ingestion import openmeteo as OM
from services.ingestion.stations import get_station
st = get_station(None)
res = OM.past(st, past_days=14)
print("puntos=", len(res.points), "gaps=", res.gaps, "obsoleta=", res.obsolete)
out = Path("data/fixtures/historico_cerrado.csv")
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date", "precip_mm", "et0_mm", "tmin_c", "tmax_c", "kind", "station_id"])
    w.writeheader()
    for p in res.points:
        w.writerow({"date": p.date, "precip_mm": p.precip_mm if p.precip_mm is not None else "",
                    "et0_mm": p.et0_mm if p.et0_mm is not None else "",
                    "tmin_c": p.tmin_c if p.tmin_c is not None else "",
                    "tmax_c": p.tmax_c if p.tmax_c is not None else "",
                    "kind": "estimacion", "station_id": p.station_id})
Path("data/fixtures/historico_cerrado.README.txt").write_text(
    "historico_cerrado.csv: pasada modelizada Open-Meteo (past) grabada como serie cerrada reproducible.\n"
    "kind=estimacion (modelo, NO observación). Estación: motril-18140. Ver scenarios.historico_cerrado.\n",
    encoding="utf-8")
print("csv_ok")
