"""AEMET OpenData — solo servidor. Clave desde AEMET_API_KEY, jamás en cliente/logs.

Uso: observaciones/predicción/avisos oficiales cuando estén verificados.
Flujo AEMET: GET {base}{endpoint}?api_key=*** -> {estado, datos: url} -> GET url.
Los logs muestran endpoint y estado, nunca la clave ni la URL completa.
"""
from __future__ import annotations
import os

BASE = "https://opendata.aemet.es/opendata/api"


def _key() -> str:
    k = os.getenv("AEMET_API_KEY", "")
    if not k:
        raise RuntimeError("falta AEMET_API_KEY en servidor (.env gitignored)")
    return k


def fetch_json(endpoint: str, timeout: int = 25) -> dict:
    """endpoint como '/prediccion/especifica/municipio/diaria/18140' (código INE, sin clave)."""
    import httpx
    key = _key()
    # Redactado: nunca registrar la URL con clave.
    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.get(f"{BASE}{endpoint}", params={"api_key": key})
            r.raise_for_status()
            meta = r.json()
    except httpx.HTTPStatusError as e:
        code = e.response.status_code if e.response is not None else None
        raise RuntimeError(f"AEMET {code} en {endpoint}: clave/producto no autorizado o límite. Verificar clave y condiciones por producto.") from None
    if not isinstance(meta, dict) or meta.get("estado") != 200 or "datos" not in meta:
        return {"endpoint": endpoint, "estado": meta.get("estado") if isinstance(meta, dict) else None,
                "descripcion": meta.get("descripcion") if isinstance(meta, dict) else None, "datos": None}
    with httpx.Client(timeout=timeout) as c:
        d = c.get(meta["datos"])
        d.raise_for_status()
        try:
            payload = d.json()
        except Exception:
            payload = {"texto": d.text[:2000]}
    return {"endpoint": endpoint, "estado": 200, "datos": payload,
            "procedencia": {"fuente": "AEMET OpenData", "tipo": "observacion_o_pronostico_segun_endpoint",
                            "aviso": "verificar cobertura/producto y licencia vigente por producto"}}


def etiqueta_municipio_costa_tropical() -> dict:
    # Ejemplo inicial: Motril (INE 18140, aproximado). Estación cercana ≠ microclima parcela.
    return {"municipio": "Motril (ejemplo)", "ine": "18140", "nota": "pendiente documentar estación/distancia/altitud y sustitución"}
