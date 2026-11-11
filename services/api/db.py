"""Persistencia TecRural — Postgres (Neon) cuando hay DATABASE_URL, memoria si no.

Pooled (-pooler) para tráfico app. Migraciones/DDL simples con autocommit.
Nunca exponer la URL en respuestas, logs ni cliente.

Diseño serverless: cada operación abre y cierra su propia conexión
(Vercel congela/reutiliza instancias; no se conserva conexión global).
"""
from __future__ import annotations
import json
import os
from contextlib import contextmanager
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

_db_ok: bool | None = None


def database_configured() -> bool:
    return bool(os.getenv("DATABASE_URL"))


@contextmanager
def _cursor():
    """Conexión corta por operación. None si no hay DATABASE_URL."""
    url = os.getenv("DATABASE_URL")
    if not url:
        yield None
        return
    import psycopg  # diferido para no obligar en test puro motor
    conn = psycopg.connect(url, autocommit=True)
    try:
        with conn.cursor() as cur:
            yield cur
    finally:
        conn.close()


def init_schema() -> bool:
    """Crea tablas si hay DATABASE_URL. Devuelve True si usó DB."""
    global _db_ok
    if not database_configured():
        _db_ok = False
        return False
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with _cursor() as cur:
        assert cur is not None
        cur.execute(sql)
    _db_ok = True
    return True


def using_db() -> bool:
    return bool(_db_ok)


# ---------- Partidas ----------

def save_game(gid: str, account_id: str | None, ephemeral: bool, seed: int, state) -> None:
    with _cursor() as cur:
        if cur is None:
            return
        from packages.simulator.engine import SimState
        assert isinstance(state, SimState)
        from dataclasses import asdict
        payload = json.dumps(asdict(state))
        cur.execute(
            """INSERT INTO games(id, account_id, ephemeral, seed, state_json, updated_at)
               VALUES (%s, %s, %s, %s, %s::jsonb, now())
               ON CONFLICT (id) DO UPDATE SET account_id=EXCLUDED.account_id,
                 ephemeral=EXCLUDED.ephemeral, seed=EXCLUDED.seed,
                 state_json=EXCLUDED.state_json, updated_at=now()""",
            (gid, account_id, ephemeral, seed, payload),
        )


def load_game(gid: str):
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT account_id, ephemeral, seed, state_json FROM games WHERE id=%s", (gid,))
        row = cur.fetchone()
        if not row:
            return None
        return {"account_id": row[0], "ephemeral": row[1], "seed": row[2], "state_json": row[3]}


def append_events(gid: str, day: str, events: list) -> None:
    with _cursor() as cur:
        if cur is None:
            return
        cur.execute("INSERT INTO game_events(game_id, day, events_json) VALUES (%s, %s, %s::jsonb)",
                    (gid, day, json.dumps(events)))


def load_history(gid: str, limit: int = 60):
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT day, events_json FROM game_events WHERE game_id=%s ORDER BY id DESC LIMIT %s", (gid, limit))
        return [{"day": r[0], "events": r[1]} for r in cur.fetchall()]


def clear_history(gid: str) -> None:
    with _cursor() as cur:
        if cur is None:
            return
        cur.execute("DELETE FROM game_events WHERE game_id=%s", (gid,))


# ---------- Cuentas ----------

def account_create(aid: str, email: str, salt: str, digest: str) -> bool:
    """True si se creó en DB; False si no hay DB (el llamador usa memoria)."""
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute(
            "INSERT INTO accounts(id, email, password_salt, password_hash) VALUES (%s, %s, %s, %s)",
            (aid, email, salt, digest),
        )
        return True


def account_by_email(email: str):
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT id, email, password_salt, password_hash, marketing_consent, consent_log"
                    " FROM accounts WHERE email=%s", (email,))
        r = cur.fetchone()
        if not r:
            return None
        return {"id": r[0], "email": r[1], "password_salt": r[2], "password_hash": r[3],
                "marketing_consent": r[4], "consent_log": r[5] or []}


def account_by_id(aid: str):
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT id, email, password_salt, password_hash, marketing_consent, consent_log"
                    " FROM accounts WHERE id=%s", (aid,))
        r = cur.fetchone()
        if not r:
            return None
        return {"id": r[0], "email": r[1], "password_salt": r[2], "password_hash": r[3],
                "marketing_consent": r[4], "consent_log": r[5] or []}


def account_set_password(aid: str, salt: str, digest: str) -> bool:
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute("UPDATE accounts SET password_salt=%s, password_hash=%s WHERE id=%s", (salt, digest, aid))
        return True


