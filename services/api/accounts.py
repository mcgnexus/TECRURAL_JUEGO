"""Fase 6 — Cuentas por email y contraseña, consentimiento y guardado (juego). Sin claves en cliente.

Persistencia: Postgres (Neon) cuando hay DATABASE_URL; memoria local si no.
En serverless (Vercel) cada instancia lee/escribe en DB, nunca solo memoria.
"""
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

ACCOUNTS: dict[str, dict] = {}  # id -> cuenta (fallback sin DB)
BY_EMAIL: dict[str, str] = {}  # email normalizado -> id (fallback)
SESSIONS: dict[str, dict] = {}  # token -> {account_id, expires} (fallback)
FAILED: dict[str, dict] = {}  # email -> {attempts, locked_until} (fallback)
RESETS: dict[str, dict] = {}  # email -> {token, expires} (fallback)
OUTBOX: list[dict] = []  # envíos comerciales simulados (prueba de revocación)
CONTACTS: dict[str, list] = {}  # account_id -> solicitudes contacto (fallback)
VERSIONS: dict[str, list] = {}  # game_id -> [{v, day, state, at}] (fallback)


def _db():
    try:
        from services.api import db as D
    except ImportError:
        try:
            import db as D  # type: ignore
        except ImportError:
            return None
    try:
        return D if D.database_configured() else None
    except Exception:
        return None


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
    if (D := _db()) is not None:
        try:
            f = D.failed_get(email) or {"attempts": 0, "locked_until": 0.0}
            return bool(_now() < f.get("locked_until", 0.0))
        except Exception:
            raise
    f = FAILED.get(email)
    return bool(f and _now() < f.get("locked_until", 0))


def register(email: str, password: str) -> dict:
    """Alta con email y contraseña. La contraseña nunca se guarda en claro."""
    em = _norm(email)
    if not valid_email(em):
        raise ValueError("correo inválido")
    if not password or len(password) < MIN_PASSWORD_LEN:
        raise ValueError(f"la contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres")
    if (D := _db()) is not None:
        try:
            if D.account_by_email(em):
                raise ValueError("esa cuenta ya existe; inicie sesión o recupere la contraseña")
            import uuid
            aid = uuid.uuid4().hex[:12]
            salt, digest = _hash(password)
            D.account_create(aid, em, salt, digest)
            return {"ok": True, "account_id": aid,
                    "nota": "cuenta creada. Tratamiento: guardar partidas y recuperarlas. Ver /privacy."}
        except ValueError:
            raise
        except Exception:
            raise  # con base configurada nunca confirmar un alta solo en memoria
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


def _check_password(stored: dict, password: str) -> bool:
    salt, digest = _hash(password or "", bytes.fromhex(stored["password_salt"]))
    return secrets.compare_digest(digest, stored["password_hash"])


