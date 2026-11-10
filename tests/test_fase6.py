"""Fase 6: cuentas, guardado versionado, consentimiento, borrado/export, backup y migración."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from services.api.main import app
from services.api import accounts as AC

c = TestClient(app)
H = lambda tok: {"Authorization": f"Bearer {tok}"}

def new_verified(phone="+34600000001", email=None):
    r = c.post("/accounts/request_code", json={"phone": phone, **({"email": email} if email else {})})
    assert r.status_code == 200, r.text
    code = r.json()["code_debug"]
    r = c.post("/accounts/verify", json={"phone": phone, "code": code})
    assert r.status_code == 200, r.text
    return r.json()["token"], r.json()["account_id"]

def test_registro_y_restauracion_sms_simulado_y_limites():
    tok, aid = new_verified("+34600000011")
    assert c.get("/accounts/me", headers=H(tok)).json()["verified"] is True
    # Límite envíos: 5/hora
    phone = "+34600000012"
    for _ in range(5):
        assert c.post("/accounts/request_code", json={"phone": phone}).status_code == 200
    assert c.post("/accounts/request_code", json={"phone": phone}).status_code == 429
    # Intentos verificación limitados y aislados
    c.post("/accounts/request_code", json={"phone": "+34600000013"})
    for _ in range(5):
        assert c.post("/accounts/verify", json={"phone": "+34600000013", "code": "000000"}).status_code == 422
    assert c.post("/accounts/verify", json={"phone": "+34600000013", "code": "000000"}).status_code == 429

def test_cuentas_aisladas_y_guardado_versionado_con_conflicto():
    t1, _ = new_verified("+34600000021")
    t2, _ = new_verified("+34600000022")
    g1 = c.post("/games", json={}, headers=H(t1)).json()["game_id"]
    g0 = c.post("/games", json={}).json()["game_id"]
    assert c.get(f"/games/{g0}").status_code == 200  # efímera antigua sigue abierta
    assert c.get(f"/games/{g1}").status_code == 403  # con cuenta exige propietario
    assert c.get(f"/games/{g1}", headers=H(t2)).status_code == 403  # otro propietario denegado
    assert c.get(f"/games/{g1}", headers=H(t1)).status_code == 200
    v1 = c.post(f"/games/{g1}/save", headers=H(t1)).json()
    assert v1["v"] == 1
    c.post(f"/games/{g1}/advance", json={"actions": []}, headers=H(t1))
    # Restaurar versión anterior sin force -> 409, con force -> ok sin pérdida silenciosa
    assert c.post(f"/games/{g1}/restore", json={"version": 1, "force": False}, headers=H(t1)).status_code == 409
    assert c.post(f"/games/{g1}/restore", json={"version": 1, "force": True}, headers=H(t1)).status_code == 200
    assert len(c.get(f"/games/{g1}/versions", headers=H(t1)).json()["versions"]) >= 1

def test_consentimiento_revocacion_export_borrado_y_sin_publicidad():
    tok, aid = new_verified("+34600000031")
    # Por defecto sin consentimiento: cuenta funciona igual
    assert c.get("/accounts/me", headers=H(tok)).json()["marketing_consent"] is False
    assert AC.send_commercial(aid, "oferta") is False
    n0 = len(AC.OUTBOX)
    c.post("/accounts/me/consent", json={"marketing": True}, headers=H(tok))
    assert AC.send_commercial(aid, "oferta") is True and len(AC.OUTBOX) == n0 + 1
    c.post("/accounts/me/consent", json={"marketing": False}, headers=H(tok))
    assert AC.send_commercial(aid, "oferta2") is False  # revocación detiene envíos
    exp = c.get("/accounts/me/export", headers=H(tok)).json()
    assert exp["cuenta"]["phone"] == "+34600000031"
    assert c.delete("/accounts/me", headers=H(tok)).status_code == 200
    assert c.get("/accounts/me", headers=H(tok)).status_code == 401

def test_migrar_partida_antigua_y_crm_bloqueado():
    tok, _ = new_verified("+34600000041")
    gid = c.post("/games", json={}, headers=H(tok)).json()["game_id"]
    viejo = {"schema_version": 1, "day": "2026-01-01", "cash_eur": 100.0, "reservoir_m3": 50.0,
             "parcels": [{"id": "P1", "crop": "aguacate", "area_ha": 1.0, "soil_water_mm": 40.0}]}
    r = c.post(f"/games/{gid}/restore", json={"backup": {"state": viejo}, "force": True}, headers=H(tok))
    assert r.status_code == 200
    assert r.json()["debt_eur"] == 0.0 and r.json()["cum_income_eur"] == 0.0  # migrado a v3
    assert c.post("/crm/sync", headers=H(tok)).status_code == 503
    assert c.get("/privacy").json()["revision_legal"].startswith("pendiente")
