"""Validación de series: unidades, fechas, duplicados, huecos, imposibles (Fase 2)."""
from __future__ import annotations
from services.ingestion.provider import SeriesPoint


def validate(points: list[SeriesPoint]) -> tuple[list[SeriesPoint], dict]:
    seen: dict[str, SeriesPoint] = {}
    dup = 0
    for p in points:
        if p.date in seen:
            dup += 1
        seen[p.date] = p  # conserva el último
    ok: list[SeriesPoint] = []
    dropped = 0
    gaps: list[str] = []
    for date in sorted(seen):
        p = seen[date]
        bad = (
            (p.precip_mm is not None and not 0 <= p.precip_mm <= 500)
            or (p.et0_mm is not None and not 0 <= p.et0_mm <= 15)
            or (p.tmin_c is not None and not -15 <= p.tmin_c <= 55)
            or (p.tmax_c is not None and not -15 <= p.tmax_c <= 55)
            or (p.tmin_c is not None and p.tmax_c is not None and p.tmin_c > p.tmax_c)
        )
        if bad:
            dropped += 1
            continue
        if p.precip_mm is None or p.et0_mm is None:
            gaps.append(date)
        ok.append(p)
    return ok, {"duplicates_removed": dup, "dropped_invalid": dropped, "gaps": gaps}
