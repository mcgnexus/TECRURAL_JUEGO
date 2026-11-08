"""Persistencia TecRural — Postgres (Neon) cuando hay DATABASE_URL, memoria si no.

Pooled (-pooler) para tráfico app. Migraciones/DDL simples con autocommit.
Nunca exponer la URL en respuestas, logs ni cliente.
"""
from __future__ import annotations
import json
import os
from dataclasses import asdict
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

_conn = None
_use_db = False


def database_configured() -> bool:
    return bool(os.getenv("DATABASE_URL"))


def get_conn():
    global _conn
    if _conn is not None:
        return _conn
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    import psycopg  # diferido para no obligar en test puro motor
    _conn = psycopg.connect(url, autocommit=True)
    return _conn


def init_schema() -> bool:
    """Crea tablas si hay DATABASE_URL. Devuelve True si usó DB."""
    global _use_db
    conn = get_conn()
    if conn is None:
        _use_db = False
        return False
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    _use_db = True
    return True


def using_db() -> bool:
    return _use_db


def save_game(gid: str, account_id: str | None, ephemeral: bool, seed: int, state) -> None:
    conn = get_conn()
    if conn is None:
        return
    from packages.simulator.engine import SimState
    assert isinstance(state, SimState)
    payload = json.dumps(asdict(state))
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO games(id, account_id, ephemeral, seed, state_json, updated_at)
               VALUES (%s, %s, %s, %s, %s::jsonb, now())
               ON CONFLICT (id) DO UPDATE SET seed=EXCLUDED.seed, state_json=EXCLUDED.state_json, updated_at=now()""",
            (gid, account_id, ephemeral, seed, payload),
        )


def load_game(gid: str):
    conn = get_conn()
    if conn is None:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT account_id, ephemeral, seed, state_json FROM games WHERE id=%s", (gid,))
        row = cur.fetchone()
        if not row:
            return None
        return {"account_id": row[0], "ephemeral": row[1], "seed": row[2], "state_json": row[3]}


def append_events(gid: str, day: str, events: list) -> None:
    conn = get_conn()
    if conn is None:
        return
    with conn.cursor() as cur:
        cur.execute("INSERT INTO game_events(game_id, day, events_json) VALUES (%s, %s, %s::jsonb)",
                    (gid, day, json.dumps(events)))


def load_history(gid: str, limit: int = 60):
    conn = get_conn()
    if conn is None:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT day, events_json FROM game_events WHERE game_id=%s ORDER BY id DESC LIMIT %s", (gid, limit))
        return [{"day": r[0], "events": r[1]} for r in cur.fetchall()]


def clear_history(gid: str) -> None:
    conn = get_conn()
    if conn is None:
        return
    with conn.cursor() as cur:
        cur.execute("DELETE FROM game_events WHERE game_id=%s", (gid,))
