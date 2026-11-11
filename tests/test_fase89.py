"""Fases 8-9: lanzamiento/ensayo y gemelo piloto. Sin datos reales sin autorización."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_recursos_con_licencia_y_guia():
    import json
    rec = json.loads((Path(__file__).resolve().parents[1] / "packages/content/recursos.json").read_text(encoding="utf-8"))
    assert all(r.get("licencia") for r in rec["recursos"])
    assert "360px" in (Path(__file__).resolve().parents[1] / "docs/evidence/GUIA_ESTILO.md").read_text(encoding="utf-8")

def test_tres_publicos_y_objetivos_previos():
    t = (Path(__file__).resolve().parents[1] / "docs/evidence/ENSAYO_USUARIOS.md").read_text(encoding="utf-8")
    assert "Agricultores" in t and "cnicos" in t and "general" in t.lower()
    assert "ANTES" in t and "NO mediciones" in t or "no presentadas como mediciones" in t.lower() or "Metas" in t

def test_monitoring_sin_secretos_y_puerta():
    from fastapi.testclient import TestClient
    from services.api.main import app
    c = TestClient(app)
    m = c.get("/monitoring/health").json()
    assert "uptime_s" in m and "fuentes" in m
    blob = str(m)
    for s in ("sk-", "jwt", "DATABASE_URL", "SIAR_TOKEN"):
        assert s not in blob
    chk = c.get("/launch/checklist").json()
    assert chk["puerta"] == "ensayo" and "pendiente" in chk["estado"]

def test_seguridad_cuentas_aisladas_y_recuperacion():
    from fastapi.testclient import TestClient
    from services.api.main import app
    c = TestClient(app)
    c.post("/accounts/register", json={"email": "fase89a@ejemplo.es", "password": "Secreta01"})
    tok = c.post("/accounts/login", json={"email": "fase89a@ejemplo.es", "password": "Secreta01"}).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    g = c.post("/games", json={}, headers=h).json()["game_id"]
    assert c.get(f"/games/{g}", headers={"Authorization": "Bearer xxx"}).status_code in (401, 403)

def test_gemelo_piloto_simulado():
    from fastapi.testclient import TestClient
    from services.api.main import app
    c = TestClient(app)
    c.post("/accounts/register", json={"email": "fase89b@ejemplo.es", "password": "Secreta01"})
    tok = c.post("/accounts/login", json={"email": "fase89b@ejemplo.es", "password": "Secreta01"}).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    # Sin autorización verificable se rechaza
    assert c.post("/twin/import", json={"finca_id": "F", "owner_id": "", "permiso_ref": "", "limites": {}},
                  headers=h).status_code == 422
    assert c.post("/twin/import", json={"finca_id": "FINCA-PILOTO", "owner_id": "TIT-1",
                  "permiso_ref": "permiso-simulado", "limites": {}}, headers=h).status_code == 200
    c.post("/twin/sensor", json={"sensor_id": "S-HUM-01", "finca_id": "FINCA-PILOTO",
           "magnitud": "humedad", "unidad": "%"}, headers=h)
    assert c.post("/twin/ingest", json={"sensor_id": "S-HUM-01", "fecha": "2026-09-01", "valor": 30.0},
                  headers=h).json()["ok"] is True
    dup = c.post("/twin/ingest", json={"sensor_id": "S-HUM-01", "fecha": "2026-09-01", "valor": 30.0},
                 headers=h).json()
    assert dup.get("duplicado") is True  # duplicados no duplican
    malo = c.post("/twin/ingest", json={"sensor_id": "S-HUM-01", "fecha": "2026-09-02", "valor": 99999},
                  headers=h).json()
    assert malo.get("aislado") is True  # erróneos aislados
    r = c.post("/twin/compare", json={"finca_id": "FINCA-PILOTO", "predicciones": [10.0],
               "mediciones": [12.0], "umbral": 1.0}, headers=h).json()
    assert r["alarma_deriva"] is True  # deriva exige revisión humana
    assert c.post("/twin/kill?finca_id=FINCA-PILOTO&recomendacion=riego&desactivar=true",
                  headers=h).json()["desactivada"] is True