def login(email: str, password: str) -> dict:
    """Verifica la contraseña y abre sesión de 24 h. Límite de intentos con bloqueo temporal."""
    em = _norm(email)
    if not valid_email(em):
        raise ValueError("correo inválido")
    if _locked(em):
        raise PermissionError("cuenta bloqueada temporalmente por intentos (protección abuso)")
    if (D := _db()) is not None:
        try:
            a = D.account_by_email(em)
            ok = bool(a and _check_password(a, password))
            if not ok:
                f = D.failed_get(em) or {"attempts": 0}
                n = (f.get("attempts", 0) or 0) + 1
                D.failed_bump(em, LOCKOUT_S if n >= MAX_LOGIN_ATTEMPTS else None)
                raise ValueError("credenciales incorrectas")
            D.failed_clear(em)
            token = secrets.token_urlsafe(24)
            D.session_create(token, a["id"], _now() + SESSION_TTL_S)
            return {"token": token, "account_id": a["id"], "expires_in_s": SESSION_TTL_S,
                    "nota": "sesión válida 24 h. Tratamiento: guardar partidas y recuperarlas. Ver /privacy."}
        except (ValueError, PermissionError):
            raise
        except Exception:
            raise
    aid = BY_EMAIL.get(em)
    ok = False
    if aid and (a := ACCOUNTS.get(aid)):
        ok = _check_password(a, password)
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
    import os as _os
    prod = _os.getenv("TECRURAL_PROD") == "1"
    em = _norm(email)
    if not valid_email(em):
        raise ValueError("correo inválido")
    out = {"ok": True, "nota": "si la cuenta existe, se envió un enlace de recuperación (válido 30 min)."}
    if (D := _db()) is not None:
        try:
            if D.account_by_email(em):
                tok = secrets.token_urlsafe(24)
                D.reset_save(em, tok, _now() + RESET_TTL_S)
                if simulated and not prod:
                    out["reset_debug"] = tok  # SOLO desarrollo/tests; jamás en producción real
            return out
        except Exception:
            raise
    if em in BY_EMAIL:
        tok = secrets.token_urlsafe(24)
        RESETS[em] = {"token": tok, "expires": _now() + RESET_TTL_S}
        if simulated and not prod:
            out["reset_debug"] = tok  # SOLO desarrollo/tests; jamás en producción real
    return out


def reset_password(email: str, token: str, password: str) -> dict:
    """Fija una contraseña nueva con el token de recuperación."""
    em = _norm(email)
    if not password or len(password) < MIN_PASSWORD_LEN:
        raise ValueError(f"la contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres")
    if (D := _db()) is not None:
        try:
            r = D.reset_get(em)
            if not r:
                raise ValueError("enlace caducado o inexistente, pida uno nuevo (recuperación)")
            if not secrets.compare_digest(str(token), str(r.get("token"))):
                raise ValueError("enlace inválido")
            a = D.account_by_email(em)
            if not a:
                raise KeyError("cuenta no encontrada")
            salt, digest = _hash(password)
            D.account_set_password(a["id"], salt, digest)
            D.reset_delete(em)
            D.failed_clear(em)
            D.sessions_delete_account(a["id"])
            return {"ok": True, "nota": "contraseña actualizada; sesiones anteriores cerradas."}
        except (ValueError, KeyError):
            raise
        except Exception:
            raise
    r = RESETS.get(em)
    if not r or _now() > r.get("expires", 0):
        raise ValueError("enlace caducado o inexistente, pida uno nuevo (recuperación)")
    if not secrets.compare_digest(str(token), str(r.get("token"))):
        raise ValueError("enlace inválido")
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
        if (D := _db()) is not None:
            try:
                D.session_delete(token)
            except Exception:
                raise
        SESSIONS.pop(token, None)
    return {"ok": True}


def account_from_token(token: str | None) -> dict | None:
    if not token:
        return None
    if (D := _db()) is not None:
        try:
            a = D.session_account(token)
            if a:
                return a
        except Exception:
            raise
    s = SESSIONS.get(token)
    if not s or _now() > s["expires"]:
        SESSIONS.pop(token, None)
        return None
    return ACCOUNTS.get(s["account_id"])


def set_consent(account_id: str, marketing: bool) -> dict:
    if (D := _db()) is not None:
        try:
            if D.account_set_consent(account_id, bool(marketing)):
                return {"marketing_consent": bool(marketing),
                        "prueba": {"marketing": bool(marketing)},
                        "nota": "consentimiento comercial separado, opcional y revocable"}
        except Exception:
            raise
    a = ACCOUNTS.get(account_id)
    if not a:
        raise KeyError("cuenta no encontrada")
    a["marketing_consent"] = bool(marketing)
    proof = {"at": _now(), "marketing": bool(marketing)}
    a["consent_log"].append(proof)
    return {"marketing_consent": a["marketing_consent"], "prueba": proof,
            "nota": "consentimiento comercial separado, opcional y revocable"}


