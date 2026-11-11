"""API TecRural — cuentas, partidas, permisos y consultas. Sin lógica científica duplicada."""
from __future__ import annotations
import datetime as dt
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field

from packages.simulator.engine import SimState, ParcelState, ParcelAction, WeatherDay, step, step_week

try:
    from services.api.db import (init_schema, save_game, load_game, append_events, load_history,
                                 clear_history, database_configured)
except ImportError:  # ejecución como paquete raíz distinto
    from db import init_schema, save_game, load_game, append_events, load_history, clear_history, database_configured  # type: ignore

try:
    from services.api import accounts as AC
except ImportError:
    import accounts as AC  # type: ignore

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
    sell_kg: float | None = Field(default=None, ge=0, le=50000)
    channel: str = "base"
    fertilizer_id: str | None = None
    fertilizer_kg: float = Field(default=0.0, ge=0, le=2000)
    spray_id: str | None = None


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
        reservoir_max_m3=d.get("reservoir_max_m3", 500.0),
        parcels=[ParcelState(id=p["id"], crop=p["crop"], area_ha=p["area_ha"], soil_water_mm=p["soil_water_mm"]) for p in d["parcels"]],
    )


def _restore_state(data: dict) -> SimState:
    parcels = [ParcelState(**{k: v for k, v in p.items() if k in ParcelState.__dataclass_fields__}) for p in data.get("parcels", [])]
    return SimState(
        schema_version=data.get("schema_version", 3),
        day=data.get("day", "2026-01-01"),
        cash_eur=data.get("cash_eur", 5000.0),
        reservoir_m3=data.get("reservoir_m3", 200.0),
        reservoir_max_m3=data.get("reservoir_max_m3", 500.0),
        parcels=parcels,
        difficulty=data.get("difficulty", "normal"),
        realism=data.get("realismo", data.get("realism", "simplificado")),
        cum_pumped_m3=float(data.get("cum_pumped_m3", 0.0)),
        cum_inflow_m3=float(data.get("cum_inflow_m3", 0.0)),
        cum_energy_kwh=float(data.get("cum_energy_kwh", 0.0)),
        cum_overflow_m3=float(data.get("cum_overflow_m3", 0.0)),
        debt_eur=float(data.get("debt_eur", 0.0)),
        cum_income_eur=float(data.get("cum_income_eur", 0.0)),
        cum_fixed_eur=float(data.get("cum_fixed_eur", 0.0)),
    )


def _get(gid: str, authorization: str | None = None) -> dict:
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
    # Acceso por propietario: partidas con cuenta exigen su sesión; efímeras abiertas (compat. F1-5)
    if g.get("account"):
        a = _me(authorization)
        if not a or a["id"] != g["account"]:
            raise HTTPException(403, "partida de otro propietario (acceso denegado)")
    return g


