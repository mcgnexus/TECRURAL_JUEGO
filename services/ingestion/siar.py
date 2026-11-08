"""SiAR / RIA Andalucía — adaptador conforme al contrato, alta pendiente (Fase 2).

Estado: requiere registro en "Mi SiAR" y manual de API; sin credenciales no hay
llamadas reales. Devuelve FuenteNoDisponible con el motivo. Acepta fixture local
(CSV SiAR) para pruebas y para cargar series históricas autorizadas.
"""
from __future__ import annotations
from services.ingestion import provider as P


def meta() -> dict:
    return {"provider": "siar", "estado": "alta pendiente",
            "acceso": "Mi SiAR con registro + manual API (MAPA)",
            "nota": "RIA: 100 estaciones desde 1999. Sin clave no hay observación real."}


def from_csv_rows(rows: list[dict], station_id: str, kind: str = "observacion") -> P.SeriesResult:
    pts = [P.SeriesPoint(date=r["date"], precip_mm=r.get("precip_mm"), et0_mm=r.get("et0_mm"),
                         tmin_c=r.get("tmin_c"), tmax_c=r.get("tmax_c"),
                         kind=kind, station_id=station_id) for r in rows]
    from services.ingestion.validate import validate
    ok, q = validate(pts)
    return P.SeriesResult(provider="siar", station_id=station_id, kind=kind, points=ok,
                          gaps=q["gaps"], dropped_invalid=q["dropped_invalid"],
                          duplicates_removed=q["duplicates_removed"],
                          provenance={"fuente": "SiAR/RIA (fixture o serie autorizada)", **meta()})


def observation(station_id: str, start: str, end: str) -> P.SeriesResult:
    raise P.FuenteNoDisponible("SiAR: alta pendiente (Mi SiAR + manual API). Sin credenciales no hay observación real.")