def _account_email(account_id: str) -> str | None:
    if (D := _db()) is not None:
        try:
            if (a := D.account_by_id(account_id)):
                return a["email"]
        except Exception:
            raise
    if (a := ACCOUNTS.get(account_id)):
        return a["email"]
    return None


def send_commercial(account_id: str, body: str) -> bool:
    """Solo envía si hay consentimiento vigente; si no, bloquea (revocación detiene envíos)."""
    consent = None
    if (D := _db()) is not None:
        try:
            if (a := D.account_by_id(account_id)):
                consent = a.get("marketing_consent")
        except Exception:
            raise
    if consent is None:
        a = ACCOUNTS.get(account_id)
        if not a or not a.get("marketing_consent"):
            return False
        email = a["email"]
    elif not consent:
        return False
    else:
        email = _account_email(account_id) or ""
    OUTBOX.append({"to": email, "kind": "comercial", "body": body, "at": _now()})
    return True


def export_account(account_id: str) -> dict:
    if (D := _db()) is not None:
        try:
            if (a := D.account_by_id(account_id)):
                safe = {k: v for k, v in a.items() if k not in ("password_salt", "password_hash")}
                contacts = D.contacts_list(account_id) or []
                return {"cuenta": safe, "contactos": contacts,
                        "nota": "exportación RGPD: datos de la cuenta y solicitudes de contacto (sin credenciales)"}
        except Exception:
            raise
    a = ACCOUNTS.get(account_id)
    if not a:
        raise KeyError("cuenta no encontrada")
    safe = {k: v for k, v in a.items() if k not in ("password_salt", "password_hash")}
    return {"cuenta": safe,
            "contactos": CONTACTS.get(account_id, []),
            "nota": "exportación RGPD: datos de la cuenta y solicitudes de contacto (sin credenciales)"}


def delete_account(account_id: str) -> dict:
    if (D := _db()) is not None:
        try:
            D.sessions_delete_account(account_id)
            D.account_delete(account_id)
        except Exception:
            raise
    for tok, s in list(SESSIONS.items()):
        if s["account_id"] == account_id:
            SESSIONS.pop(tok, None)
    email = (ACCOUNTS.get(account_id) or {}).get("email")
    CONTACTS.pop(account_id, None)
    ACCOUNTS.pop(account_id, None)
    if email:
        BY_EMAIL.pop(email, None)
    return {"ok": True, "nota": "cuenta, sesiones y contactos borrados"}


def add_contact(account_id: str, medio: str, valor: str, finalidad: str, mensaje: str | None) -> None:
    if (D := _db()) is not None:
        try:
            if D.contact_add(account_id, medio, valor, finalidad, mensaje):
                return
        except Exception:
            raise
    CONTACTS.setdefault(account_id, []).append(
        {"medio": medio, "valor": valor, "finalidad": finalidad, "mensaje": mensaje, "at": _now()})


def save_version(game_id: str, state: dict) -> dict:
    if (D := _db()) is not None:
        try:
            if (out := D.version_save(game_id, state.get("day"), state)):
                return out
        except Exception:
            raise
    vs = VERSIONS.setdefault(game_id, [])
    v = {"v": len(vs) + 1, "day": state.get("day"), "state": state, "at": _now()}
    vs.append(v)
    return {"v": v["v"], "day": v["day"]}


def list_versions(game_id: str) -> list:
    if (D := _db()) is not None:
        try:
            if (out := D.versions_list(game_id)) is not None:
                return out
        except Exception:
            raise
    return [{"v": x["v"], "day": x["day"], "at": x["at"]} for x in VERSIONS.get(game_id, [])]


def get_version(game_id: str, v: int) -> dict | None:
    if (D := _db()) is not None:
        try:
            if (out := D.version_get(game_id, v)) is not None:
                return out
        except Exception:
            raise
    for x in VERSIONS.get(game_id, []):
        if x["v"] == v:
            return x
    return None