def account_set_consent(aid: str, marketing: bool) -> bool:
    with _cursor() as cur:
        if cur is None:
            return False
        import datetime as _dt
        cur.execute("UPDATE accounts SET marketing_consent=%s,"
                    " consent_log = consent_log || %s::jsonb WHERE id=%s",
                    (marketing, json.dumps({"at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                                             "marketing": marketing}), aid))
        return True


def account_delete(aid: str) -> bool:
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute("DELETE FROM accounts WHERE id=%s", (aid,))
        return True


# ---------- Sesiones ----------

def session_create(token: str, aid: str, expires_epoch: float) -> bool:
    import datetime as _dt
    exp = _dt.datetime.fromtimestamp(expires_epoch, tz=_dt.timezone.utc)
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute("INSERT INTO sessions(token, account_id, expires_at) VALUES (%s, %s, %s)",
                    (token, aid, exp))
        return True


def session_account(token: str):
    """Devuelve la cuenta si la sesión existe y no caducó; limpia caducadas."""
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT account_id, expires_at FROM sessions WHERE token=%s", (token,))
        r = cur.fetchone()
        if not r:
            return None
        if r[1] < now:
            cur.execute("DELETE FROM sessions WHERE token=%s", (token,))
            return None
        return account_by_id(r[0])


def session_delete(token: str) -> bool:
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute("DELETE FROM sessions WHERE token=%s", (token,))
        return True


def sessions_delete_account(aid: str) -> bool:
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute("DELETE FROM sessions WHERE account_id=%s", (aid,))
        return True


# ---------- Recuperación e intentos ----------

def reset_save(email: str, token: str, expires_epoch: float) -> bool:
    import datetime as _dt
    exp = _dt.datetime.fromtimestamp(expires_epoch, tz=_dt.timezone.utc)
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute("INSERT INTO password_resets(email, token, expires_at) VALUES (%s, %s, %s)"
                    " ON CONFLICT (email) DO UPDATE SET token=EXCLUDED.token, expires_at=EXCLUDED.expires_at",
                    (email, token, exp))
        return True


def reset_get(email: str):
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT token, expires_at FROM password_resets WHERE email=%s", (email,))
        r = cur.fetchone()
        if not r or r[1] < now:
            return None
        return {"token": r[0]}


def reset_delete(email: str) -> bool:
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute("DELETE FROM password_resets WHERE email=%s", (email,))
        return True


def failed_get(email: str):
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT attempts, locked_until FROM login_attempts WHERE email=%s", (email,))
        r = cur.fetchone()
        if not r:
            return {"attempts": 0, "locked_until": 0.0}
        locked = r[1].timestamp() if r[1] else 0.0
        if locked and locked < now.timestamp():
            return {"attempts": 0, "locked_until": 0.0}
        return {"attempts": r[0], "locked_until": locked or 0.0}


def failed_bump(email: str, lock_seconds: float | None = None) -> None:
    import datetime as _dt
    locked = (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(seconds=lock_seconds)) if lock_seconds else None
    with _cursor() as cur:
        if cur is None:
            return
        cur.execute("INSERT INTO login_attempts(email, attempts, locked_until) VALUES (%s, 1, %s)"
                    " ON CONFLICT (email) DO UPDATE SET attempts=login_attempts.attempts+1,"
                    " locked_until=COALESCE(EXCLUDED.locked_until, login_attempts.locked_until)",
                    (email, locked))


def failed_clear(email: str) -> None:
    with _cursor() as cur:
        if cur is None:
            return
        cur.execute("DELETE FROM login_attempts WHERE email=%s", (email,))


# ---------- Contactos ----------

def contact_add(aid: str, medio: str, valor: str, finalidad: str, mensaje: str | None) -> bool:
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute("INSERT INTO contacts(account_id, medio, valor, finalidad, mensaje)"
                    " VALUES (%s, %s, %s, %s, %s)", (aid, medio, valor, finalidad, mensaje))
        return True


def contacts_list(aid: str) -> list | None:
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT medio, valor, finalidad, mensaje, created_at FROM contacts"
                    " WHERE account_id=%s ORDER BY id", (aid,))
        return [{"medio": r[0], "valor": r[1], "finalidad": r[2], "mensaje": r[3],
                 "at": r[4].timestamp() if r[4] else None} for r in cur.fetchall()]


# ---------- Versiones ----------

def version_save(game_id: str, day: str, state: dict):
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT COALESCE(MAX(v),0) FROM game_versions WHERE game_id=%s", (game_id,))
        v = (cur.fetchone() or [0])[0] + 1
        cur.execute("INSERT INTO game_versions(game_id, v, day, state_json) VALUES (%s, %s, %s, %s::jsonb)",
                    (game_id, v, day, json.dumps(state)))
        return {"v": v, "day": day}


def versions_list(game_id: str):
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT v, day, created_at FROM game_versions WHERE game_id=%s ORDER BY v", (game_id,))
        return [{"v": r[0], "day": r[1], "at": r[2].timestamp() if r[2] else None} for r in cur.fetchall()]


def version_get(game_id: str, v: int):
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT v, day, state_json FROM game_versions WHERE game_id=%s AND v=%s", (game_id, v))
        r = cur.fetchone()
        if not r:
            return None
        return {"v": r[0], "day": r[1], "state": r[2]}


# ---------- Snapshots ----------

def snapshot_save(game_id: str, day: str, payload: dict) -> bool:
    with _cursor() as cur:
        if cur is None:
            return False
        cur.execute("INSERT INTO snapshots(game_id, day, payload_json) VALUES (%s, %s, %s::jsonb)"
                    " ON CONFLICT (game_id, day) DO UPDATE SET payload_json=EXCLUDED.payload_json,"
                    " created_at=now()",
                    (game_id, day, json.dumps(payload)))
        return True


def snapshot_load(game_id: str, day: str):
    with _cursor() as cur:
        if cur is None:
            return None
        cur.execute("SELECT payload_json FROM snapshots WHERE game_id=%s AND day=%s", (game_id, day))
        r = cur.fetchone()
        if not r:
            return None
        return r[0] if isinstance(r[0], dict) else json.loads(r[0])
