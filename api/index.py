"""Punto de entrada serverless (Vercel) para la API TecRural (FastAPI).

Vercel sirve la variable `app` ASGI. El repo (services/, packages/) se añade
al path porque la función se ejecuta desde api/.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.api.main import app  # noqa: E402,F401  (Vercel sirve `app`)
