"""Prioridad 3: flujos web completos sin prometer de más; PWA instalable y offline honesto."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BASE = Path(__file__).resolve().parents[1]

def test_prevision_se_muestra_en_una_tabla_sin_json():
    app = (BASE / "apps/web/src/App.tsx").read_text(encoding="utf-8")
    assert '<table' in app and 'Escenario bajo' in app and 'Escenario central' in app and 'Escenario alto' in app
    assert 'JSON.stringify(info.forecast)' not in app
    assert 'JSON.stringify(forecast.forecast)' not in app

def test_flujos_esenciales_en_web():
    app = (BASE / "apps/web/src/App.tsx").read_text(encoding="utf-8")
    for s in ["Cuenta", "Guardar finca", "Avanzar", "Clima real", "Previsi", "Historial",
              "inventario", "phenology", "Vender", "agua:", "versión", "Sistema",
              "correo y contraseña", "sin garantía", "Profesional desactivado",
              "no finge datos", "no medida", "escenario"]:
        assert s in app, f"falta flujo {s}"

def test_pwa_instalable_y_offline_honesto():
    html = (BASE / "apps/web/index.html").read_text(encoding="utf-8")
    assert 'rel="manifest"' in html and 'rel="icon"' in html
    assert (BASE / "apps/web/public/icon-512.svg").exists()
    assert (BASE / "apps/web/public/sw.js").exists()
    sw = (BASE / "apps/web/public/sw.js").read_text(encoding="utf-8")
    assert "invent" not in sw.lower() or "nunca inventa" in sw.lower()
    main = (BASE / "apps/web/src/main.tsx").read_text(encoding="utf-8")
    assert "serviceWorker" in main
    assert "VITE_API_URL" in (BASE / "apps/web/.env.example").read_text(encoding="utf-8")

def test_sin_promesas_y_monitor_sin_secretos():
    from fastapi.testclient import TestClient
    from services.api.main import app
    c = TestClient(app)
    web = (BASE / "apps/web/src/App.tsx").read_text(encoding="utf-8").lower()
    for s in ["profesional activado", "garantizado", "gemelo validado"]:
        assert s not in web
    m = c.get("/monitoring/health").json()
    blob = str(m)
    for s in ("sk-", "jwt", "DATABASE_URL", "SIAR_TOKEN", "AEMET_API_KEY"):
        assert s not in blob
    assert c.get("/launch/checklist").json()["puerta"] == "ensayo"
    assert "pendiente" in c.get("/privacy").json()["revision_legal"]
