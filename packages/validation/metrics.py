"""Métricas Fase 7 por cultivo/zona/variable/estación/uso. Incluye base simple actual."""
from __future__ import annotations
import math


def mae(obs: list[float], pred: list[float]) -> float:
    assert len(obs) == len(pred) and len(obs) > 0
    return sum(abs(o - p) for o, p in zip(obs, pred)) / len(obs)


def rmse(obs: list[float], pred: list[float]) -> float:
    assert len(obs) == len(pred) and len(obs) > 0
    return math.sqrt(sum((o - p) ** 2 for o, p in zip(obs, pred)) / len(obs))


def sesgo(obs: list[float], pred: list[float]) -> float:
    """Media(pred - obs): positivo = sobrestima."""
    assert len(obs) == len(pred) and len(obs) > 0
    return sum(p - o for o, p in zip(obs, pred)) / len(obs)


def cobertura_intervalos(obs: list[float], low: list[float], high: list[float]) -> float:
    """Fracción de observaciones dentro del intervalo. Calibración: comparar con nominal."""
    assert len(obs) == len(low) == len(high) and len(obs) > 0
    dentro = sum(1 for o, l, h in zip(obs, low, high) if l <= o <= h)
    return dentro / len(obs)


def sensibilidad_especificidad(y_true: list[int], y_pred: list[int]) -> dict:
    """Clasificación binaria (p. ej. estrés sí/no)."""
    assert len(y_true) == len(y_pred) and len(y_true) > 0
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    sens = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    return {"sensibilidad": round(sens, 4), "especificidad": round(spec, 4),
            "n": len(y_true), "tp": tp, "tn": tn, "fp": fp, "fn": fn}


def comparar_con_base(obs: list[float], pred: list[float], base: list[float]) -> dict:
    """Comparación obligatoria con método simple actual (p. ej. media calibración)."""
    return {"mae_modelo": mae(obs, pred), "mae_base": mae(obs, base),
            "rmse_modelo": rmse(obs, pred), "rmse_base": rmse(obs, base),
            "mejora_mae": mae(obs, base) - mae(obs, pred),
            "n": len(obs)}
