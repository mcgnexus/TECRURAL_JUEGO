"""Fase 2: contratos, caché/TTL, validación, huecos, dobles, zona horaria. Sin red en vivo."""
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.ingestion import provider as P
from services.ingestion import stations as ST
from services.ingestion import validate as V
from services.ingestion import scenarios as SC
from services.ingestion import cache as C

FIX = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_aemet_parser_fixture():
    from services.ingestion import aemet as A
    blob = json.loads((FIX / "aemet_municipio_18140_ejemplo.json").read_text(encoding="utf-8"))
    res = A._parse_municipio_diaria(blob["datos"], "motril-18140")
    assert res.points[0].date == "2026-11-09" and res.points[0].precip_mm == 3.0
    assert all(p.et0_mm is None for p in res.points)  # AEMET municipal no da ET0 -> hueco
    assert res.points[0].tz == "Europe/Madrid" and res.points[0].kind == "pronostico"


def test_openmeteo_parser_fixture():
    from services.ingestion import openmeteo as OM
    data = json.loads((FIX / "openmeteo_motril_2d.json").read_text(encoding="utf-8"))
    res = OM._to_points(data, "motril-18140", "pronostico", "2026-11-08T10:00+01:00")
    assert len(res.points) == 2 and res.points[0].tz == "Europe/Madrid"
    assert all(p.precip_mm is not None and p.et0_mm is not None for p in res.points)


def test_validacion_huecos_duplicados_imposibles():
    pts = [P.SeriesPoint(date="2026-03-01", precip_mm=2.0, et0_mm=3.0, tmin_c=10, tmax_c=20),
           P.SeriesPoint(date="2026-03-01", precip_mm=2.0, et0_mm=3.0, tmin_c=10, tmax_c=20),
           P.SeriesPoint(date="2026-03-02", precip_mm=999.0, et0_mm=3.0),
           P.SeriesPoint(date="2026-03-03", precip_mm=1.0, et0_mm=None),
           P.SeriesPoint(date="2026-03-04", precip_mm=1.0, et0_mm=3.0, tmin_c=25, tmax_c=20)]
    ok, q = V.validate(pts)
    assert q["duplicates_removed"] == 1 and q["dropped_invalid"] == 2
    assert q["gaps"] == ["2026-03-03"]


def test_aemet_401_es_fuente_no_disponible():
    from services.ingestion import aemet as A
    st = {"id": "t-m", "aemet_municipio": "18140", "lat": 36.75, "lon": -3.87}

    def h(request):
        return httpx.Response(401, json={"estado": 401})
    try:
        A.forecast(st, 2, client=mock_client(h))
        raise AssertionError("debió fallar")
    except P.FuenteNoDisponible:
        pass


def test_red_caida_sin_cache_es_fuente_no_disponible():
    from services.ingestion import openmeteo as OM
    st = {"id": "t-caida", "lat": 36.75, "lon": -3.87}

    def h(request):
        raise httpx.ConnectError("red caída")
    try:
        OM.forecast(st, 2, client=mock_client(h))
        raise AssertionError("debió fallar")
    except P.FuenteNoDisponible:
        pass


def test_reintento_429_luego_200():
    from services.ingestion import openmeteo as OM
    data = json.loads((FIX / "openmeteo_motril_2d.json").read_text(encoding="utf-8"))
    st = {"id": "t-retry", "lat": 36.75, "lon": -3.87}
    calls = {"n": 0}

    def h(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, json={"error": True})
        return httpx.Response(200, json=data)
    res = OM.forecast(st, 2, client=mock_client(h))
    assert len(res.points) == 2 and calls["n"] == 3
    for f in C.CACHE_DIR.glob("openmeteo_t-retry_*"):
        f.unlink()


def test_cache_expirada_sirve_obsoleta():
    from services.ingestion import openmeteo as OM
    data = json.loads((FIX / "openmeteo_motril_2d.json").read_text(encoding="utf-8"))
    st = {"id": "t-stale", "lat": 36.75, "lon": -3.87}
    params = {"lat": 36.75, "lon": -3.87, "days": 2}
    C.write("openmeteo", "t-stale", "pronostico", params, data)
    p = C._path("openmeteo", "t-stale", "pronostico", params)
    blob = json.loads(p.read_text(encoding="utf-8"))
    blob["cached_at"] = time.time() - 7200  # expirada (TTL 1 h)
    p.write_text(json.dumps(blob), encoding="utf-8")

    def h(request):
        raise httpx.ConnectError("caída")
    res = OM.forecast(st, 2, client=mock_client(h))
    assert res.obsolete is True and len(res.points) == 2
    p.unlink()


def test_zona_horaria_espana_cambio_hora():
    from zoneinfo import ZoneInfo
    from datetime import datetime
    mad = ZoneInfo("Europe/Madrid")
    assert datetime(2026, 2, 1, 12, tzinfo=mad).utcoffset().total_seconds() == 3600
    assert datetime(2026, 7, 1, 12, tzinfo=mad).utcoffset().total_seconds() == 7200
    # Transiciones 2026: 29 mar y 25 oct
    assert datetime(2026, 3, 28, 12, tzinfo=mad).utcoffset().total_seconds() == 3600
    assert datetime(2026, 3, 30, 12, tzinfo=mad).utcoffset().total_seconds() == 7200
    assert datetime(2026, 10, 26, 12, tzinfo=mad).utcoffset().total_seconds() == 3600


def test_historico_cerrado_reproducible():
    import csv
    f = FIX / "historico_cerrado.csv"
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    for r in rows:
        for k in ("precip_mm", "et0_mm", "tmin_c", "tmax_c"):
            r[k] = float(r[k]) if r[k] not in ("", None) else None
    a = SC.historico_cerrado(rows, "motril-18140")
    b = SC.historico_cerrado(rows, "motril-18140")
    assert a == b and a["serie"]["kind"] == "estimacion" and len(a["serie"]["points"]) > 7


def test_snapshot_roundtrip():
    payload = {"escenario": "t", "serie": {"points": [{"date": "2026-01-02"}]}}
    SC.snapshot_save("t-game", "2026-01-02", payload)
    assert SC.snapshot_load("t-game", "2026-01-02") == payload
    import shutil
    shutil.rmtree(SC.SNAP_DIR / "t-game")


def test_estaciones_default_motril():
    assert ST.DEFAULT_STATION == "motril-18140"
    st = ST.get_station(None)
    assert st["aemet_municipio"] == "18140"
    assert len(ST.list_stations()) >= 1
