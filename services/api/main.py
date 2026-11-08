"""API TecRural — cuentas, partidas, permisos y consultas. Sin lógica científica duplicada."""
from __future__ import annotations
import datetime as dt
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.simulator.engine import SimState, ParcelState, ParcelAction, WeatherDay, step, step_week

try:
    from services.api.db import (init_schema, save_game, load_game, append_events, load_history,
                                 clear_history, database_configured)
except ImportError:  # ejecución como paquete raíz distinto
    from db import init_schema, save_game, load_game, append_events, load_history, clear_history, database_configured  # type: ignore

BASE = Path(__file__).resolve().parents[2]
PARAMS = json.loads((BASE / "packages/content/default_game_params.json").read_text(encoding="utf-8"))

try:
    from services.api.weather import router as weather_router
except ImportError:
    from weather import router as weather_router  # type: ignore

app = FastAPI(title="TecRural API", version="1.0.0")
app.include_router(weather_router)

# Fallback memoria para dev sin DB. Con DATABASE_URL se persiste en Neon.
GAMES: dict[str, dict] = {}
HIST: dict[str, list] = {}
_DB_OK = False
try:
    _DB_OK = bool(init_schema())
except Exception:
    _DB_OK = False  # sin credenciales/red no bloquea el juego local; no se registra el secreto


class NewGame(BaseModel):
    account: str | None = None  # si None -> efímero


class DayAction(BaseModel):
    parcel_id: str
    irrigation_mm: float = Field(default=0.0, ge=0, le=100)
    harvest: bool = False
    prune: bool = False
    scout: bool = False
    fertilize_abstract: bool = False


class AdvanceDay(BaseModel):
    actions: list[DayAction] = []
    precip_mm: float = Field(default=2.0, ge=0, le=500)
    et0_mm: float = Field(default=3.5, ge=0, le=15)
    kind: str = "simulado"  # escenario ficticio etiquetado


class AdvanceWeek(AdvanceDay):
    days: int = Field(default=7, ge=1, le=14)


class AdvanceWeather(BaseModel):
    actions: list[DayAction] = []
    provider: str = "auto"  # auto|aemet|openmeteo
    station: str | None = None
    days: int = Field(default=3, ge=1, le=7)
    permitir_ficticio: bool = False  # si True, días con hueco usan simulado etiquetado


class ParcelEdit(BaseModel):
    area_ha: float | None = Field(default=None, ge=0.1, le=10)


class FarmEdit(BaseModel):
    parcels: dict[str, ParcelEdit] = {}
    cash_eur: float | None = Field(default=None, ge=0, le=1000000)


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


def _get(gid: str) -> dict:
    g = GAMES.get(gid)
    if g is None and _DB_OK:
        try:
            row = load_game(gid)
        except Exception:
            row = None
        if row:
            data = row["state_json"] if isinstance(row["state_json"], dict) else json.loads(row["state_json"])
            g = {"state": _restore_state(data), "account": row["account_id"],
                 "ephemeral": row["ephemeral"], "seed": row["seed"]}
            GAMES[gid] = g
    if not g:
        raise HTTPException(404, "partida no encontrada")
    return g


def _persist(gid: str, g: dict) -> None:
    GAMES[gid] = g
    if _DB_OK:
        try:
            save_game(gid, None, g["ephemeral"], g["seed"], g["state"])
        except Exception:
            pass


def _record(gid: str, day: str, events: list) -> None:
    HIST.setdefault(gid, []).append({"day": day, "events": events})
    if _DB_OK:
        try:
            append_events(gid, day, events)
        except Exception:
            pass


def _to_actions(body: AdvanceDay) -> dict[str, ParcelAction]:
    return {a.parcel_id: ParcelAction(irrigation_mm=a.irrigation_mm, harvest=a.harvest,
            prune=a.prune, scout=a.scout, fertilize_abstract=a.fertilize_abstract) for a in body.actions}


