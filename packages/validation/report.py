"""Informe reproducible Fase 7: datos autorizados + código y versiones congeladas."""
from __future__ import annotations
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]


def informe_reproducible(dataset_id: str, filas: list[dict], metricas: dict, fugas: dict,
                         codigo_version: str, params_version: str, umbrales: dict) -> dict:
    """No declara 'gemelo digital validado' salvo finca concreta evaluada (aquí nunca)."""
    umbrales_ok = True
    motivos = []
    for k, u in umbrales.items():
        if not isinstance(u, dict) or u.get("valor") is None:
            umbrales_ok = False
            motivos.append(f"umbral pendiente: {k}")
    if fugas.get("solape_pares") or fugas.get("fuga_temporal"):
        umbrales_ok = False
        motivos.append("fuga temporal o espacial detectada")
    return {
        "dataset": dataset_id,
        "n_total": len(filas),
        "metricas": metricas,
        "fugas": fugas,
        "codigo_version": codigo_version,
        "params_version": params_version,
        "umbrales": umbrales,
        "aprobable": bool(umbrales_ok and filas),
        "motivos_bloqueo": motivos,
        "nota": ("informe reproducible desde datos autorizados; revisión independiente pendiente; "
                 "control de deriva e incidentes activo; sin vinculación a finca concreta "
                 "no existe gemelo digital validado"),
        "profesional": "desactivado",
    }
