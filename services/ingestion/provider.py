"""Contratos comunes de clima (Fase 2). Todo proveedor devuelve el mismo esquema.

SeriesPoint: fecha ISO (Europe/Madrid), precipitación mm/día, ET0 mm/día (None = hueco),
tmin/tmax °C, kind observacion|pronostico|estimacion|simulado, station_id, issued_at, tz.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict


@dataclass
class SeriesPoint:
    date: str
    precip_mm: float | None = None
    et0_mm: float | None = None
    tmin_c: float | None = None
    tmax_c: float | None = None
    kind: str = "pronostico"
    station_id: str = ""
    issued_at: str | None = None
    tz: str = "Europe/Madrid"


@dataclass
class SeriesResult:
    provider: str
    station_id: str
    kind: str
    points: list[SeriesPoint] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)          # fechas con hueco
    dropped_invalid: int = 0
    duplicates_removed: int = 0
    obsolete: bool = False                                 # caché expirada servida por fallo
    issued_at: str | None = None                           # fecha emisión del pronóstico
    provenance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"provider": self.provider, "station_id": self.station_id, "kind": self.kind,
                "points": [asdict(p) for p in self.points], "gaps": self.gaps,
                "dropped_invalid": self.dropped_invalid, "duplicates_removed": self.duplicates_removed,
                "obsolete": self.obsolete, "issued_at": self.issued_at, "provenance": self.provenance}


class FuenteNoDisponible(RuntimeError):
    """La fuente no responde / sin credenciales / sin estación: degradar, nunca inventar."""