@app.post("/games")
def create_game(body: NewGame):
    gid = uuid.uuid4().hex[:8]
    st = _new_state()
    g = {"state": st, "account": body.account, "ephemeral": body.account is None, "seed": 1234}
    _persist(gid, g)
    HIST[gid] = []
    if _DB_OK:
        try:
            clear_history(gid)
        except Exception:
            pass
    return {"game_id": gid, "ephemeral": body.account is None,
            "aviso": "Sin cuenta la partida es efímera." if body.account is None else "Partida guardada en cuenta.",
            "modo": "juego (no es recomendación real)",
            "persistencia": "neon" if _DB_OK else "memoria-local"}


@app.get("/games/{gid}")
def get_game(gid: str):
    g = _get(gid)
    st: SimState = g["state"]
    return {"cash_eur": st.cash_eur, "reservoir_m3": st.reservoir_m3, "day": st.day,
            "parcels": [{"id": p.id, "crop": p.crop, "area_ha": p.area_ha, "soil_water_mm": p.soil_water_mm,
                         "health": p.health_0_1, "pending_kg": p.pending_fruit_kg} for p in st.parcels],
            "persistencia": "neon" if _DB_OK else "memoria-local"}


@app.put("/games/{gid}")
def edit_farm(gid: str, body: FarmEdit):
    """Edición de finca ficticia. Límites 0.1-10 ha y validación como restricción de interfaz (juego)."""
    g = _get(gid)
    st: SimState = g["state"]
    for pid, pe in body.parcels.items():
        p = next((x for x in st.parcels if x.id == pid), None)
        if not p:
            raise HTTPException(404, f"parcela {pid} no existe")
        if pe.area_ha is not None:
            p.area_ha = pe.area_ha
    if body.cash_eur is not None:
        st.cash_eur = body.cash_eur
    _persist(gid, g)
    return get_game(gid)


@app.post("/games/{gid}/restart")
def restart(gid: str):
    g = _get(gid)
    st = _new_state()
    g["state"] = st
    g["seed"] = 1234
    HIST[gid] = []
    _persist(gid, g)
    if _DB_OK:
        try:
            clear_history(gid)
        except Exception:
            pass
    return get_game(gid)


def _next_days(start_day: str, n: int, body: AdvanceDay) -> list[WeatherDay]:
    d0 = dt.date.fromisoformat(start_day)
    return [WeatherDay(date=(d0 + dt.timedelta(days=i + 1)).isoformat(),
                       precip_mm=body.precip_mm, et0_mm=body.et0_mm, kind=body.kind)  # type: ignore
            for i in range(n)]


@app.post("/games/{gid}/advance")
def advance(gid: str, body: AdvanceDay):
    g = _get(gid)
    st: SimState = g["state"]
    try:
        out = step(st, _to_actions(body), _next_days(st.day, 1, body)[0], PARAMS, rng_seed=g["seed"])
    except ValueError as e:
        raise HTTPException(422, str(e))
    g["seed"] += 1
    _record(gid, out["state"]["day"], out["events"])
    _persist(gid, g)
    return out


@app.post("/games/{gid}/advance_week")
def advance_week(gid: str, body: AdvanceWeek):
    """Avance semanal determinista: N pasos diarios con las mismas acciones (equivale a N avances diarios)."""
    g = _get(gid)
    st: SimState = g["state"]
    try:
        out = step_week(st, _to_actions(body), _next_days(st.day, body.days, body), PARAMS, rng_seed=g["seed"])
    except ValueError as e:
        raise HTTPException(422, str(e))
    g["seed"] += body.days
    _record(gid, out["state"]["day"], out["events"])
    _persist(gid, g)
    return out


@app.get("/games/{gid}/history")
def history(gid: str):
    _get(gid)
    if _DB_OK:
        try:
            rows = load_history(gid)
            if rows:
                return {"history": rows, "fuente": "neon"}
        except Exception:
            pass
    return {"history": HIST.get(gid, []), "fuente": "memoria-local",
            "nota": "juego: explica efectos y costes por día; incertidumbre y procedencia en cada avance"}


