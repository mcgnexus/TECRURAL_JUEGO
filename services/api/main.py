"""API TecRural — cuentas, partidas, permisos y consultas. Sin lógica científica duplicada."""
from __future__ import annotations
import json, uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from packages.simulator.engine import SimState, ParcelState, ParcelAction, WeatherDay, step

BASE = Path(__file__).resolve().parents[2]
PARAMS = json.loads((BASE / "packages/content/default_game_params.json").read_text(encoding="utf-8"))

app = FastAPI(title="TecRural API", version="0.1.0")

# Almacenamiento local efímero (SQLite/Postgres en siguiente iteración vía DATABASE_URL).
# Prueba sin cuenta: efímero y así se informa.
GAMES: dict[str, dict] = {}


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


@app.post("/games")
def create_game(body: NewGame):
    gid = uuid.uuid4().hex[:8]
    st = _new_state()
    GAMES[gid] = {"state": st, "account": body.account, "ephemeral": body.account is None, "seed": 1234}
    return {"game_id": gid, "ephemeral": body.account is None,
            "aviso": "Sin cuenta la partida es efímera." if body.account is None else "Partida guardada en cuenta.",
            "modo": "juego (no es recomendación real)"}


@app.get("/games/{gid}")
def get_game(gid: str):
    g = GAMES.get(gid)
    if not g:
        raise HTTPException(404, "partida no encontrada")
    st: SimState = g["state"]
    return {"cash_eur": st.cash_eur, "reservoir_m3": st.reservoir_m3, "day": st.day,
            "parcels": [{"id": p.id, "crop": p.crop, "soil_water_mm": p.soil_water_mm,
                         "health": p.health_0_1, "pending_kg": p.pending_fruit_kg} for p in st.parcels]}


@app.post("/games/{gid}/advance")
def advance(gid: str, body: AdvanceDay):
    g = GAMES.get(gid)
    if not g:
        raise HTTPException(404, "partida no encontrada")
    st: SimState = g["state"]
    acts = {a.parcel_id: ParcelAction(irrigation_mm=a.irrigation_mm, harvest=a.harvest,
                                     prune=a.prune, scout=a.scout,
                                     fertilize_abstract=a.fertilize_abstract) for a in body.actions}
    # Fecha siguiente simple
    nxt = "2026-01-02" if st.day == "2026-01-01" else st.day  # el motor fija day=weather.date
    import datetime as dt
    d = dt.date.fromisoformat(st.day) + dt.timedelta(days=1)
    w = WeatherDay(date=d.isoformat(), precip_mm=body.precip_mm, et0_mm=body.et0_mm, kind=body.kind)  # type: ignore
    out = step(st, acts, w, PARAMS, rng_seed=g["seed"])
    g["seed"] += 1
    return out


@app.get("/health")
def health():
    return {"ok": True, "modo_profesional": "desactivado"}
