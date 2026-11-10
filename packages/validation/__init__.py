"""Validación científica Fase 7 — marco general. Sin datos autorizados no hay aprobación."""
from .metrics import mae, rmse, sesgo, cobertura_intervalos, sensibilidad_especificidad, comparar_con_base
from .splits import separar_calibracion_prueba, informe_subgrupos, comprobar_fuga
from .report import informe_reproducible, comprobar_umbrales, aprobacion_valida
from .replay import replay_from_snapshot, comparar_ejecuciones
from .evidencia import auditar_evidencia

__all__ = ["mae", "rmse", "sesgo", "cobertura_intervalos", "sensibilidad_especificidad",
           "comparar_con_base", "separar_calibracion_prueba", "informe_subgrupos",
           "comprobar_fuga", "informe_reproducible", "comprobar_umbrales",
           "aprobacion_valida", "replay_from_snapshot", "comparar_ejecuciones",
           "auditar_evidencia"]
