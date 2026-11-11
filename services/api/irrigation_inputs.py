"""Conversión física de riego conocido; no estima caudales ausentes."""
import math


def irrigation_mm_per_event(*, area_ha: float, volume_m3: float | None = None,
                            flow_m3_hour: float | None = None,
                            duration_hours: float | None = None) -> float:
    if not math.isfinite(area_ha) or area_ha <= 0:
        raise ValueError('Se necesita una superficie válida.')
    if volume_m3 is not None and (flow_m3_hour is not None or duration_hours is not None):
        raise ValueError('Indique volumen o caudal y duración, no ambos.')
    if volume_m3 is None:
        if flow_m3_hour is None or duration_hours is None:
            raise ValueError('La duración necesita un caudal total conocido.')
        if not all(math.isfinite(v) and v >= 0 for v in (flow_m3_hour, duration_hours)):
            raise ValueError('El caudal y la duración deben ser no negativos.')
        volume_m3 = flow_m3_hour * duration_hours
    if not math.isfinite(volume_m3) or volume_m3 < 0:
        raise ValueError('El volumen de riego no es válido.')
    return volume_m3 / (area_ha * 10)