@app.post("/games/{gid}/advance_weather")
def advance_weather(gid: str, body: AdvanceWeather):
    """Avanza con clima real normalizado (escenario presente_con_prevision).

    Guarda instantánea por día: la campaña se reproduce desde la instantánea
    aunque la fuente original cambie. Huecos -> 422 detenido salvo permitir_ficticio.
    """
    from services.ingestion import provider as P
    from services.ingestion import scenarios as SC
    g = _get(gid)
    st: SimState = g["state"]
    try:
        esc = SC.presente_con_prevision(body.station, body.days)
    except P.FuenteNoDisponible as e:
        raise HTTPException(503, f"fuente no disponible: {e}")
    serie = esc["serie"]
    by_date = {p["date"]: p for p in serie["points"]}
    migrada = False
    days: list[WeatherDay] = []
    for i in range(body.days):
        d = (dt.date.fromisoformat(st.day) + dt.timedelta(days=i + 1)).isoformat()
        p = by_date.get(d)
        if p is None and st.day == "2026-01-01" and i == 0:
            # La partida ficticia adopta el calendario real en el primer avance con
            # clima real (migración explícita y registrada, no inventada).
            serie_days = sorted(by_date)
            if len(serie_days) < body.days:
                raise HTTPException(422, "serie real más corta que los días pedidos")
            migrada = True
        if migrada:
            d = sorted(by_date)[i]
            p = by_date.get(d)
        if p is None or p.get("precip_mm") is None or p.get("et0_mm") is None:
            if not body.permitir_ficticio:
                raise HTTPException(422, f"datos insuficientes el {d} (hueco etiquetado): simulación detenida. Use permitir_ficticio o escenario histórico.")
            days.append(WeatherDay(date=d, precip_mm=2.0, et0_mm=3.5, kind="simulado",
                                   station_id=serie["station_id"]))
        else:
            days.append(WeatherDay(date=d, precip_mm=p["precip_mm"], et0_mm=p["et0_mm"],
                                   tmin_c=p.get("tmin_c") or 15.0, tmax_c=p.get("tmax_c") or 25.0,
                                   kind=p.get("kind") or "pronostico", station_id=serie["station_id"]))
    try:
        out = step_week(st, _to_actions(body), days, PARAMS, rng_seed=g["seed"]) if body.days > 1 else \
            step(st, _to_actions(body), days[0], PARAMS, rng_seed=g["seed"])
    except ValueError as e:
        raise HTTPException(422, str(e))
    g["seed"] += body.days
    snap = {"escenario": esc["escenario"], "station": esc["station"], "serie": serie,
            "avisos": esc["avisos"], "politica": esc["politica_huecos"],
            "dias_usados": [{"date": w.date, "precip_mm": w.precip_mm, "et0_mm": w.et0_mm,
                             "kind": w.kind, "station": w.station_id} for w in days]}
    for w in days:
        SC.snapshot_save(gid, w.date, snap)
    _record(gid, out["state"]["day"], out["events"] + [{"type": "clima_real", "proveedor": serie["provider"],
              "estacion": serie["station_id"], "dias": [w.date for w in days], "avisos": esc["avisos"],
              "calendario_migrado": migrada}])
    _persist(gid, g)
    out["weather_snapshot"] = {"dias": [w.date for w in days], "serie_kind": serie["kind"],
                               "calendario_migrado": migrada}
    return out


@app.get("/games/{gid}/snapshot/{day}")
def snapshot(gid: str, day: str):
    _get(gid)
    from services.ingestion import scenarios as SC
    try:
        return SC.snapshot_load(gid, day)
    except FileNotFoundError:
        raise HTTPException(404, "instantánea no encontrada")


@app.get("/health")
def health():
    return {"ok": True, "modo_profesional": "desactivado",
            "db_configurada": bool(database_configured()), "db_activa": bool(_DB_OK)}
