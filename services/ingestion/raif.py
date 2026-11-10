"""RAIF Andalucía — contexto fitosanitario (Fase 5). Sin API inferida: portal/app web."""
from __future__ import annotations
from .provider import FuenteNoDisponible

ZONA = "Andalucia (visor SIG semanal, ~200 estaciones clima)"
FUENTE = "https://www.juntadeandalucia.es/organismos/agricultura/pesca-agua-y-desarrollo-rural/areas/agricultura/sanidad-vegetal/paginas/web-raif.html"


def aviso(cultivo: str, zona: str = "Costa Tropical (aprox.)", fecha: str = "") -> dict:
    """Devuelve contexto juego: nunca un diagnóstico. No inferir tratamiento."""
    return {
        "proveedor": "raif",
        "fuente": FUENTE,
        "zona": zona,
        "cultivo": cultivo,
        "fecha_consulta": fecha,
        "antiguedad": "semanal (visor SIG)",
        "nivel": "aviso regional, NO diagnóstico parcela",
        "nota": "juego orientativo: requiere confirmación en campo + técnico + MAPA vigente",
        "evidence_level": "juego",
    }


def observacion(*args, **kwargs):
    raise FuenteNoDisponible(
        "RAIF sin API pública inferida; usar portal/app oficial. Aviso regional ≠ diagnóstico.")
