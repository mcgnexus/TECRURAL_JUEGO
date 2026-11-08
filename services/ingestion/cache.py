"""Caché local con TTL + reintentos limitados (Fase 2).

TTL: previsión 1 h, observación 6 h. Ante fallo con caché expirada: sirve
obsoleta marcada (obsolete=True) o lanza FuenteNoDisponible si no hay nada.
"""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache" / "weather"
TTL = {"pronostico": 3600, "observacion": 6 * 3600, "estimacion": 6 * 3600}


def _path(provider: str, station: str, kind: str, params: dict) -> Path:
    h = hashlib.sha1(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]
    return CACHE_DIR / f"{provider}_{station}_{kind}_{h}.json"


def read(provider: str, station: str, kind: str, params: dict):
    p = _path(provider, station, kind, params)
    if not p.exists():
        return None, True
    try:
        blob = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None, True
    age = time.time() - blob.get("cached_at", 0)
    return blob, age > TTL.get(kind, 3600)


def write(provider: str, station: str, kind: str, params: dict, payload: dict) -> None:
    p = _path(provider, station, kind, params)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"cached_at": time.time(), "payload": payload}, ensure_ascii=False), encoding="utf-8")


def fetch_with_cache(provider: str, station: str, kind: str, params: dict, fetcher, attempts: int = 3):
    """fetcher() -> payload dict. Reintentos con retroceso 1/2/4 s."""
    blob, expired = read(provider, station, kind, params)
    if blob is not None and not expired:
        return blob["payload"], False
    last: Exception | None = None
    for i in range(attempts):
        try:
            payload = fetcher()
            write(provider, station, kind, params, payload)
            return payload, False
        except Exception as e:  # noqa: BLE001 — cualquier fallo degrada, no bloquea
            last = e
            time.sleep(min(2 ** i, 4))
    if blob is not None:
        return blob["payload"], True  # obsoleta marcada
    from services.ingestion.provider import FuenteNoDisponible
    raise FuenteNoDisponible(f"{provider}/{station}/{kind} no disponible tras {attempts} intentos: {type(last).__name__ if last else '?'}")
