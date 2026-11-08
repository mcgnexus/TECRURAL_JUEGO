"""Asistente explicativo (DeepSeek) — solo servidor, solo redacción.

REGLAS:
- Nunca fuente de valores científicos ni dosis. Solo explica eventos del juego en lenguaje claro.
- Nunca enviar datos identificativos o agrícolas privados sin base jurídica/información/acuerdo.
  Solo se envía un resumen anonimizado del juego (cultivo, día, evento).
- Clave desde DEEPSEEK_API_KEY. Jamás al cliente ni a logs.
"""
from __future__ import annotations
import os

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


def explain_game_event(cultivo: str, evento: str, indicador: str) -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        return "(explicación no disponible: falta DEEPSEEK_API_KEY en servidor)"
    import httpx
    prompt = (f"Explica en 2-3 frases simples para agricultor/estudiante este evento de JUEGO "
              f"(no es recomendación real): cultivo={cultivo}, evento={evento}, dato={indicador}. "
              f"Recuerda que es simulado y que el modo profesional está desactivado.")
    with httpx.Client(timeout=30) as c:
        r = c.post(API_URL, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                   json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                         "temperature": 0.3, "max_tokens": 220})
        r.raise_for_status()
        j = r.json()
    try:
        return j["choices"][0]["message"]["content"].strip()
    except Exception:
        return "(respuesta inesperada del asistente)"
