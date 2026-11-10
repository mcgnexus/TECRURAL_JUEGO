"""Fase 6 — Cuentas, autenticación y consentimiento (juego). Proveedores simulados, sin claves en cliente."""
from __future__ import annotations
import re
import secrets
import time
from dataclasses import dataclass, field

PHONE_RE = re.compile(r"^\+\d{7,15}$")  # E.164 genérico; ES habitual +34...
CODE_TTL_S = 600
SESSION_TTL_S = 86400
MAX_SEND_PER_HOUR = 5
MAX_VERIFY_ATTEMPTS = 5

ACCOUNTS: dict[str, dict] = {}  # id -> cuenta
BY_PHONE: dict[str, str] = {}  # phone -> id
SESSIONS: dict[str, dict] = {}  # token -> {account_id, expires}
OTP: dict[str, dict] = {}  # phone -> {code, expires, attempts, sent:[ts]}
OUTBOX: list[dict] = []  # SMS simulados enviados (prueba de revocación)
CONTACTS: dict[str, list] = {}  # account_id -> solicitudes contacto
VERSIONS: dict[str, list] = {}  # game_id -> [{v, day, state, at}]


def _now() -> float:
    return time.time()


def valid_phone(phone: str) -> bool:
    return bool(PHONE_RE.match(phone or ""))


def request_code(phone: str, email: str | None = None, simulated: bool = True) -> dict:
    """Paso 1 registro: genera código 6 dígitos, límite de envíos. Devuelve código solo en simulado."""
    if not valid_phone(phone):
        raise ValueError("teléfono inválido (formato E.164, ej. +34600000001)")
    if email is not None and ("@" not in email or "." not in email):
        raise ValueError("correo inválido")
    now = _now()
    o = OTP.get(phone, {"sent": [], "attempts": 0})
    o["sent"] = [t for t in o.get("sent", []) if now - t < 3600]
    if len(o["sent"]) >= MAX_SEND_PER_HOUR:
        raise PermissionError("límite de envíos alcanzado, intente más tarde (protección abuso)")
    code = f"{secrets.randbelow(900000) + 100000:06d}"
    o.update({"code": code, "expires": now + CODE_TTL_S, "attempts": 0})
    o["sent"].append(now)
    OTP[phone] = o
    # Alta perezosa de cuenta no verificada (aislada por teléfono)
    if phone not in BY_PHONE:
        import uuid
        aid = uuid.uuid4().hex[:12]
        BY_PHONE[phone] = aid
        ACCOUNTS[aid] = {"id": aid, "phone": phone, "email": email, "verified": False,
                         "created_at": now, "marketing_consent": False, "consent_log": []}
    elif email:
        ACCOUNTS[BY_PHONE[phone]]["email"] = email
    OUTBOX.append({"to": phone, "kind": "otp", "at": now})
    out = {"ok": True, "nota": "código enviado (simulado en desarrollo). Caduca en 10 min."}
    if simulated:
        out["code_debug"] = code  # SOLO desarrollo/tests; jamás en producción real
    return out


def verify_code(phone: str, code: str) -> dict:
    """Paso 2: verifica código, marca cuenta verificada y abre sesión con expiración."""
    now = _now()
    o = OTP.get(phone)
    if not o or now > o.get("expires", 0):
        raise ValueError("código caducado o inexistente, pida uno nuevo (recuperación)")
    if o.get("attempts", 0) >= MAX_VERIFY_ATTEMPTS:
        raise PermissionError("cuenta bloqueada temporalmente por intentos (protección abuso)")
    if str(code) != str(o.get("code")):
        o["attempts"] = o.get("attempts", 0) + 1
        raise ValueError("código incorrecto")
    aid = BY_PHONE[phone]
    ACCOUNTS[aid]["verified"] = True
    OTP.pop(phone, None)
    token = secrets.token_urlsafe(24)
    SESSIONS[token] = {"account_id": aid, "expires": now + SESSION_TTL_S}
    return {"token": token, "account_id": aid, "expires_in_s": SESSION_TTL_S,
            "nota": "sesión válida 24 h. Tratamiento: guardar partidas y recuperarlas. Ver /privacy."}


def account_from_token(token: str | None) -> dict | None:
    if not token:
        return None
    s = SESSIONS.get(token)
    if not s or _now() > s["expires"]:
        SESSIONS.pop(token, None)
        return None
    return ACCOUNTS.get(s["account_id"])


def set_consent(account_id: str, marketing: bool) -> dict:
    a = ACCOUNTS.get(account_id)
    if not a:
        raise KeyError("cuenta no encontrada")
    a["marketing_consent"] = bool(marketing)
    proof = {"at": _now(), "marketing": bool(marketing)}
    a["consent_log"].append(proof)
    return {"marketing_consent": a["marketing_consent"], "prueba": proof,
            "nota": "consentimiento comercial separado, opcional y revocable"}


def send_commercial(account_id: str, body: str) -> bool:
    """Solo envía si hay consentimiento vigente; si no, bloquea (revocación detiene envíos)."""
    a = ACCOUNTS.get(account_id)
    if not a or not a.get("marketing_consent"):
        return False
    OUTBOX.append({"to": a["phone"], "kind": "comercial", "body": body, "at": _now()})
    return True


def export_account(account_id: str) -> dict:
    a = ACCOUNTS.get(account_id)
    if not a:
        raise KeyError("cuenta no encontrada")
    return {"cuenta": {k: v for k, v in a.items()},
            "contactos": CONTACTS.get(account_id, []),
            "nota": "exportación RGPD: datos de la cuenta y solicitudes de contacto"}


def delete_account(account_id: str) -> dict:
    for tok, s in list(SESSIONS.items()):
        if s["account_id"] == account_id:
            SESSIONS.pop(tok, None)
    phone = ACCOUNTS[account_id]["phone"]
    CONTACTS.pop(account_id, None)
    ACCOUNTS.pop(account_id, None)
    BY_PHONE.pop(phone, None)
    return {"ok": True, "nota": "cuenta, sesiones y contactos borrados"}


def save_version(game_id: str, state: dict) -> dict:
    vs = VERSIONS.setdefault(game_id, [])
    v = {"v": len(vs) + 1, "day": state.get("day"), "state": state, "at": _now()}
    vs.append(v)
    return {"v": v["v"], "day": v["day"]}


def list_versions(game_id: str) -> list:
    return [{"v": x["v"], "day": x["day"], "at": x["at"]} for x in VERSIONS.get(game_id, [])]


def get_version(game_id: str, v: int) -> dict | None:
    for x in VERSIONS.get(game_id, []):
        if x["v"] == v:
            return x
    return None
