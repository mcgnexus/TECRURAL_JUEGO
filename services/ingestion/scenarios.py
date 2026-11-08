"""Escenarios y política de huecos (Fase 2).

- historico_cerrado: serie fija (fixture o SiAR autorizada). Reproducible siempre.
- presente_con_prevision: pasado modelizado (Open-Meteo past, kind=estimacion) +
  pronóstico (AEMET por defecto, Open-Meteo de reserva). Todo con issued_at.
- Política de huecos: con datos insuficientes la simulación SE DETIENE o se
  degrada a escenario ficticio etiquetado. La sustitución (p. ej. ET0 Open-Meteo
  donde AEMET no la da) se etiqueta `sustitucion` y se conserva. Nunca se inventa.
"""
from __future__ import annotations
import json
from pathlib import Path

from services.ingestion import provider as P
from services.ingestion import stations as ST
from services.ingestion.validate import validate

SNAP_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshots"
POLITICA = ("huecos: detener o degradar a ficticio etiquetado; sustitución etiquetada y "
            "conservada; nunca inventar puntos de datos")


def _substitute_et0(main: P.SeriesResult, fallback: P.SeriesResult) -> tuple[P.SeriesResult, list[str]]:
    """Rellena ET0 ausente con la misma fecha del fallback, etiquetando sustitución."""
    by_date = {p.date: p for p in fallback.points}
    notas: list[str] = []
    for p in main.points:
        if p.et0_mm is None and p.date in by_date and by_date[p.date].et0_mm is not None:
            p.et0_mm = by_date[p.date].et0_mm
            notas.append(f"{p.date}: ET0 de {fallback.provider} (sustitución etiquetada)")
    main.gaps = [p.date for p in main.points if p.precip_mm is None or p.et0_mm is None]
    return main, notas


def presente_con_prevision(station_id: str | None = None, days: int = 7, client=None) -> dict:
    from services.ingestion import aemet as A, openmeteo as OM
    st = ST.get_station(station_id)
    avisos: list[str] = []
    pron = None
    try:
        cand = A.forecast(st, days, client=client)
        if not cand.points:
            raise P.FuenteNoDisponible("AEMET devolvió 0 días (respuesta vacía o no parseable)")
        pron = cand
    except P.FuenteNoDisponible as e:
        avisos.append(f"AEMET no disponible ({e}); reserva Open-Meteo modelizado.")
        pron = OM.forecast(st, days, client=client)
    if any(p.et0_mm is None for p in pron.points):
        try:
            fb = OM.forecast(st, days, client=client)
            pron, notas = _substitute_et0(pron, fb)
            avisos.extend(notas)
        except P.FuenteNoDisponible as e:
            avisos.append(f"sin ET0 de reserva ({e}); la simulación se detiene en días con hueco.")
    pts, q = validate(pron.points)
    pron.points = pts
    pron.gaps = [p.date for p in pts if p.precip_mm is None or p.et0_mm is None]
    return {"escenario": "presente_con_prevision", "station": st, "serie": pron.to_dict(),
            "avisos": avisos, "politica_huecos": POLITICA}


def historico_cerrado(rows: list[dict], station_id: str | None = None, nombre: str = "historico",
                      kind: str = "estimacion") -> dict:
    """Serie fija reproducible (fixture o SiAR autorizada). kind honesto según origen."""
    from services.ingestion import siar as S
    st = ST.get_station(station_id)
    res = S.from_csv_rows(rows, st["id"], kind=kind)
    return {"escenario": nombre, "station": st, "serie": res.to_dict(),
            "avisos": [], "politica_huecos": POLITICA}


def snapshot_save(game_id: str, day: str, payload: dict) -> str:
    d = SNAP_DIR / game_id
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{day}.json"
    f.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(f)


def snapshot_load(game_id: str, day: str) -> dict:
    f = SNAP_DIR / game_id / f"{day}.json"
    return json.loads(f.read_text(encoding="utf-8"))
