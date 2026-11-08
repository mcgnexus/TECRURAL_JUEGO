"""AEMET OpenData — solo servidor. Clave desde AEMET_API_KEY, jamás en cliente/logs (Fase 2: contrato común).

Flujo AEMET: GET {base}{endpoint}?api_key=*** -> {estado, datos: url} -> GET url.
Pronóstico municipio/diaria 18140 (Motril): precipitacion por tramos (suma diaria),
temperaturas max/min. AEMET municipal NO da ET0 -> hueco que se sustituye de forma
etiquetada (ver scenarios) o detiene la simulación según política.
Observación convencional: endpoint parametrizable por id de estación; Motril aún
sin estación concreta verificada -> FuenteNoDisponible documentada.
"""
from __future__ import annotations
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from services.ingestion import provider as P
from services.ingestion.validate import validate

BASE = "https://opendata.aemet.es/opendata/api"
TZ = "Europe/Madrid"


def _key() -> str:
    k = os.getenv("AEMET_API_KEY", "")
    if not k:
        raise RuntimeError("falta AEMET_API_KEY en servidor (.env gitignored)")
    return k


def _client(timeout: int = 25):
    import httpx
    return httpx.Client(timeout=timeout)


def fetch_json(endpoint: str, timeout: int = 25, client=None) -> dict:
    """Compatibilidad Fase 0/1. endpoint sin clave, p. ej. '/prediccion/.../diaria/18140'."""
    import httpx
    key = _key()
    close = client is None
    c = client or _client(timeout)
    try:
        try:
            r = c.get(f"{BASE}{endpoint}", params={"api_key": key})
            r.raise_for_status()
            meta = r.json()
        except httpx.HTTPStatusError as e:
            code = e.response.status_code if e.response is not None else None
            raise RuntimeError(f"AEMET {code} en {endpoint}: clave/producto no autorizado o límite. Verificar clave y condiciones por producto.") from None
        if not isinstance(meta, dict) or meta.get("estado") != 200 or "datos" not in meta:
            return {"endpoint": endpoint, "estado": meta.get("estado") if isinstance(meta, dict) else None,
                    "descripcion": meta.get("descripcion") if isinstance(meta, dict) else None, "datos": None}
        d = c.get(meta["datos"])
        d.raise_for_status()
        d.encoding = "utf-8"  # AEMET no siempre declara charset; forzar UTF-8
        try:
            payload = d.json()
        except Exception:
            payload = {"texto": d.text[:2000]}
        return {"endpoint": endpoint, "estado": 200, "datos": payload,
                "procedencia": {"fuente": "AEMET OpenData",
                                "aviso": "verificar cobertura/producto y licencia vigente por producto"}}
    finally:
        if close:
            c.close()


def _parse_municipio_diaria(payload, station_id: str) -> P.SeriesResult:
    if isinstance(payload, dict):
        # Envoltorios conocidos o dict único de municipio
        if isinstance(payload.get("datos"), list):
            payload = payload["datos"]
        else:
            payload = [payload]
    pts: list[P.SeriesPoint] = []
    for m in payload:
        if not isinstance(m, dict):
            continue
        pred = m.get("prediccion", {}) if isinstance(m, dict) else {}
        for dia in pred.get("dia", []):
            prec = dia.get("precipitacion", []) or []
            tot = sum(float(x.get("value", 0) or 0) for x in prec if isinstance(x, dict))
            tmax = dia.get("temperatura", {}).get("maxima")
            tmin = dia.get("temperatura", {}).get("minima")
            pts.append(P.SeriesPoint(date=dia.get("fecha", "")[:10], precip_mm=round(tot, 1),
                                     et0_mm=None,  # AEMET municipal no da ET0 -> hueco
                                     tmin_c=tmin, tmax_c=tmax, kind="pronostico",
                                     station_id=station_id, tz=TZ))
    ok, q = validate(pts)
    issued = datetime.now(ZoneInfo(TZ)).isoformat(timespec="minutes")
    for p in ok:
        p.issued_at = issued
    return P.SeriesResult(provider="aemet", station_id=station_id, kind="pronostico", points=ok,
                          gaps=[p.date for p in ok if p.et0_mm is None] or q["gaps"],
                          dropped_invalid=q["dropped_invalid"], duplicates_removed=q["duplicates_removed"],
                          issued_at=issued,
                          provenance={"fuente": "AEMET OpenData predicción municipio/diaria",
                                      "et0": "hueco: AEMET municipal no publica ET0",
                                      "tz": TZ})


def forecast(station: dict, days: int = 7, client=None) -> P.SeriesResult:
    from services.ingestion.cache import fetch_with_cache
    endpoint = f"/prediccion/especifica/municipio/diaria/{station['aemet_municipio']}"
    params = {"endpoint": endpoint, "days": days}

    def run():
        r = fetch_json(endpoint, client=client)
        if r.get("estado") != 200 or not r.get("datos"):
            raise P.FuenteNoDisponible(f"AEMET sin datos en {endpoint}: {r.get('descripcion')}")
        return {"datos": r["datos"]}

    try:
        payload, obsolete = fetch_with_cache("aemet", station["id"], "pronostico", params, run)
    except P.FuenteNoDisponible:
        raise
    except RuntimeError as e:
        if "401" in str(e) or "403" in str(e) or "AEMET 4" in str(e):
            raise P.FuenteNoDisponible(f"AEMET auth/límite en {endpoint}: verificar clave y producto.") from None
        raise
    res = _parse_municipio_diaria(payload["datos"], station["id"])
    res.obsolete = obsolete
    return res


def observation(station: dict, station_convencional: str | None = None, client=None) -> P.SeriesResult:
    """Observación convencional por id de estación. Sin estación verificada -> no disponible."""
    if not station_convencional:
        raise P.FuenteNoDisponible(
            "AEMET observación: pendiente id de estación convencional para Motril "
            "(el municipio 18140 solo sirve para predicción).")
    r = fetch_json(f"/observacion/convencional/datos/estacion/{station_convencional}", client=client)
    if r.get("estado") != 200 or not r.get("datos"):
        raise P.FuenteNoDisponible(f"AEMET sin observación en estación {station_convencional}")
    pts = [P.SeriesPoint(date=(o.get("fint") or "")[:10],
                         precip_mm=float(o["prec"]) if o.get("prec") not in (None, "Ip") else 0.0,
                         et0_mm=None, tmin_c=None, tmax_c=None,
                         kind="observacion", station_id=station["id"], tz=TZ)
           for o in r["datos"] if isinstance(o, dict) and o.get("fint")]
    ok, q = validate(pts)
    return P.SeriesResult(provider="aemet", station_id=station["id"], kind="observacion", points=ok,
                          gaps=q["gaps"], dropped_invalid=q["dropped_invalid"],
                          duplicates_removed=q["duplicates_removed"],
                          provenance={"fuente": "AEMET observación convencional",
                                      "estacion_convencional": station_convencional, "tz": TZ})


def etiqueta_municipio_costa_tropical() -> dict:
    return {"municipio": "Motril", "ine": "18140", "nota": "estación cercana ≠ microclima parcela"}
