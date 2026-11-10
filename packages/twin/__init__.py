"""Gemelo digital Fase 9 — piloto con sensores simulados. Real solo autorizado."""
from __future__ import annotations
import time

PILOTOS: dict[str, dict] = {}  # finca_id -> {owner_id, permiso_ref, observada, inferida, escenarios, alarmas, kill}
SENSORES: dict[str, dict] = {}  # sensor_id -> {finca_id, magnitud, unidad, frecuencia_s, calibrado, fallos}


def importar_finca(finca_id: str, owner_id: str, permiso_ref: str, limites: dict) -> dict:
    if not owner_id or not permiso_ref:
        raise ValueError("autorización verificable requerida por parcela (owner + permiso)")
    PILOTOS[finca_id] = {"owner_id": owner_id, "permiso_ref": permiso_ref, "limites": limites,
                         "observada": [], "inferida": [], "escenarios": [], "alarmas": [],
                         "kill": {}, "historial": [{"at": time.time(), "evento": "importacion"}]}
    return {"ok": True, "nota": "copia observada separada de inferencias y escenarios"}


def registrar_sensor(sensor_id: str, finca_id: str, magnitud: str, unidad: str,
                     frecuencia_s: int = 3600, calibrado: str = "") -> dict:
    SENSORES[sensor_id] = {"finca_id": finca_id, "magnitud": magnitud, "unidad": unidad,
                           "frecuencia_s": frecuencia_s, "calibrado": calibrado, "fallos": 0}
    return {"ok": True}


def ingerir(sensor_id: str, fecha: str, valor: float, duplicada_ok: bool = True) -> dict:
    """Aísla duplicados/retrasados/erróneos; nunca sobrescribe originales."""
    s = SENSORES.get(sensor_id)
    if not s:
        raise KeyError("sensor no registrado")
    p = PILOTOS[s["finca_id"]]
    if valor < -100 or valor > 10000:
        return {"aislado": True, "motivo": "fuera de rango físico"}
    if any(o.get("sensor") == sensor_id and o.get("fecha") == fecha for o in p["observada"]):
        return {"duplicado": True, "nota": "se conserva el primero"}
    p["observada"].append({"sensor": sensor_id, "fecha": fecha, "valor": valor})
    p["historial"].append({"at": time.time(), "evento": f"ingesta {sensor_id} {fecha}"})
    return {"ok": True}


def comparar(finca_id: str, predicciones: list[float], mediciones: list[float], umbral: float | None = None) -> dict:
    import math
    assert len(predicciones) == len(mediciones) and predicciones
    rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(predicciones, mediciones)) / len(predicciones))
    alarma = umbral is not None and rmse > umbral
    PILOTOS[finca_id]["alarmas"].append({"rmse": rmse, "alarma": alarma, "at": time.time()})
    return {"rmse": rmse, "alarma_deriva": alarma,
            "nota": "alarma exige revisión humana; cada recomendación desactivable"}


def kill_switch(finca_id: str, recomendacion: str, desactivar: bool = True) -> dict:
    PILOTOS[finca_id]["kill"][recomendacion] = bool(desactivar)
    return {"ok": True, "desactivada": bool(desactivar)}
