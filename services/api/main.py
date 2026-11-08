"""API TecRural — cuentas, partidas, permisos y consultas. Sin lógica científica duplicada."""
from __future__ import annotations
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from packages.simulator.engine import SimState, ParcelState, ParcelAction, WeatherDay, step

try:
    from services.api.db import init_schema, save_game, load_game, using_db, database_configured
except ImportError:  # ejecución como paquete raíz distinto
    from db import init_schema, save_game, load_game, using_db, database_configured  # type: ignore

BASE = Path(__file__).resolve().parents[2]
PARAMS = json.loads((BASE / "packages/content/default_game_params.json").read_text(encoding="utf-8"))

app = FastAPI(title="TecRural API", version="0.2.0")

# Fallback memoria para dev sin DB. Con DATABASE_URL se persiste en Neon.
GAMES: dict[str, dict] = {}
_DB_OK = False
try:
    _DB_OK = bool(init_schema())
except Exception:
    _DB_OK = False  # sin credenciales/red no bloquea el juego local; no se registra el secreto


class NewGame(BaseModel):
    account: str | None = None  # si None -> efímero


class DayAction(BaseModel):
    parcel_id: str
    irrigation_mm: float = 0.0
    harvest: bool = False
    prune: bool = False
    scout: bool = False
    fertilize_abstract: bool = False


class AdvanceDay(BaseModel):
    actions: list[DayAction] = []
    precip_mm: float = 2.0
    et0_mm: float = 3.5
    kind: str = "simulado"  # escenario ficticio etiquetado


def _new_state() -> SimState:
    d = PARAMS["default_farm"]
    return SimState(
        cash_eur=d["cash_eur"], reservoir_m3=d["reservoir_m3"],
        parcels=[ParcelState(id=p["id"], crop=p["crop"], area_ha=p["area_ha"], soil_water_mm=p["soil_water_mm"]) for p in d["parcels"]],
    )


def _restore_state(data: dict) -> SimState:
    parcels = [ParcelState(**p) for p in data.get("parcels", [])]
    return SimState(
        schema_version=data.get("schema_version", 1),
        day=data.get("day", "2026-01-01"),
        cash_eur=data.get("cash_eur", 5000.0),
        reservoir_m3=data.get("reservoir_m3", 200.0),
        reservoir_max_m3=data.get("reservoir_max_m3", 500.0),
        parcels=parcels,
        difficulty=data.get("difficulty", "normal"),
        realism=data.get("realismo", data.get("realism", "simplificado")),
    )


@app.post("/games")
def create_game(body: NewGame):
    gid = uuid.uuid4().hex[:8]
    st = _new_state()
    rec = {"state": st, "account": body.account, "ephemeral": body.account is None, "seed": 1234}
    GAMES[gid] = rec
    if _DB_OK:
        try:
            save_game(gid, None, rec["ephemeral"], rec["seed"], st)
        except Exception:
            pass
    return {"game_id": gid, "ephemeral": body.account is None,
            "aviso": "Sin cuenta la partida es efímera." if body.account is None else "Partida guardada en cuenta.",
            "modo": "juego (no es recomendación real)",
            "persistencia": "neon" if _DB_OK else "memoria-local"}


@app.get("/games/{gid}")
def get_game(gid: str):
    g = GAMES.get(gid)
    if g is None and _DB_OK:
        try:
            row = load_game(gid)
        except Exception:
            row = None
        if row:
            st = _restore_state(row["state_json"] if isinstance(row["state_json"], dict) else json.loads(row["state_json"]))
            g = {"state": st, "account": row["account_id"], "ephemeral": row["ephemeral"], "seed": row["seed"]}
            GAMES[gid] = g
    if not g:
        raise HTTPException(404, "partida no encontrada")
    st: SimState = g["state"]
    return {"cash_eur": st.cash_eur, "reservoir_m3": st.reservoir_m3, "day": st.day,
            "parcels": [{"id": p.id, "crop": p.crop, "soil_water_mm": p.soil_water_mm,
                         "health": p.health_0_1, "pending_kg": p.pending_fruit_kg} for p in st.parcels],
            "persistencia": "neon" if _DB_OK else "memoria-local"}


@app.post("/games/{gid}/advance")
def advance(gid: str, body: AdvanceDay):
    g = GAMES.get(gid)
    if g is None and _DB_OK:
        try:
            row = load_game(gid)
        except Exception:
            row = None
        if row:
            g = {"state": _restore_state(row["state_json"] if isinstance(row["state_json"], dict) else json.loads(row["state_json"])),
                 "account": row["account_id"], "ephemeral": row["ephemeral"], "seed": row["seed"]}
            GAMES[gid] = g
    if not g:
        raise HTTPException(404, "partida no encontrada")
    st: SimState = g["state"]
    acts = {a.parcel_id: ParcelAction(irrigation_mm=a.irrigation_mm, harvest=a.harvest,
                                     prune=a.prune, scout=a.scout,
                                     fertilize_abstract=a.fertilize_abstract) for a in body.actions}
    import datetime as dt
    d = dt.date.fromisoformat(st.day) + dt.timedelta(days=1)
    w = WeatherDay(date=d.isoformat(), precip_mm=body.precip_mm, et0_mm=body.et0_mm, kind=body.kind)  # type: ignore
    out = step(st, acts, w, PARAMS, rng_seed=g["seed"])
    g["seed"] += 1
    if _DB_OK:
        try:
            save_game(gid, None, g["ephemeral"], g["seed"], st)
        except Exception:
            pass
    return out


@app.get("/health")
def health():
    return {"ok": True, "modo_profesional": "desactivado",
            "db_configurada": bool(database_configured()), "db_activa": bool(_DB_OK)}
