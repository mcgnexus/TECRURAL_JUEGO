"""Verificación SiAR en vivo. Imprime estados y conteos, jamás el token ni URLs."""
import os, sys
from pathlib import Path
from datetime import date, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for line in Path(".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from services.ingestion import siar as S
try:
    print("accesos=", S.accesos().get("datos"))
except Exception as e:
    print("accesos_error=", type(e).__name__, str(e)[:120])

try:
    est = S.estaciones()
    print("nestaciones=", len(est))
    gr = [e for e in est if str(e.get("Codigo", "")).startswith("GR")]
    print("granada=", [(e.get("Codigo"), e.get("Estacion") or e.get("Termino")) for e in gr])
except Exception as e:
    print("estaciones_error=", type(e).__name__, str(e)[:120])

try:
    fin = date.today().isoformat()
    ini = (date.today() - timedelta(days=6)).isoformat()
    res = S.observation("GR11", ini, fin)
    print("obs_gr11=", len(res.points), "puntos, gaps=", res.gaps, "obsoleta=", res.obsolete)
    if res.points:
        print("primero=", res.points[0].date, res.points[0].precip_mm, res.points[0].et0_mm)
except Exception as e:
    print("obs_error=", type(e).__name__, str(e)[:160])