def _bearer(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization[7:]


def _me(authorization: str | None = None):
    tok = _bearer(authorization)
    return AC.account_from_token(tok)


def _require_me(authorization: str | None = None) -> dict:
    tok = _bearer(authorization)
    a = AC.account_from_token(tok)
    if not a:
        raise HTTPException(401, "sesión requerida o caducada (inicie sesión; expira en 24 h)")
    return a


def _persist(gid: str, g: dict) -> None:
    GAMES[gid] = g
    if _DB_OK:
        try:
            save_game(gid, g.get("account"), g["ephemeral"], g["seed"], g["state"])
        except Exception:
            pass


def _record(gid: str, day: str, events: list, water_ledger: list | None = None) -> None:
    HIST.setdefault(gid, []).append({"day": day, "events": events, "water_ledger": water_ledger or []})
    if _DB_OK:
        try:
            append_events(gid, day, events + ([{"type": "libro_agua", "movimientos": water_ledger or []}] if water_ledger else []))
        except Exception:
            pass


# Analíticas juego por partida (suelo/hoja): registro, sin diagnóstico.
ANALYSES: dict[str, list] = {}


class SoilAnalysis(BaseModel):
    parcel_id: str
    date: str
    ph: float | None = None
    materia_organica_pct: float | None = None
    n_mg_kg: float | None = None
    p_mg_kg: float | None = None
    k_mg_kg: float | None = None
    nota: str = "registro juego, sin diagnóstico"


def _to_actions(body: AdvanceDay) -> dict[str, ParcelAction]:
    return {a.parcel_id: ParcelAction(irrigation_mm=a.irrigation_mm, harvest=a.harvest,
            prune=a.prune, scout=a.scout, fertilize_abstract=a.fertilize_abstract,
            sell_kg=a.sell_kg, channel=a.channel, fertilizer_id=a.fertilizer_id,
            fertilizer_kg=a.fertilizer_kg, spray_id=a.spray_id) for a in body.actions}


@app.post("/games")
def create_game(body: NewGame, authorization: str | None = Header(default=None)):
    me = _me(authorization)
    gid = uuid.uuid4().hex[:8]
    st = _new_state()
    # Cuenta con sesión obligatoria para guardar: solo con sesión la partida deja de ser efímera
    if me:
        g = {"state": st, "account": me["id"], "ephemeral": False, "seed": 1234}
    else:
        g = {"state": st, "account": body.account, "ephemeral": body.account is None, "seed": 1234}
        if body.account is not None:
            g["ephemeral"] = False  # compat. etiqueta antigua sin sesión
    _persist(gid, g)
    HIST[gid] = []
    if _DB_OK:
        try:
            clear_history(gid)
        except Exception:
            pass
    return {"game_id": gid, "ephemeral": g["ephemeral"],
            "aviso": "Sin cuenta la partida es efímera." if g["ephemeral"] else "Partida guardada en cuenta.",
            "modo": "juego (no es recomendación real)",
            "persistencia": "neon" if _DB_OK else "memoria-local"}


@app.get("/games/{gid}")
def get_game(gid: str, authorization: str | None = Header(default=None)):
    g = _get(gid, authorization)
    st: SimState = g["state"]
    return {"cash_eur": st.cash_eur, "reservoir_m3": st.reservoir_m3, "day": st.day,
            "reservoir_max_m3": st.reservoir_max_m3,
            "cum_pumped_m3": st.cum_pumped_m3, "cum_inflow_m3": st.cum_inflow_m3,
            "cum_energy_kwh": st.cum_energy_kwh, "cum_overflow_m3": st.cum_overflow_m3,
            "debt_eur": st.debt_eur, "cum_income_eur": st.cum_income_eur,
            "cum_fixed_eur": st.cum_fixed_eur,
            "parcels": [{"id": p.id, "crop": p.crop, "area_ha": p.area_ha, "soil_water_mm": p.soil_water_mm,
                         "health": p.health_0_1, "pending_kg": p.pending_fruit_kg,
                         "inventory_kg": p.inventory_kg, "phenology": p.phenology,
                         "cum_n_kg": p.cum_n_kg} for p in st.parcels],
            "infra_game": PARAMS.get("infra_game", {}),
            "economy_game": PARAMS.get("economy_game", {}),
            "aviso": "juego orientativo, no recomendación real. Profesional desactivado.",
            "aviso_agua": "juego: dotaciones ficticias, sin derecho real de agua",
            "persistencia": "neon" if _DB_OK else "memoria-local"}


@app.put("/games/{gid}")
def edit_farm(gid: str, body: FarmEdit, authorization: str | None = Header(default=None)):
    """Edición de finca ficticia. Límites 0.1-10 ha y validación como restricción de interfaz (juego)."""
    g = _get(gid, authorization)
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
def restart(gid: str, authorization: str | None = Header(default=None)):
    g = _get(gid, authorization)
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
def advance(gid: str, body: AdvanceDay, authorization: str | None = Header(default=None)):
    import time as _t
    g = _get(gid, authorization)
    st: SimState = g["state"]
    _s = _t.perf_counter()
    try:
        out = step(st, _to_actions(body), _next_days(st.day, 1, body)[0], PARAMS, rng_seed=g["seed"])
    except ValueError as e:
        try:
            from services.api import monitoring as _MON
        except ImportError:
            import monitoring as _MON  # type: ignore
        _MON.registrar_error("advance_422")
        raise HTTPException(422, str(e))
    try:
        from services.api import monitoring as _MON
    except ImportError:
        import monitoring as _MON  # type: ignore
    _MON.registrar_calculo((_t.perf_counter() - _s) * 1000)
    g["seed"] += 1
    _record(gid, out["state"]["day"], out["events"], out.get("water_ledger"))
    _persist(gid, g)
    return out


@app.post("/games/{gid}/advance_week")
def advance_week(gid: str, body: AdvanceWeek, authorization: str | None = Header(default=None)):
    """Avance semanal determinista: N pasos diarios con las mismas acciones (equivale a N avances diarios)."""
    g = _get(gid, authorization)
    st: SimState = g["state"]
    try:
        out = step_week(st, _to_actions(body), _next_days(st.day, body.days, body), PARAMS, rng_seed=g["seed"])
    except ValueError as e:
        raise HTTPException(422, str(e))
    g["seed"] += body.days
    _record(gid, out["state"]["day"], out["events"], out.get("water_ledger"))
    _persist(gid, g)
    return out


@app.get("/games/{gid}/history")
def history(gid: str, authorization: str | None = Header(default=None)):
    _get(gid, authorization)
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
def advance_weather(gid: str, body: AdvanceWeather, authorization: str | None = Header(default=None)):
    """Avanza con clima real normalizado (escenario presente_con_prevision).

    Guarda instantánea por día: la campaña se reproduce desde la instantánea
    aunque la fuente original cambie. Huecos -> 422 detenido salvo permitir_ficticio.
    """
    from services.ingestion import provider as P
    from services.ingestion import scenarios as SC
    g = _get(gid, authorization)
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
    from dataclasses import asdict as _asdict
    estado_inicial = _asdict(st)
    seed_usada = g["seed"]
    try:
        out = step_week(st, _to_actions(body), days, PARAMS, rng_seed=g["seed"]) if body.days > 1 else \
            step(st, _to_actions(body), days[0], PARAMS, rng_seed=g["seed"])
    except ValueError as e:
        raise HTTPException(422, str(e))
    g["seed"] += body.days
    from packages.simulator.engine import MODEL_VERSION as _MV
    snap = {"escenario": esc["escenario"], "station": esc["station"], "serie": serie,
            "avisos": esc["avisos"], "politica": esc["politica_huecos"],
            "acciones": [a.model_dump() for a in body.actions],
            "seed": seed_usada,
            "codigo_version": _MV,
            "params_version": PARAMS.get("version"),
            "estado_inicial": estado_inicial,
            "events": out["events"], "indicators": out["indicators"], "state": out["state"],
            "water_ledger": out.get("water_ledger"), "forecast": out.get("forecast"),
            "dias_usados": [{"date": w.date, "precip_mm": w.precip_mm, "et0_mm": w.et0_mm,
                             "kind": w.kind, "station": w.station_id} for w in days]}
    for w in days:
        SC.snapshot_save(gid, w.date, snap)
    _record(gid, out["state"]["day"], out["events"] + [{"type": "clima_real", "proveedor": serie["provider"],
              "estacion": serie["station_id"], "dias": [w.date for w in days], "avisos": esc["avisos"],
              "calendario_migrado": migrada}], out.get("water_ledger"))
    _persist(gid, g)
    out["weather_snapshot"] = {"dias": [w.date for w in days], "serie_kind": serie["kind"],
                               "calendario_migrado": migrada}
    return out


@app.get("/games/{gid}/snapshot/{day}")
def snapshot(gid: str, day: str, authorization: str | None = Header(default=None)):
    _get(gid, authorization)
    from services.ingestion import scenarios as SC
    try:
        return SC.snapshot_load(gid, day)
    except FileNotFoundError:
        raise HTTPException(404, "instantánea no encontrada")


@app.post("/games/{gid}/replay/{day}")
def replay(gid: str, day: str, authorization: str | None = Header(default=None)):
    """Repite la ejecución guardada en la instantánea con acciones, versiones y
    semilla originales y compara eventos, indicadores, estado, ledger y previsión."""
    import copy
    g = _get(gid, authorization)
    from services.ingestion import scenarios as SC
    try:
        snap = SC.snapshot_load(gid, day)
    except FileNotFoundError:
        raise HTTPException(404, "instantánea no encontrada")
    from packages.validation import replay_from_snapshot, comparar_ejecuciones
    from packages.simulator.engine import MODEL_VERSION as _MV
    if snap.get("codigo_version") != _MV or snap.get("params_version") != PARAMS.get("version"):
        raise HTTPException(409, "versiones cambiaron: la repetición exige código y parámetros congelados")
    st0 = _restore_state(snap.get("estado_inicial", {})) if snap.get("estado_inicial") else _new_state()
    out = replay_from_snapshot(snap, st0, PARAMS, snap.get("seed", g["seed"]))
    ref = {"events": snap.get("events"), "indicators": snap.get("indicators"),
           "state": snap.get("state"), "water_ledger": snap.get("water_ledger"),
           "forecast": snap.get("forecast")}
    if any(ref[k] is None for k in ref):
        return {"ok": True, "comparacion": {"identicas": True, "diferencias": []},
                "nota": "instantánea antigua sin resultado guardado; repetición ejecutada con versiones actuales",
                "out": {k: out.get(k) for k in ("indicators", "mass_balance")}}
    comp = comparar_ejecuciones({**out}, ref)
    return {"ok": comp["identicas"], "comparacion": comp}


@app.get("/games/{gid}/forecast")
def forecast(gid: str, authorization: str | None = Header(default=None)):
    """Previsión juego por intervalos. Profesional desactivado: orientativo, sin calibrar."""
    from packages.simulator.engine import forecast_interval
    g = _get(gid, authorization)
    st: SimState = g["state"]
    return {"forecast": {p.id: forecast_interval(p, PARAMS, st.day) for p in st.parcels},
            "evidence_level": "juego",
            "nota": "orientativo, profesional desactivado. Requiere campañas no usadas para calibrar."}


@app.post("/games/{gid}/analyses")
def add_analysis(gid: str, body: SoilAnalysis, authorization: str | None = Header(default=None)):
    _get(gid, authorization)
    ANALYSES.setdefault(gid, []).append(body.model_dump())
    return {"ok": True, "nota": "registro juego, sin diagnóstico"}


@app.get("/games/{gid}/analyses")
def list_analyses(gid: str, authorization: str | None = Header(default=None)):
    _get(gid, authorization)
    return {"analyses": ANALYSES.get(gid, []),
            "nota": "registro juego: un balance simplificado no es diagnóstico foliar"}


class DebtMove(BaseModel):
    amount_eur: float = Field(ge=-100000, le=100000)


@app.post("/games/{gid}/debt")
def move_debt(gid: str, body: DebtMove, authorization: str | None = Header(default=None)):
    """Deuda opcional juego (escenario). Positivo = pedir, negativo = devolver."""
    g = _get(gid, authorization)
    st: SimState = g["state"]
    if body.amount_eur > 0:
        st.debt_eur = round(st.debt_eur + body.amount_eur, 2)
        st.cash_eur = round(st.cash_eur + body.amount_eur, 2)
    else:
        pay = min(-body.amount_eur, st.cash_eur, st.debt_eur)
        st.debt_eur = round(st.debt_eur - pay, 2)
        st.cash_eur = round(st.cash_eur - pay, 2)
    _persist(gid, g)
    return {"debt_eur": st.debt_eur, "cash_eur": st.cash_eur,
            "nota": "juego: deuda escenario, no contrato real"}


@app.get("/raif/aviso")
def raif_aviso(cultivo: str = "aguacate", zona: str = "Costa Tropical (aprox.)"):
    from services.ingestion import raif as R
    return R.aviso(cultivo, zona)


@app.get("/prices/historic")
def prices_historic(cultivo: str | None = None):
    import csv
    f = BASE / "data/fixtures/precios_historicos.csv"
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    if cultivo:
        rows = [r for r in rows if r["cultivo"] == cultivo]
    return {"precios": rows, "nota": "históricos juego con fecha y nivel; futuros son escenarios, no cotizaciones"}


class TreatmentReq(BaseModel):
    parcel_id: str
    producto_id: str
    cultivo: str


@app.post("/treatments")
def treatment(req: TreatmentReq):
    """Funcionalidad profesional BLOQUEADA. Exige MAPA vigente + uso autorizado + técnico."""
    import json as _json
    cat = _json.loads((BASE / "packages/content/fitosanitarios.json").read_text(encoding="utf-8"))
    prod = next((x for x in cat["productos"] if x["id"] == req.producto_id), None)
    if prod is None or not prod.get("vigente") or req.cultivo not in prod.get("usos", []):
        raise HTTPException(422, f"bloqueado: ficha obsoleta o uso sin confirmar para {req.producto_id}/{req.cultivo}. Sin MAPA+técnico no hay recomendación.")
    raise HTTPException(403, "profesional desactivado: aun con ficha vigente se exige revisión por técnico competente")


# ---------- Fase 6: cuentas, guardado versionado, consentimiento, CRM bloqueado ----------

class RegisterBody(BaseModel):
    email: str = Field(description="Correo de la cuenta. No se solicita DNI.")
    password: str = Field(min_length=8, description="Mínimo 8 caracteres.")


class LoginBody(BaseModel):
    email: str
    password: str


class RecoverBody(BaseModel):
    email: str


class ResetBody(BaseModel):
    email: str
    token: str
    password: str = Field(min_length=8)


class ConsentBody(BaseModel):
    marketing: bool = False  # nunca premarcado en cliente


class ContactBody(BaseModel):
    medio: str = Field(description="correo|telefono")
    valor: str
    finalidad: str = Field(min_length=10, description="finalidad clara y concreta")
    mensaje: str | None = None


class RestoreBody(BaseModel):
    version: int | None = None
    backup: dict | None = None
    force: bool = False


ANALYTICS: dict[str, int] = {}


@app.post("/accounts/register")
def accounts_register(body: RegisterBody):
    if "dni" in (body.model_dump() or {}):
        raise HTTPException(422, "no se solicita DNI")
    try:
        return AC.register(body.email, body.password)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/accounts/login")
def accounts_login(body: LoginBody):
    try:
        return AC.login(body.email, body.password)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except PermissionError as e:
        raise HTTPException(429, str(e))


@app.post("/accounts/recover")
def accounts_recover(body: RecoverBody):
    try:
        return AC.request_reset(body.email, simulated=True)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/accounts/reset")
def accounts_reset(body: ResetBody):
    try:
        return AC.reset_password(body.email, body.token, body.password)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.post("/accounts/logout")
def accounts_logout(authorization: str | None = Header(default=None)):
    return AC.logout(_bearer(authorization))


@app.get("/accounts/me")
def accounts_me(authorization: str | None = Header(default=None)):
    a = _require_me(authorization)
    return {"id": a["id"], "email": a["email"],
            "marketing_consent": a["marketing_consent"],
            "nota": "tratamiento: guardar partidas y recuperarlas. Recuperación por correo."}


@app.get("/accounts/me/export")
def accounts_export(authorization: str | None = Header(default=None)):
    a = _require_me(authorization)
    return AC.export_account(a["id"])


@app.delete("/accounts/me")
def accounts_delete(authorization: str | None = Header(default=None)):
    a = _require_me(authorization)
    return AC.delete_account(a["id"])


@app.post("/accounts/me/consent")
def accounts_consent(body: ConsentBody, authorization: str | None = Header(default=None)):
    a = _require_me(authorization)
    return AC.set_consent(a["id"], body.marketing)


@app.post("/contact")
def contact(body: ContactBody, authorization: str | None = Header(default=None)):
    me = _me(authorization)
    aid = me["id"] if me else "anonimo"
    AC.CONTACTS.setdefault(aid, []).append({**body.model_dump(), "at": __import__("time").time()})
    return {"ok": True, "nota": f"solicitud registrada con finalidad: {body.finalidad}. Sin consentimiento comercial no hay comunicaciones."}


@app.get("/privacy")
def privacy():
    return {
        "tratamiento": "cuenta con correo y contraseña para guardar/recuperar partidas. Sin DNI.",
        "recuperacion": "enlace de recuperación por correo (30 min); sesiones 24 h; propietario verifica acceso a sus partidas.",
        "retencion": "partidas y versiones hasta borrado de cuenta; copias en Neon si hay DATABASE_URL.",
        "derechos": "acceso/exportación/borrado en /accounts/me. Contacto: pendiente definir con asesor.",
        "marketing": "consentimiento separado, opcional, no premarcado, revocable; revocación detiene envíos.",
        "crm": "sin salida a CRM: proveedor no elegido, sin base/acuerdo/retención definidos.",
        "analitica": "agregada y de conversión, sin datos personales.",
        "revision_legal": "pendiente asesor competente antes de producción; verificar legislación y reglas del canal.",
    }


@app.post("/games/{gid}/save")
def game_save(gid: str, authorization: str | None = Header(default=None)):
    g = _get(gid, authorization)
    if g.get("ephemeral"):
        raise HTTPException(422, "partida efímera: inicie sesión para guardar versionado")
    return AC.save_version(gid, g["state"] and __import__("dataclasses").asdict(g["state"]))


@app.get("/games/{gid}/versions")
def game_versions(gid: str, authorization: str | None = Header(default=None)):
    _get(gid, authorization)
    return {"versions": AC.list_versions(gid)}


@app.post("/games/{gid}/restore")
def game_restore(gid: str, body: RestoreBody, authorization: str | None = Header(default=None)):
    g = _get(gid, authorization)
    st = None
    if body.backup is not None:
        st = body.backup.get("state", body.backup)
    elif body.version is not None:
        v = AC.get_version(gid, body.version)
        if not v:
            raise HTTPException(404, "versión no encontrada")
        st = v["state"]
    else:
        raise HTTPException(422, "indique version o backup")
    # Migra partida antigua: campos ausentes toman valores actuales sin perder progreso
    new_state = _restore_state(st)
    cur_day = g["state"].day
    new_day = new_state.day
    if new_day < cur_day and not body.force:
        raise HTTPException(409, f"conflicto: la copia es anterior ({new_day} < {cur_day}). Reintente con force=true; no se pierde progreso silenciosamente.")
    g["state"] = new_state
    _persist(gid, g)
    _record(gid, new_state.day, [{"type": "restauracion", "nota": "recuperación con permisos, sin pérdida silenciosa"}])
    return get_game(gid, authorization)


@app.get("/games/{gid}/backup")
def game_backup(gid: str, authorization: str | None = Header(default=None)):
    g = _get(gid, authorization)
    from dataclasses import asdict as _asdict
    return {"game_id": gid, "state": _asdict(g["state"]), "history": HIST.get(gid, []),
            "versions": AC.list_versions(gid), "account": g.get("account"), "ephemeral": g.get("ephemeral")}


@app.post("/crm/sync")
def crm_sync(authorization: str | None = Header(default=None)):
    import os as _os
    if not _os.getenv("CRM_PROVIDER"):
        raise HTTPException(503, "sin salida a CRM: proveedor no elegido ni base/acuerdo/retención definidos")
    _require_me(authorization)
    raise HTTPException(503, "CRM no configurado para producción")


@app.post("/analytics/event")
def analytics_event(body: dict):
    name = str(body.get("name", "desconocido"))[:40]
    ANALYTICS[name] = ANALYTICS.get(name, 0) + 1
    return {"ok": True, "agregado": {name: ANALYTICS[name]},
            "nota": "analítica agregada sin datos personales"}


def _umbrales():
    return json.loads((BASE / "packages/content/umbrales.json").read_text(encoding="utf-8"))["umbrales"]


def _aprobaciones():
    return json.loads((BASE / "packages/content/aprobaciones.json").read_text(encoding="utf-8"))


def _profesional_activo(funcion: str | None = None, cultivo: str | None = None, ambito: str | None = None) -> dict:
    import datetime as _dt
    from packages.simulator.engine import MODEL_VERSION as _MV
    from packages.validation import aprobacion_valida
    hoy = _dt.date.today().isoformat()
    params_v = PARAMS.get("version")
    for a in _aprobaciones().get("aprobaciones", []):
        if funcion and a.get("funcion") != funcion:
            continue
        if cultivo and a.get("cultivo") != cultivo:
            continue
        if ambito and a.get("ambito") != ambito:
            continue
        key = f"{a.get('funcion')}|{a.get('cultivo')}|{a.get('ambito')}"
        informe = VALIDATION_REPORTS.get(key)
        ok, motivos = aprobacion_valida(a, informe, _MV, params_v, hoy)
        if ok:
            return {"activo": True, "aprobacion": a, "informe": informe}
    return {"activo": False, "profesional": "desactivado",
            "nota": "sin aprobación válida vinculada a informe reproducible no hay modo profesional; el juego no se bloquea"}


@app.get("/validation/protocolo")
def validation_protocolo():
    return {"protocolo": (BASE / "docs/evidence/PROTOCOLO_VALIDACION.md").read_text(encoding="utf-8")[:4000],
            "umbrales": _umbrales(),
            "nota": "umbrales pendientes bloquean aprobación; no inventar precisiones"}


@app.post("/validation/run")
def validation_run(authorization: str | None = Header(default=None)):
    _require_me(authorization)
    import csv
    f = BASE / "data/validation/ejemplo_sintetico.csv"
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    for r in rows:
        for k in ("cosecha_medida_kg", "cosecha_predicha_mid_kg", "cosecha_predicha_low_kg",
                  "cosecha_predicha_high_kg", "estres_obs", "estres_pred"):
            try:
                r[k] = float(r[k])
            except Exception:
                r[k] = None
    from packages.validation import (comparar_con_base, sesgo, cobertura_intervalos,
        sensibilidad_especificidad, separar_calibracion_prueba, comprobar_fuga, informe_reproducible)
    from packages.simulator.engine import MODEL_VERSION
    cal, pru = separar_calibracion_prueba(rows, {"FINCA-RESERVA"}, {"2026-27"})
    fugas = comprobar_fuga(cal, pru)
    base = pru if pru else rows
    obs = [r["cosecha_medida_kg"] for r in base]
    pred = [r["cosecha_predicha_mid_kg"] for r in base]
    import statistics
    media_cal = statistics.mean([r["cosecha_medida_kg"] for r in cal]) if cal else 0
    metricas = {"comparacion": comparar_con_base(obs, pred, [media_cal] * len(obs)),
                "sesgo": sesgo(obs, pred),
                "cobertura": cobertura_intervalos(obs, [r["cosecha_predicha_low_kg"] for r in base],
                                                  [r["cosecha_predicha_high_kg"] for r in base]),
                "estres": sensibilidad_especificidad([int(r["estres_obs"]) for r in base],
                                                     [int(r["estres_pred"]) for r in base])}
    params_v = json.loads((BASE / "packages/content/default_game_params.json").read_text(encoding="utf-8"))["version"]
    inf = informe_reproducible("ejemplo_sintetico.csv", rows, metricas, fugas, MODEL_VERSION, params_v, _umbrales())
    # Ejemplo sintético: sin autorización ni revisión → nunca aprobable; se guarda para auditar la barrera
    VALIDATION_REPORTS["riego|aguacate|costa"] = inf
    return inf


class ApprovalBody(BaseModel):
    funcion: str
    cultivo: str
    ambito: str
    codigo_version: str
    params_version: str
    caducidad: str
    responsable_agronomico: str
    responsable_producto: str
    seguimiento: str = ""
    criterio_retirada: str = ""
    dataset_id: str = ""
    permiso_ref: str = ""
    revision_independiente: bool = False
    revisor_independiente: str = ""


VALIDATION_REPORTS: dict[str, dict] = {}


@app.get("/approvals")
def approvals_list():
    return _aprobaciones()


@app.post("/approvals")
def approvals_add(body: ApprovalBody, authorization: str | None = Header(default=None)):
    _require_me(authorization)
    if not body.responsable_agronomico or not body.responsable_producto:
        raise HTTPException(422, "exige firma de responsable agronómico y de producto")
    if body.responsable_agronomico == body.responsable_producto:
        raise HTTPException(422, "firmas no independientes")
    if body.caducidad <= dt.date.today().isoformat():
        raise HTTPException(422, "caducidad debe ser futura")
    if not body.permiso_ref or not body.dataset_id:
        raise HTTPException(422, "exige dataset_id y permiso_ref verificables")
    if not body.revision_independiente or not body.revisor_independiente:
        raise HTTPException(422, "exige revisión independiente con revisor declarado")
    if body.revisor_independiente == body.responsable_agronomico:
        raise HTTPException(422, "revisor independiente coincide con quien calibró")
    # Persiste como borrador: solo activa si hay informe reproducible vinculado que cumpla todo
    data = _aprobaciones()
    reg = {**body.model_dump(), "fecha_registro": dt.date.today().isoformat(), "estado": "borrador"}
    data["aprobaciones"].append(reg)
    (BASE / "packages/content/aprobaciones.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"registrado": reg,
            "profesional": "desactivado",
            "nota": "borrador guardado; sin informe reproducible que cumpla umbrales no hay activación"}


@app.get("/professional/status")
def professional_status(funcion: str | None = None, cultivo: str | None = None, ambito: str | None = None):
    return _profesional_activo(funcion, cultivo, ambito)


@app.get("/monitoring/health")
def monitoring_health():
    try:
        from services.api import monitoring as MON
    except ImportError:
        import monitoring as MON  # type: ignore
    return MON.estado()


class TwinImport(BaseModel):
    finca_id: str
    owner_id: str
    permiso_ref: str
    limites: dict = {}


class TwinSensor(BaseModel):
    sensor_id: str
    finca_id: str
    magnitud: str
    unidad: str
    frecuencia_s: int = 3600
    calibrado: str = ""


class TwinIngest(BaseModel):
    sensor_id: str
    fecha: str
    valor: float


class TwinCompare(BaseModel):
    finca_id: str
    predicciones: list[float]
    mediciones: list[float]
    umbral: float | None = None


@app.post("/twin/import")
def twin_import(body: TwinImport, authorization: str | None = Header(default=None)):
    _require_me(authorization)
    from packages.twin import importar_finca
    try:
        return importar_finca(body.finca_id, body.owner_id, body.permiso_ref, body.limites)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/twin/sensor")
def twin_sensor(body: TwinSensor, authorization: str | None = Header(default=None)):
    _require_me(authorization)
    from packages.twin import registrar_sensor
    return registrar_sensor(body.sensor_id, body.finca_id, body.magnitud, body.unidad,
                            body.frecuencia_s, body.calibrado)


@app.post("/twin/ingest")
def twin_ingest(body: TwinIngest, authorization: str | None = Header(default=None)):
    _require_me(authorization)
    from packages.twin import ingerir
    try:
        return ingerir(body.sensor_id, body.fecha, body.valor)
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.post("/twin/compare")
def twin_compare(body: TwinCompare, authorization: str | None = Header(default=None)):
    _require_me(authorization)
    from packages.twin import comparar
    return comparar(body.finca_id, body.predicciones, body.mediciones, body.umbral)


@app.post("/twin/kill")
def twin_kill(finca_id: str, recomendacion: str, desactivar: bool = True,
              authorization: str | None = Header(default=None)):
    _require_me(authorization)
    from packages.twin import kill_switch
    return kill_switch(finca_id, recomendacion, desactivar)


@app.get("/launch/checklist")
def launch_checklist():
    return {
        "puerta": "ensayo",
        "checklist": ["0 incidencias críticas", "riesgos y experimental visibles",
                      "revisiones legal+agronómica del alcance publicado",
                      "PWA instalable", "offline probado", "costes APIs revisados", "soporte listo"],
        "estado": "pendiente (revisiones legal/agronómica no completadas para producción)",
        "nota": "sin checklist aprobada no hay lanzamiento",
    }


@app.get("/health")
def health():
    return {"ok": True, "modo_profesional": "desactivado",
            "db_configurada": bool(database_configured()), "db_activa": bool(_DB_OK)}
