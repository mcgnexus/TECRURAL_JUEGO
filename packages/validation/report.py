"""Informe reproducible Fase 7 + barrera profesional (prioridad 2).

Una aprobación solo habilita si está vinculada a: informe reproducible aprobable,
datos autorizados con permiso, umbrales cumplidos con n suficiente, versiones
exactas vigentes, revisión independiente, alcance coincidente y caducidad futura.
Cualquier requisito ausente o cambiado bloquea. El juego nunca se bloquea.
"""
from __future__ import annotations
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]


def _metrica_para_umbral(metricas: dict, clave: str):
    """Mapea clave de umbral a valor medido en el informe."""
    c = metricas.get("comparacion", {}) if isinstance(metricas, dict) else {}
    if clave.endswith(".mae_mm") or "mae" in clave:
        return c.get("mae_modelo")
    if clave.endswith(".rmse_kg") or "rmse" in clave:
        return c.get("rmse_modelo")
    if "cobertura" in clave:
        return metricas.get("cobertura")
    if clave.endswith(".sensibilidad"):
        e = metricas.get("estres", {})
        return e.get("sensibilidad") if isinstance(e, dict) else None
    if clave.endswith(".especificidad"):
        e = metricas.get("estres", {})
        return e.get("especificidad") if isinstance(e, dict) else None
    return None


def comprobar_umbrales(metricas: dict, umbrales: dict, n: int) -> tuple[bool, list[str]]:
    motivos: list[str] = []
    for k, u in umbrales.items():
        if not isinstance(u, dict) or u.get("valor") is None:
            motivos.append(f"umbral pendiente: {k}")
            continue
        n_min = u.get("n_min")
        if n_min is not None and n < n_min:
            motivos.append(f"muestra insuficiente {k}: n={n} < n_min={n_min}")
            continue
        med = _metrica_para_umbral(metricas, k)
        if med is None:
            motivos.append(f"métrica ausente para {k}")
            continue
        try:
            if "cobertura" in k or "sensibilidad" in k or "especificidad" in k:
                if float(med) < float(u["valor"]):
                    motivos.append(f"umbral incumplido {k}: {med} < {u['valor']}")
            else:  # error: menor es mejor
                if float(med) > float(u["valor"]):
                    motivos.append(f"umbral incumplido {k}: {med} > {u['valor']}")
        except (TypeError, ValueError):
            motivos.append(f"umbral no comparable {k}")
    return (len(motivos) == 0, motivos)


def informe_reproducible(dataset_id: str, filas: list[dict], metricas: dict, fugas: dict,
                         codigo_version: str, params_version: str, umbrales: dict,
                         dataset_autorizado: bool = False, permiso_ref: str = "",
                         revision_independiente: bool = False,
                         revisor: str = "") -> dict:
    """No declara 'gemelo digital validado' salvo finca concreta evaluada (aquí nunca)."""
    motivos: list[str] = []
    if not dataset_autorizado:
        motivos.append("datos no autorizados o sin permiso verificable")
    if not permiso_ref:
        motivos.append("permiso_ref ausente")
    if not revision_independiente:
        motivos.append("revisión independiente pendiente")
    ok_umb, m_umb = comprobar_umbrales(metricas, umbrales, len(filas))
    motivos.extend(m_umb)
    if fugas.get("solape_pares") or fugas.get("fuga_temporal"):
        motivos.append("fuga temporal o espacial detectada")
    aprobable = bool(filas and not motivos)
    return {
        "dataset": dataset_id,
        "n_total": len(filas),
        "metricas": metricas,
        "fugas": fugas,
        "codigo_version": codigo_version,
        "params_version": params_version,
        "umbrales": umbrales,
        "dataset_autorizado": bool(dataset_autorizado),
        "permiso_ref": permiso_ref,
        "revision_independiente": bool(revision_independiente),
        "revisor": revisor,
        "aprobable": aprobable,
        "motivos_bloqueo": motivos,
        "nota": ("informe reproducible desde datos autorizados; revisión independiente pendiente; "
                 "control de deriva e incidentes activo; sin vinculación a finca concreta "
                 "no existe gemelo digital validado"),
        "profesional": "desactivado",
    }


def aprobacion_valida(aprobacion: dict, informe: dict | None, codigo_actual: str,
                      params_actual: str, hoy: str) -> tuple[bool, list[str]]:
    """Comprueba TODOS los requisitos. Devuelve (válida, motivos)."""
    motivos: list[str] = []
    if not aprobacion.get("responsable_agronomico") or not aprobacion.get("responsable_producto"):
        motivos.append("falta firma agronómica o de producto")
    if aprobacion.get("responsable_agronomico") == aprobacion.get("responsable_producto"):
        motivos.append("firmas no independientes")
    if (aprobacion.get("caducidad") or "") < hoy:
        motivos.append("caducidad alcanzada o ausente")
    if not aprobacion.get("permiso_ref"):
        motivos.append("permiso_ref ausente en aprobación")
    if not aprobacion.get("revision_independiente"):
        motivos.append("sin revisión independiente declarada")
    rev = aprobacion.get("revisor_independiente") or ""
    if rev and rev == aprobacion.get("responsable_agronomico"):
        motivos.append("revisor independiente coincide con quien calibró")
    if aprobacion.get("codigo_version") != codigo_actual:
        motivos.append(f"código cambió: aprobación {aprobacion.get('codigo_version')} ≠ actual {codigo_actual}")
    if aprobacion.get("params_version") != params_actual:
        motivos.append(f"parámetros cambiaron: aprobación {aprobacion.get('params_version')} ≠ actual {params_actual}")
    if informe is None:
        motivos.append("sin informe reproducible vinculado")
        return False, motivos
    if informe.get("dataset") != aprobacion.get("dataset_id"):
        motivos.append("informe de otro dataset")
    if informe.get("permiso_ref") != aprobacion.get("permiso_ref"):
        motivos.append("permiso del informe no coincide")
    if informe.get("codigo_version") != aprobacion.get("codigo_version"):
        motivos.append("código del informe no coincide")
    if informe.get("params_version") != aprobacion.get("params_version"):
        motivos.append("parámetros del informe no coinciden")
    if not informe.get("aprobable"):
        motivos.extend([f"informe: {m}" for m in informe.get("motivos_bloqueo", [])] or ["informe no aprobable"])
    return (len(motivos) == 0, motivos)
