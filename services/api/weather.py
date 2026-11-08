"""Clima real: estaciones, series normalizadas y escenarios (Fase 2). Solo servidor."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query

from services.ingestion import provider as P
from services.ingestion import stations as ST
from services.ingestion import scenarios as SC

router = APIRouter(prefix="/weather", tags=["clima"])


@router.get("/stations")
def stations():
    return {"por_defecto": ST.DEFAULT_STATION, "stations": ST.list_stations()}


def _serie(provider: str, station_id: str | None, days: int, kind: str, client=None) -> dict:
    st = ST.get_station(station_id)
    try:
        if provider == "aemet":
            from services.ingestion import aemet as A
            res = A.forecast(st, days, client=client) if kind == "pronostico" else A.observation(st, client=client)
        elif provider == "openmeteo":
            from services.ingestion import openmeteo as OM
            res = OM.forecast(st, days, client=client) if kind == "pronostico" else OM.past(st, days, client=client)
        elif provider == "siar":
            from services.ingestion import siar as S
            res = S.observation(st["id"], "", "")
        else:
            raise HTTPException(400, f"proveedor desconocido: {provider}")
    except P.FuenteNoDisponible as e:
        raise HTTPException(503, f"fuente no disponible: {e}")
    return res.to_dict()


@router.get("/forecast")
def forecast(provider: str = Query(default="aemet"), station: str | None = None, days: int = Query(default=7, ge=1, le=14)):
    return _serie(provider, station, days, "pronostico")


@router.get("/observation")
def observation(provider: str = Query(default="siar"), station: str | None = None, days: int = Query(default=7, ge=1, le=30)):
    return _serie(provider, station, days, "observacion")


@router.get("/scenario/present")
def scenario_present(station: str | None = None, days: int = Query(default=7, ge=1, le=14)):
    try:
        return SC.presente_con_prevision(station, days)
    except P.FuenteNoDisponible as e:
        raise HTTPException(503, f"fuente no disponible: {e}")


@router.get("/scenario/historic")
def scenario_historic(station: str | None = None):
    import csv
    from pathlib import Path
    f = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "historico_cerrado.csv"
    rows = [{k: (float(v) if k in ("precip_mm", "et0_mm", "tmin_c", "tmax_c") and v not in ("", None) else (v or None)) for k, v in r.items()} for r in csv.DictReader(f.open(encoding="utf-8"))]
    kinds = {r.get("kind") or "estimacion" for r in rows}
    return SC.historico_cerrado(rows, station, kind=sorted(kinds)[0] if len(kinds) == 1 else "estimacion")
