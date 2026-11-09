"""SiAR / RIA — cliente real conforme al contrato (Fase 2). Solo servidor.

Manual: ManualTecnico_WEB_API_SIAR v2.2 (MAPA). Base https://servicio.mapa.gob.es/siarapi.
Token como parámetro URL `?token=` según manual; jamás en logs (errores redactados).
Observación diaria real con ET0 Penman-Monteith (EtPMon) y precipitación (mm).
"""
from __future__ import annotations
import os

from services.ingestion import provider as P
from services.ingestion.validate import validate

BASE = "https://servicio.mapa.gob.es/siarapi"


def _token() -> str:
    t = os.getenv("SIAR_TOKEN", "")
    if not t:
        raise RuntimeError("falta SIAR_TOKEN en servidor (.env gitignored)")
    return t


def _get(path: str, params: dict, timeout: int = 30, client=None):
    import httpx
    params = {"token": _token(), **params}  # token solo en la petición, nunca en logs
    close = client is None
    c = client or httpx.Client(timeout=timeout)
    try:
        r = c.get(f"{BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        code = e.response.status_code if e.response is not None else None
        raise RuntimeError(f"SiAR {code} en {path}: token/límite/producto. Revisar ACCESOS y alta.") from None
    finally:
        if close:
            c.close()


def accesos(client=None) -> dict:
    """Límites y uso actual del token."""
    return _get("/API/V1/Info/ACCESOS", {}, client=client)


def estaciones(client=None) -> list[dict]:
    """Catálogo de estaciones (Codigo Nemo, Término, IdEstacion...)."""
    j = _get("/API/V1/Info/ESTACIONES", {}, client=client)
    return j.get("datos", [])


def meta() -> dict:
    return {"provider": "siar", "estado": "alta verificada con token de servidor",
            "manual": "ManualTecnico_WEB_API_SIAR v2.2 (MAPA)",
            "nota": "RIA: 100 estaciones Andalucía desde 1999. Token solo servidor."}


def _parse_diarios(rows: list, station_id: str) -> P.SeriesResult:
    pts = []
    for o in rows:
        if not isinstance(o, dict) or not o.get("Fecha"):
            continue
        et0 = o.get("EtPMon")
        pts.append(P.SeriesPoint(
            date=str(o["Fecha"])[:10], precip_mm=_f(o.get("Precipitacion")),
            et0_mm=_f(et0), tmin_c=_f(o.get("TempMin")), tmax_c=_f(o.get("TempMax")),
            kind="observacion", station_id=station_id, tz="Europe/Madrid"))
    ok, q = validate(pts)
    return P.SeriesResult(provider="siar", station_id=station_id, kind="observacion", points=ok,
                          gaps=q["gaps"], dropped_invalid=q["dropped_invalid"],
                          duplicates_removed=q["duplicates_removed"],
                          provenance={"fuente": "SiAR observación diaria (ET0 Penman-Monteith)",
                                      "tz": "Europe/Madrid", **meta()})


def _f(v):
    try:
        return None if v in (None, "") else float(v)
    except (TypeError, ValueError):
        return None


def observation(station_id: str, start: str, end: str, client=None) -> P.SeriesResult:
    """Observación diaria real. station_id = código Nemo (p. ej. GR11)."""
    from services.ingestion.cache import fetch_with_cache
    params = {"Id": station_id, "FechaInicial": start, "FechaFinal": end}

    def run():
        j = _get("/API/V1/Datos/Diarios/ESTACION",
                 {"Id": station_id, "FechaInicial": start, "FechaFinal": end,
                  "DatosCalculados": "true"}, client=client)
        datos = j.get("datos")
        if not datos:
            raise P.FuenteNoDisponible(f"SiAR sin datos para {station_id} {start}..{end}: {j.get('MensajeRespuesta')}")
        return {"datos": datos}

    try:
        payload, obsolete = fetch_with_cache("siar", station_id, "observacion", params, run)
    except P.FuenteNoDisponible:
        raise
    except RuntimeError as e:
        if "SiAR 4" in str(e) or "401" in str(e) or "403" in str(e):
            raise P.FuenteNoDisponible(f"SiAR auth/límite: {str(e)[:120]}") from None
        raise
    res = _parse_diarios(payload["datos"], station_id)
    res.obsolete = obsolete
    return res


def from_csv_rows(rows: list[dict], station_id: str, kind: str = "observacion") -> P.SeriesResult:
    pts = [P.SeriesPoint(date=r["date"], precip_mm=r.get("precip_mm"), et0_mm=r.get("et0_mm"),
                         tmin_c=r.get("tmin_c"), tmax_c=r.get("tmax_c"),
                         kind=kind, station_id=station_id) for r in rows]
    ok, q = validate(pts)
    return P.SeriesResult(provider="siar", station_id=station_id, kind=kind, points=ok,
                          gaps=q["gaps"], dropped_invalid=q["dropped_invalid"],
                          duplicates_removed=q["duplicates_removed"],
                          provenance={"fuente": "SiAR/RIA (fixture o serie autorizada)", **meta()})
