"""Separación finca/campaña sin fuga temporal ni espacial. Subgrupos e incertidumbre."""
from __future__ import annotations


def separar_calibracion_prueba(filas: list[dict], prueba_fincas: set, prueba_campanas: set) -> tuple[list, list]:
    """Reserva conjunto de prueba nunca usado en calibración (pares finca×campaña disjuntos)."""
    cal, pru = [], []
    for f in filas:
        en_prueba = f.get("finca_id") in prueba_fincas or f.get("campaña") in prueba_campanas
        (pru if en_prueba else cal).append(f)
    return cal, pru


def comprobar_fuga(cal: list[dict], pru: list[dict]) -> dict:
    """Detecta solapes y fuga temporal: pares repetidos o fechas de prueba anteriores a calibración."""
    pares_cal = {(f.get("finca_id"), f.get("campaña")) for f in cal}
    pares_pru = {(f.get("finca_id"), f.get("campaña")) for f in pru}
    solape = sorted(pares_cal & pares_pru)
    fechas_cal = sorted(f.get("fecha", "") for f in cal if f.get("fecha"))
    fechas_pru = sorted(f.get("fecha", "") for f in pru if f.get("fecha"))
    fuga_temporal = bool(fechas_cal and fechas_pru and min(fechas_pru) < max(fechas_cal))
    return {"solape_pares": solape, "fuga_temporal": fuga_temporal,
            "n_cal": len(cal), "n_pru": len(pru), "ok": not solape and not fuga_temporal}


def informe_subgrupos(filas: list[dict], metrica_fn) -> dict:
    """Errores por subgrupo: año seco/húmedo, edad, suelo, variedad. Informa n e incertidumbre."""
    grupos: dict[str, list] = {}
    for f in filas:
        for clave in ("ano_tipo", "edad_grupo", "suelo_textura", "variedad"):
            k = f"{clave}={f.get(clave, 'desconocido')}"
            grupos.setdefault(k, []).append(f)
    out = {}
    for k, fs in sorted(grupos.items()):
        try:
            out[k] = {"n": len(fs), "metrica": metrica_fn(fs)}
        except Exception as e:
            out[k] = {"n": len(fs), "error": str(e)}
    return out
