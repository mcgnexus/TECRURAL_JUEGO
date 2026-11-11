"""Fase 6 — Cuentas por email y contraseña, consentimiento y guardado (juego). Sin claves en cliente."""
from __future__ import annotations
import hashlib
import re
import secrets
import time

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_TTL_S = 86400
RESET_TTL_S = 1800
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_S = 900
MIN_PASSWORD_LEN = 8
PBKDF2_ITERS = 260000

ACCOUNTS: dict[str, dict] = {}  # id -> cuenta
BY_EMAIL: dict[str, str] = {}  # email normalizado -> id
SESSIONS: dict[str, dict] = {}  # token -> {account_id, expires}
FAILED: dict[str, dict] = {}  # email -> {attempts, locked_until}
RESETS: dict[str, dict] = {}  # email -> {token, expires}
OUTBOX: list[dict] = []  # envíos comerciales simulados (prueba de revocación)
CONTACTS: dict[str, list] = {}  # account_id -> solicitudes contacto
VERSIONS: dict[str, list] = {}  # game_id -> [{v, day, state, at}]


def _now() -> float:
    return time.time()


def _norm(email: str) -> str:
    return (email or "").strip().lower()


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(_norm(email) or ""))


def _hash(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERS)
    return salt.hex(), dk.hex()


def _locked(email: str) -> bool:
    f = FAILED.get(email)
    return bool(f and _now() < f.get("locked_until", 0))


def register(email: str, password: str) -> dict:
    """Alta con email y contraseña. La contraseña nunca se guarda en claro."""
    em = _norm(email)
    if not valid_email(em):
        raise ValueError("correo inválido")
    if not password or len(password) < MIN_PASSWORD_LEN:
        raise ValueError(f"la contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres")
    if em in BY_EMAIL:
        raise ValueError("esa cuenta ya existe; inicie sesión o recupere la contraseña")
    import uuid
    aid = uuid.uuid4().hex[:12]
    salt, digest = _hash(password)
    BY_EMAIL[em] = aid
    ACCOUNTS[aid] = {"id": aid, "email": em, "password_salt": salt, "password_hash": digest,
                     "created_at": _now(), "marketing_consent": False, "consent_log": []}
    return {"ok": True, "account_id": aid,
            "nota": "cuenta creada. Tratamiento: guardar partidas y recuperarlas. Ver /privacy."}


def login(email: str, password: str) -> dict:
    """Verifica la contraseña y abre sesión de 24 h. Límite de intentos con bloqueo temporal."""
    em = _norm(email)
    if not valid_email(em):
        raise ValueError("correo inválido")
    if _locked(em):
        raise PermissionError("cuenta bloqueada temporalmente por intentos (protección abuso)")
    aid = BY_EMAIL.get(em)
    ok = False
    if aid and (a := ACCOUNTS.get(aid)):
        salt, digest = _hash(password or "", bytes.fromhex(a["password_salt"]))
        ok = secrets.compare_digest(digest, a["password_hash"])
    if not ok:
        f = FAILED.setdefault(em, {"attempts": 0, "locked_until": 0})
        f["attempts"] += 1
        if f["attempts"] >= MAX_LOGIN_ATTEMPTS:
            f["locked_until"] = _now() + LOCKOUT_S
        raise ValueError("credenciales incorrectas")
    FAILED.pop(em, None)
    token = secrets.token_urlsafe(24)
    SESSIONS[token] = {"account_id": aid, "expires": _now() + SESSION_TTL_S}
    return {"token": token, "account_id": aid, "expires_in_s": SESSION_TTL_S,
            "nota": "sesión válida 24 h. Tratamiento: guardar partidas y recuperarlas. Ver /privacy."}


def request_reset(email: str, simulated: bool = True) -> dict:
    """Solicita restablecer la contraseña. En ensayo devuelve el token (simulado en desarrollo)."""
    em = _norm(email)
    if not valid_email(em):
        raise ValueError("correo inválido")
    out = {"ok": True, "nota": "si la cuenta existe, se envió un enlace de recuperación (válido 30 min)."}
    if em in BY_EMAIL:
        tok = secrets.token_urlsafe(24)
        RESETS[em] = {"token": tok, "expires": _now() + RESET_TTL_S}
        if simulated:
            out["reset_debug"] = tok  # SOLO desarrollo/tests; jamás en producción real
    return out


def reset_password(email: str, token: str, password: str) -> dict:
    """Fija una contraseña nueva con el token de recuperación."""
    em = _norm(email)
    r = RESETS.get(em)
    if not r or _now() > r.get("expires", 0):
        raise ValueError("enlace caducado o inexistente, pida uno nuevo (recuperación)")
    if not secrets.compare_digest(str(token), str(r.get("token"))):
        raise ValueError("enlace inválido")
    if not password or len(password) < MIN_PASSWORD_LEN:
        raise ValueError(f"la contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres")
    aid = BY_EMAIL.get(em)
    if not aid or aid not in ACCOUNTS:
        raise KeyError("cuenta no encontrada")
    salt, digest = _hash(password)
    ACCOUNTS[aid]["password_salt"] = salt
    ACCOUNTS[aid]["password_hash"] = digest
    RESETS.pop(em, None)
    FAILED.pop(em, None)
    for tok, s in list(SESSIONS.items()):
        if s["account_id"] == aid:
            SESSIONS.pop(tok, None)
    return {"ok": True, "nota": "contraseña actualizada; sesiones anteriores cerradas."}


def logout(token: str | None) -> dict:
    if token:
        SESSIONS.pop(token, None)
    return {"ok": True}


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
    OUTBOX.append({"to": a["email"], "kind": "comercial", "body": body, "at": _now()})
    return True


def export_account(account_id: str) -> dict:
    a = ACCOUNTS.get(account_id)
    if not a:
        raise KeyError("cuenta no encontrada")
    safe = {k: v for k, v in a.items() if k not in ("password_salt", "password_hash")}
    return {"cuenta": safe,
            "contactos": CONTACTS.get(account_id, []),
            "nota": "exportación RGPD: datos de la cuenta y solicitudes de contacto (sin credenciales)"}


def delete_account(account_id: str) -> dict:
    for tok, s in list(SESSIONS.items()):
        if s["account_id"] == account_id:
            SESSIONS.pop(tok, None)
    email = ACCOUNTS[account_id]["email"]
    CONTACTS.pop(account_id, None)
    ACCOUNTS.pop(account_id, None)
    BY_EMAIL.pop(email, None)
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
