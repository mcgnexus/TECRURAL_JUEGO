# Motor TecRural — puro, sin red ni reloj global. Fases 3-5: agua, cultivos/economía, nutrición/sanidad (juego).
# Todo etiquetado JUEGO/EXPERIMENTAL. Profesional desactivado. Sin derechos reales de agua.
# Fase 4: fenología juego, producción por intervalos, inventario/lotes, costes, deuda opcional, canales.
# Fase 5: registro análisis/fertilizantes como datos, balance N juego (NO diagnóstico), plagas juego,
#   tratamientos profesionales BLOQUEADOS (requieren MAPA+técnico).
# Balance por zona radicular (mm):
#   S_final = S_inicial + lluvia_efectiva + riego_infiltrado - ET_real - drenaje
# Infraestructura (m3):
#   R_final = min(R_max, R_inicial + aporte) - bombeo_total ; desborde = max(0, R_inicial + aporte - R_max)
#   bombeo parcela = aplicada_mm * area_ha * 10
#   entregada parcela = bombeo * eficiencia_red ; infiltrada_mm = aplicada_mm * eficiencia_red * eficiencia_aplicacion
#   perdidas_red = bombeo - entregada
# Todo etiquetado JUEGO/EXPERIMENTAL. Sin derechos reales de agua: dotaciones ficticias configurables.
from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from typing import Literal

MODEL_VERSION = "sim-0.3.0"
SCHEMA_VERSION = 3

# Tolerancias numéricas fijadas (Fase 3). Verificación pre-redondeo.
MASS_TOL_MM = 1e-9
MASS_TOL_M3 = 1e-9
# Tras redondeo de exhibición (suelo 2 dec, depósito 1 dec) el descuadre máximo
# documentado es 0.02 (mm o m3). Ver docs/evidence/METODOS_AGUA.md.
STORED_TOL = 0.02

CropKind = Literal["aguacate", "mango", "chirimoyo"]
WaterSourceKind = Literal["observacion", "pronostico", "estimacion", "simulado"]


@dataclass
class WeatherDay:
    date: str  # ISO YYYY-MM-DD
    precip_mm: float
    et0_mm: float
    tmin_c: float = 15.0
    tmax_c: float = 25.0
    kind: WaterSourceKind = "simulado"
    station_id: str = "ficticia-costa-tropical"
    station_distance_km: float | None = None


@dataclass
class ParcelAction:
    irrigation_mm: float = 0.0  # lámina solicitada en parcela
    fertilize_abstract: bool = False  # abstracta, sin dosis real
    prune: bool = False
    scout: bool = False
    harvest: bool = False
    sell_kg: float | None = None  # None = auto-vender lo cosechado (compat. F1-3); 0 = guardar en inventario
    channel: str = "base"  # canal de venta juego: base|cooperativa|mercado (modificadores juego)
    fertilizer_id: str | None = None  # producto juego de catálogo, sin recomendación real
    fertilizer_kg: float = 0.0
    spray_id: str | None = None  # siempre bloqueado: profesional desactivado


@dataclass
class ParcelState:
    id: str
    crop: str
    variety: str = "sin-documentar"
    planting_year: int = 2018
    density_trees_ha: float = 400.0
    area_ha: float = 1.0
    soil_water_mm: float = 40.0  # almacenamiento zona radicular
    max_storage_mm: float = 80.0
    health_0_1: float = 0.9
    phenology: str = "produccion"
    pending_fruit_kg: float = 500.0
    cum_costs_eur: float = 0.0
    cum_yield_kg: float = 0.0
    inventory_kg: float = 0.0  # Fase 4: stock sin vender (lotes)
    cum_income_eur: float = 0.0
    cum_n_kg: float = 0.0  # Fase 5: balance N juego acumulado, NO diagnóstico
    last_pest_obs: str = ""  # última observación juego, no diagnóstico


@dataclass
class SimState:
    schema_version: int = SCHEMA_VERSION
    day: str = "2026-01-01"
    cash_eur: float = 5000.0
    reservoir_m3: float = 200.0
    reservoir_max_m3: float = 500.0
    parcels: list[ParcelState] = field(default_factory=list)
    difficulty: str = "normal"
    realism: str = "simplificado"
    cum_pumped_m3: float = 0.0
    cum_inflow_m3: float = 0.0
    cum_energy_kwh: float = 0.0
    cum_overflow_m3: float = 0.0
    debt_eur: float = 0.0  # Fase 4: deuda opcional juego
    cum_income_eur: float = 0.0
    cum_fixed_eur: float = 0.0


def mm_to_m3(mm: float, area_ha: float) -> float:
    """1 mm sobre 1 ha = 10 m3."""
    return mm * area_ha * 10.0


def m3_to_mm(m3: float, area_ha: float) -> float:
    return m3 / (area_ha * 10.0) if area_ha > 0 else 0.0


def infra_params(parameters: dict) -> dict:
    """Configuración de infraestructura de juego. Sin derechos reales de agua."""
    ig = parameters.get("infra_game", {}) if isinstance(parameters, dict) else {}
    if not isinstance(ig, dict):
        ig = {}
    return {
        "supply_inflow_m3_day": float(ig.get("supply_inflow_m3_day", 8.0)),
        "pump_capacity_m3_day": float(ig.get("pump_capacity_m3_day", 60.0)),
        "supply_max_m3_day": float(ig.get("supply_max_m3_day", 50.0)),
        "network_efficiency": float(ig.get("network_efficiency", 0.92)),
        "energy_kwh_per_m3": float(ig.get("energy_kwh_per_m3", 0.4)),
        "energy_eur_per_kwh": float(ig.get("energy_eur_per_kwh", 0.25)),
        "breakdown_prob_per_day": float(ig.get("breakdown_prob_per_day", 0.02)),
    }


def crops_params(parameters: dict) -> dict:
    cg = parameters.get("crops_game", {}) if isinstance(parameters, dict) else {}
    return cg if isinstance(cg, dict) else {}


def economy_params(parameters: dict) -> dict:
    eg = parameters.get("economy_game", {}) if isinstance(parameters, dict) else {}
    if not isinstance(eg, dict):
        eg = {}
    return {
        "fixed_eur_per_ha_day": float(eg.get("fixed_eur_per_ha_day", 0.0)),
        "channel_mod": dict(eg.get("channel_mod", {"base": 1.0, "cooperativa": 0.95, "mercado": 1.1})),
        "debt_daily_interest": float(eg.get("debt_daily_interest", 0.0002)),
        "max_kg_per_tree": float(eg.get("max_kg_per_tree", 120.0)),
        "loss_frac": float(eg.get("loss_frac", 0.05)),
    }


def nutrition_products(parameters: dict) -> dict:
    ng = parameters.get("nutrition_game", {}) if isinstance(parameters, dict) else {}
    prods = ng.get("products", {}) if isinstance(ng, dict) else {}
    return prods if isinstance(prods, dict) else {}


# Fenología juego por especie (mes-día → etapa). JUEGO, no calendario real validado.
PHENO_GAME = {
    "aguacate": [((1, 1), (2, 28), "reposo"), ((3, 1), (5, 31), "floracion"),
                 ((6, 1), (8, 31), "cuajado"), ((9, 1), (2, 28), "cosecha")],
    "mango": [((1, 1), (2, 15), "reposo"), ((2, 16), (4, 30), "floracion"),
              ((5, 1), (7, 31), "cuajado"), ((8, 1), (10, 31), "cosecha"),
              ((11, 1), (12, 31), "reposo")],
    "chirimoyo": [((1, 1), (3, 31), "reposo"), ((4, 1), (6, 15), "floracion"),
                  ((6, 16), (8, 31), "cuajado"), ((9, 1), (11, 30), "cosecha"),
                  ((12, 1), (12, 31), "reposo")],
}


def phenology_stage(crop: str, date_iso: str) -> str:
    """Etapa fenológica juego según calendario. Sin valor agronómico real."""
    try:
        import datetime as _dt
        d = _dt.date.fromisoformat(date_iso)
        md = (d.month, d.day)
        for (m1, d1), (m2, d2), stage in PHENO_GAME.get(crop, []):
            if (m1, d1) <= (m2, d2):
                if (m1, d1) <= md <= (m2, d2):
                    return stage
            else:  # cruza año (aguacate cosecha)
                if md >= (m1, d1) or md <= (m2, d2):
                    return stage
    except Exception:
        pass
    return "produccion"


def age_factor(planting_year: int, date_iso: str) -> float:
    """Factor rendimiento por edad, juego: joven<5:0.5, adulto 5-25:1.0, viejo>25:0.7."""
    try:
        age = int(date_iso[:4]) - int(planting_year)
    except Exception:
        return 1.0
    if age < 5:
        return 0.5
    if age > 25:
        return 0.7
    return 1.0


def forecast_interval(parcel: ParcelState, parameters: dict, date_iso: str) -> dict:
    """Previsión juego por intervalos (no profesional). Devuelve low/mid/high kg."""
    af = age_factor(parcel.planting_year, date_iso)
    mid = max(0.0, parcel.pending_fruit_kg * 0.5 * parcel.health_0_1 * af)
    return {"low_kg": round(mid * 0.7, 1), "mid_kg": round(mid, 1), "high_kg": round(mid * 1.3, 1),
            "evidence_level": "juego", "nota": "orientativo, profesional desactivado"}


def _validate_ranges(state: SimState, actions: dict[str, ParcelAction], weather: WeatherDay) -> list[str]:
    errors: list[str] = []
    if weather.precip_mm < 0 or weather.precip_mm > 500:
        errors.append(f"precip_mm fuera de rango físico: {weather.precip_mm}")
    if weather.et0_mm < 0 or weather.et0_mm > 15:
        errors.append(f"et0_mm fuera de rango físico: {weather.et0_mm}")
    for p in state.parcels:
        a = actions.get(p.id, ParcelAction())
        if a.irrigation_mm < 0 or a.irrigation_mm > 100:
            errors.append(f"riego fuera de rango 0-100 mm en {p.id} (restricción de interfaz, juego)")
        if p.area_ha < 0.1 or p.area_ha > 10:
            errors.append(f"superficie fuera de rango 0.1-10 ha en {p.id} (restricción de interfaz, juego)")
        if a.sell_kg is not None and (a.sell_kg < 0 or a.sell_kg > 50000):
            errors.append(f"venta fuera de rango 0-50000 kg en {p.id} (juego)")
        if a.fertilizer_kg < 0 or a.fertilizer_kg > 2000:
            errors.append(f"fertilizante fuera de rango 0-2000 kg en {p.id} (juego)")
        if a.channel not in ("base", "cooperativa", "mercado"):
            errors.append(f"canal desconocido {a.channel} en {p.id} (juego: base|cooperativa|mercado)")
    return errors


def step(
    state: SimState,
    actions: dict[str, ParcelAction],
    weather: WeatherDay,
    parameters: dict,
    rng_seed: int,
) -> dict:
    """Un paso diario puro y determinista. No hace red ni usa reloj global."""
    errs = _validate_ranges(state, actions, weather)
    if errs:
        raise ValueError("; ".join(errs))

    rng = random.Random(f"{rng_seed}:{weather.date}")
    pset_version = str(parameters.get("version", "game-0.3"))
    events: list[dict] = []
    ledger: list[dict] = []  # libro de entradas y salidas (juego)

    # Parámetros EXPLÍCITOS DE JUEGO — no son prácticas reales.
    runoff_coef = float(parameters.get("runoff_coef", 0.15))
    irr_efficiency = float(parameters.get("irrigation_efficiency", 0.85))
    kc = parameters.get("kc_game", {"aguacate": 0.8, "mango": 0.75, "chirimoyo": 0.7})
    price = parameters.get("price_eur_kg_game", {"aguacate": 2.2, "mango": 1.6, "chirimoyo": 2.8})
    cost = parameters.get("costs_eur_game", {"irrigation_eur_per_m3": 0.25, "labor_day_eur": 60.0})
    infra = infra_params(parameters)
    eco = economy_params(parameters)
    prods = nutrition_products(parameters)
    water_eur_m3 = float(cost.get("irrigation_eur_per_m3", 0.25) if isinstance(cost, dict) else 0.25)
    cash_prev = state.cash_eur
    total_costs = 0.0
    total_income = 0.0

    inflow = max(0.0, infra["supply_inflow_m3_day"])
    res_after_inflow = state.reservoir_m3 + inflow
    overflow = max(0.0, res_after_inflow - state.reservoir_max_m3)
    res_available = min(res_after_inflow, state.reservoir_max_m3)
    ledger.append({"tipo": "aporte", "m3": round(inflow, 3), "nota": "juego: dotación configurable, sin derecho real"})
    if overflow > 0:
        ledger.append({"tipo": "desborde", "m3": round(overflow, 3), "nota": "juego: aporte sobre capacidad vertido"})
        events.append({"type": "desborde", "m3": round(overflow, 1), "nota": "juego"})

    # Solicitado por parcela
    requested: dict[str, float] = {}
    for p in state.parcels:
        a = actions.get(p.id, ParcelAction())
        requested[p.id] = mm_to_m3(a.irrigation_mm, p.area_ha)
    total_requested = sum(requested.values())

    # Consistencia caja y depósito (juego): el riego pedido debe caber en lo disponible tras aporte.
    if total_requested > res_available + 1e-9:
        raise ValueError(
            f"agua insuficiente: piden {total_requested:.0f} m³ y hay {res_available:.0f} m³ tras aporte (juego)")
    est_energy_kwh = total_requested * infra["energy_kwh_per_m3"]
    est_cost = total_requested * water_eur_m3 + est_energy_kwh * infra["energy_eur_per_kwh"]
    # Estimación fertilizantes juego (sin recomendación real)
    for p in state.parcels:
        a = actions.get(p.id, ParcelAction())
        if a.fertilizer_kg > 0 and a.fertilizer_id in prods:
            est_cost += float(a.fertilizer_kg) * float(prods[a.fertilizer_id].get("eur_per_kg", 1.0))
    if est_cost > state.cash_eur + 1e-9:
        raise ValueError(f"caja insuficiente: riego cuesta {est_cost:.2f} € y hay {state.cash_eur:.2f} € (juego)")

    # Avería de juego (determinista por semilla+fecha)
    averia = rng.random() < infra["breakdown_prob_per_day"]
    if averia:
        allowed_total = 0.0
        events.append({"type": "averia", "m3": 0, "nota": "juego: bombeo detenido hoy, riego pendiente"})
    else:
        cap = min(infra["pump_capacity_m3_day"], infra["supply_max_m3_day"])
        allowed_total = min(total_requested, max(0.0, cap))
    if not averia and allowed_total < total_requested - 1e-9:
        motivo = "bombeo" if infra["pump_capacity_m3_day"] <= infra["supply_max_m3_day"] else "suministro"
        events.append({"type": f"{motivo}_limitado",
                       "solicitado_m3": round(total_requested, 1), "aplicado_m3": round(allowed_total, 1),
                       "nota": "juego: prorrateo proporcional, resto pendiente"})
    factor = (allowed_total / total_requested) if total_requested > 1e-12 else 0.0

    total_pumped = 0.0
    total_energy = 0.0
    for p in state.parcels:
        a = actions.get(p.id, ParcelAction())
        req_mm = a.irrigation_mm
        applied_mm = req_mm * factor  # prorrateo proporcional determinista
        pumped_m3 = mm_to_m3(applied_mm, p.area_ha)
        total_pumped += pumped_m3
        delivered_m3 = pumped_m3 * infra["network_efficiency"]
        network_loss_m3 = pumped_m3 - delivered_m3
        irr_infiltrated_mm = applied_mm * infra["network_efficiency"] * irr_efficiency
        energy_kwh = pumped_m3 * infra["energy_kwh_per_m3"]
        total_energy += energy_kwh

        # Fase 4: fenología juego + coherencia ha/árboles/rendimiento
        p.phenology = phenology_stage(p.crop, weather.date)
        trees = p.area_ha * p.density_trees_ha
        max_pending = trees * eco["max_kg_per_tree"]
        if p.pending_fruit_kg > max_pending + 1e-9:
            events.append({"type": "coherencia_limitada", "parcel": p.id,
                           "pendiente_kg": p.pending_fruit_kg, "max_kg": round(max_pending, 1),
                           "nota": "juego: tope árboles×kg/árbol, exceso recortado"})
            p.pending_fruit_kg = round(max_pending, 1)

        k = float(kc.get(p.crop, 0.75)) if isinstance(kc, dict) else 0.75
        rain_eff = max(0.0, weather.precip_mm * (1.0 - runoff_coef))
        etc_mm = weather.et0_mm * k
        soil_ratio = p.soil_water_mm / max(p.max_storage_mm, 1e-6)
        stress = max(0.3, min(1.0, soil_ratio * 1.5))  # regla de juego explícita
        et_real = min(etc_mm * stress, p.soil_water_mm + rain_eff + irr_infiltrated_mm)

        s_prev = p.soil_water_mm
        s = s_prev + rain_eff + irr_infiltrated_mm - et_real
        drainage = max(0.0, s - p.max_storage_mm)
        s_new = min(s, p.max_storage_mm)
        runoff = weather.precip_mm * runoff_coef
        # Conservación de masa por parcela (pre-redondeo)
        imbalance = s_prev + rain_eff + irr_infiltrated_mm - et_real - drainage - s_new
        if abs(imbalance) > MASS_TOL_MM:
            raise AssertionError(f"descuadre masa suelo {p.id}: {imbalance}")
        p.soil_water_mm = round(max(0.0, s_new), 2)

        ledger.append({"tipo": "bombeo", "parcela": p.id, "m3": round(pumped_m3, 3),
                       "mm_solicitados": req_mm, "mm_aplicados": round(applied_mm, 3)})
        if network_loss_m3 > 1e-12:
            ledger.append({"tipo": "perdidas_red", "parcela": p.id, "m3": round(network_loss_m3, 3)})
        ledger.append({"tipo": "infiltrado", "parcela": p.id, "mm": round(irr_infiltrated_mm, 3)})
        ledger.append({"tipo": "lluvia_efectiva", "parcela": p.id, "mm": round(rain_eff, 3)})
        ledger.append({"tipo": "escorrentia", "parcela": p.id, "mm": round(runoff, 3)})
        ledger.append({"tipo": "drenaje", "parcela": p.id, "mm": round(drainage, 3)})
        ledger.append({"tipo": "ET_real", "parcela": p.id, "mm": round(et_real, 3)})

        # Costes de juego: agua + energía + fijo + fertilizante + mano de obra abstracta
        water_cost = pumped_m3 * water_eur_m3
        energy_cost = energy_kwh * infra["energy_eur_per_kwh"]
        fixed_cost = p.area_ha * eco["fixed_eur_per_ha_day"]
        fert_cost = 0.0
        n_add = 0.0
        if a.fertilizer_kg > 0 or a.fertilizer_id:
            if not a.fertilizer_id or a.fertilizer_id not in prods:
                raise ValueError(f"fertilizante desconocido {a.fertilizer_id} en {p.id} (juego: ver catálogo)")
            prod = prods[a.fertilizer_id]
            fert_cost = float(a.fertilizer_kg) * float(prod.get("eur_per_kg", 1.0))
            n_add = float(a.fertilizer_kg) * float(prod.get("n_frac", 0.0))
            p.cum_n_kg = round(p.cum_n_kg + n_add, 3)
            ledger.append({"tipo": "fertilizante", "parcela": p.id, "producto": a.fertilizer_id,
                           "kg": a.fertilizer_kg, "n_kg": round(n_add, 3),
                           "nota": "juego: aporte registrado, NO es diagnóstico foliar"})
            events.append({"type": "fertilizacion", "parcel": p.id, "producto": a.fertilizer_id,
                           "kg": a.fertilizer_kg, "coste_eur": round(fert_cost, 2),
                           "nota": "juego orientativo: sin análisis no hay dosis válida"})
        day_cost = water_cost + energy_cost + fixed_cost + fert_cost
        if a.prune or a.scout or a.fertilize_abstract or a.fertilizer_kg > 0:
            day_cost += 20.0  # mano de obra abstracta de juego
        if pumped_m3 > 1e-12:
            events.append({"type": "riego", "parcel": p.id, "mm": round(applied_mm, 2),
                           "mm_solicitados": req_mm, "m3": round(pumped_m3, 1),
                           "perdidas_red_m3": round(network_loss_m3, 2),
                           "energia_kwh": round(energy_kwh, 2),
                           "coste_eur": round(water_cost + energy_cost, 2),
                           "nota": "juego: lámina×superficie×10 con pérdidas de red y aplicación"})
        if day_cost >= 20.0 and (a.prune or a.scout or a.fertilize_abstract or a.fertilizer_kg > 0):
            acts = [k for k, v in {"poda": a.prune, "vigilancia": a.scout, "abono_abstracto": a.fertilize_abstract,
                                    "abono_registrado": a.fertilizer_kg > 0}.items() if v]
            events.append({"type": "labor", "parcel": p.id, "tareas": acts, "coste_eur": 20.0,
                           "nota": "juego: coste abstracto, sin dosis real"})
        p.cum_costs_eur = round(p.cum_costs_eur + day_cost, 2)
        total_costs += day_cost

        # Sanidad juego (no diagnóstico real). Inspección genera observación probabilística sin calibrar.
        if soil_ratio < 0.25:
            p.health_0_1 = round(max(0.2, p.health_0_1 - 0.03), 3)
            events.append({"type": "estres_hidrico", "parcel": p.id, "level": "juego"})
        if a.scout:
            events.append({"type": "vigilancia", "parcel": p.id, "nota": "información general, no diagnóstico"})
            if rng.random() < 0.15:  # probabilidad juego sin calibrar
                obs = rng.choice(["pulgon_juego", "arana_roja_juego", "mosca_fruta_juego"])
                p.last_pest_obs = obs
                events.append({"type": "observacion_plaga", "parcel": p.id, "plaga": obs,
                               "nota": "juego: probabilidad sin calibrar, aviso ≠ diagnóstico"})
        # Fase 5: cualquier intento de tratamiento se bloquea (profesional desactivado)
        if a.spray_id:
            events.append({"type": "tratamiento_bloqueado", "parcel": p.id, "producto": a.spray_id,
                           "nota": "bloqueado: requiere registro MAPA vigente + uso autorizado + técnico competente"})

        # Cosecha juego → inventario por lotes → venta (sin vender lo inexistente)
        harvested = 0.0
        income = 0.0
        if a.harvest and p.pending_fruit_kg > 0:
            af = age_factor(p.planting_year, weather.date)
            gross = p.pending_fruit_kg * 0.5 * p.health_0_1 * af
            loss = gross * eco["loss_frac"]
            harvested = round(gross - loss, 1)
            p.pending_fruit_kg = round(max(0.0, p.pending_fruit_kg - gross), 1)
            p.cum_yield_kg = round(p.cum_yield_kg + harvested, 1)
            p.inventory_kg = round(p.inventory_kg + harvested, 1)
            # Exportación N juego (0.002 kg N por kg fruta)
            p.cum_n_kg = round(p.cum_n_kg - harvested * 0.002, 3)
            lote = f"{weather.date}-{p.id}-{rng_seed}"
            if harvested > 0:
                events.append({"type": "cosecha", "parcel": p.id, "kg": harvested, "lote": lote,
                               "merma_kg": round(loss, 1),
                               "nota": "juego: lote a inventario, calidad/merma supuestas"})
            p.pending_fruit_kg = round(p.pending_fruit_kg + 100.0, 1)
            ledger.append({"tipo": "rebrote", "parcela": p.id, "kg": 100.0,
                           "nota": "juego: entrada explícita de fruta, no creación espontánea"})
        # Venta: None+harvest = auto-vender lo cosechado (compat. F1-3); número = vender hasta stock
        sell_qty = 0.0
        if a.harvest and a.sell_kg is None:
            sell_qty = harvested
        elif a.sell_kg is not None and float(a.sell_kg) > 0:
            sell_qty = min(float(a.sell_kg), p.inventory_kg)
            if float(a.sell_kg) > p.inventory_kg + 1e-9:
                events.append({"type": "venta_parcial", "parcel": p.id,
                               "pedido_kg": float(a.sell_kg), "vendido_kg": round(sell_qty, 1),
                               "nota": "juego: sin existencias suficientes, no se vende lo inexistente"})
        if sell_qty > 1e-9:
            unit_base = float(price.get(p.crop, 1.5) if isinstance(price, dict) else 1.5)
            mod = float(eco["channel_mod"].get(a.channel, 1.0))
            unit = unit_base * mod * (1.0 + (rng.random() - 0.5) * 0.1)
            income = round(sell_qty * unit, 2)
            p.inventory_kg = round(max(0.0, p.inventory_kg - sell_qty), 1)
            p.cum_income_eur = round(p.cum_income_eur + income, 2)
            total_income += income
            state.cum_income_eur = round(state.cum_income_eur + income, 2)
            events.append({"type": "venta", "parcel": p.id, "kg": round(sell_qty, 1),
                           "canal": a.channel, "ingreso_eur": income,
                           "nota": "juego: precio escenario, no cotización garantizada"})

        state.cash_eur = round(state.cash_eur - day_cost + income, 2)
        state.cum_fixed_eur = round(state.cum_fixed_eur + fixed_cost, 2)

    # Deuda opcional juego: interés diario (sin préstamo real garantizado)
    if state.debt_eur > 1e-9:
        interest = round(state.debt_eur * eco["debt_daily_interest"], 2)
        state.debt_eur = round(state.debt_eur + interest, 2)
        state.cash_eur = round(state.cash_eur - interest, 2)
        total_costs += interest
        events.append({"type": "interes_deuda", "coste_eur": interest,
                       "nota": "juego: interés escenario, no contrato real"})
    # Conciliación caja juego (tolerancia redondeo 0.05)
    recon = cash_prev - total_costs + total_income - state.cash_eur
    if abs(recon) > 0.05:
        raise AssertionError(f"descuadre caja: {recon}")
    # Depósito: aporte - bombeo - desborde (sin recarga ficticia por lluvia)
    res_prev = state.reservoir_m3
    res_new = res_available - total_pumped
    imbalance_res = res_prev + inflow - overflow - total_pumped - res_new
    if abs(imbalance_res) > MASS_TOL_M3:
        raise AssertionError(f"descuadre masa depósito: {imbalance_res}")
    state.reservoir_m3 = round(max(0.0, min(state.reservoir_max_m3, res_new)), 1)
    state.cum_pumped_m3 = round(state.cum_pumped_m3 + total_pumped, 3)
    state.cum_inflow_m3 = round(state.cum_inflow_m3 + inflow, 3)
    state.cum_energy_kwh = round(state.cum_energy_kwh + total_energy, 3)
    state.cum_overflow_m3 = round(state.cum_overflow_m3 + overflow, 3)
    if total_pumped > state.reservoir_max_m3:
        events.append({"type": "riego_excesivo", "m3": total_pumped})

    indicators = {
        "cash_eur": state.cash_eur,
        "reservoir_m3": state.reservoir_m3,
        "soil_mm": {p.id: p.soil_water_mm for p in state.parcels},
        "pumped_m3": round(total_pumped, 2),
        "energy_kwh": round(total_energy, 2),
        "inflow_m3": round(inflow, 2),
        "overflow_m3": round(overflow, 2),
        "inventory_kg": {p.id: p.inventory_kg for p in state.parcels},
        "debt_eur": round(state.debt_eur, 2),
        "day_costs_eur": round(total_costs, 2),
        "day_income_eur": round(total_income, 2),
    }
    forecast = {p.id: forecast_interval(p, parameters, weather.date) for p in state.parcels}
    provenance = {
        "model_version": MODEL_VERSION,
        "parameter_set": pset_version,
        "evidence_level": "juego",
        "weather_kind": weather.kind,
        "weather_station": weather.station_id,
        "calculation_date": state.day,
        "data_date": weather.date,
        "units": {"agua": "mm", "volumen": "m3 (1mm/ha=10m3)", "dinero": "EUR", "energia": "kWh"},
        "limitations": "Juego orientativo, no recomendación real. Profesional desactivado. Humedad estimada, no medida. Precios escenarios, no cotizaciones. Aviso regional ≠ diagnóstico. Sin MAPA+técnico no hay tratamiento.",
        "rng_seed": rng_seed,
        "mass_tolerance": {"mm": MASS_TOL_MM, "m3": MASS_TOL_M3, "almacenado": STORED_TOL},
        "infra": infra,
        "economy": {"channel_mod": eco["channel_mod"], "fixed_per_ha": eco["fixed_eur_per_ha_day"]},
        "averia": averia,
        "profesional": "desactivado",
    }
    state.day = weather.date
    return {"state": asdict(state), "events": events, "indicators": indicators,
            "provenance": provenance, "water_ledger": ledger, "forecast": forecast,
            "mass_balance": {"tolerancia_mm": MASS_TOL_MM, "tolerancia_m3": MASS_TOL_M3, "ok": True,
                             "conciliacion_caja": round(recon, 4)}}


def step_week(state: SimState, actions: dict[str, ParcelAction], week: list[WeatherDay], parameters: dict, rng_seed: int) -> dict:
    """7 pasos diarios con mismas acciones programadas."""
    out = None
    for i, w in enumerate(week):
        out = step(state, actions, w, parameters, rng_seed + i)
        s = out["state"]
        state.cash_eur = s["cash_eur"]
        state.reservoir_m3 = s["reservoir_m3"]
        state.day = s["day"]
        state.cum_pumped_m3 = s.get("cum_pumped_m3", state.cum_pumped_m3)
        state.cum_inflow_m3 = s.get("cum_inflow_m3", state.cum_inflow_m3)
        state.cum_energy_kwh = s.get("cum_energy_kwh", state.cum_energy_kwh)
        state.cum_overflow_m3 = s.get("cum_overflow_m3", state.cum_overflow_m3)
        state.debt_eur = s.get("debt_eur", state.debt_eur)
        state.cum_income_eur = s.get("cum_income_eur", state.cum_income_eur)
        state.cum_fixed_eur = s.get("cum_fixed_eur", state.cum_fixed_eur)
        for ps, p in zip(s["parcels"], state.parcels):
            for k, v in ps.items():
                setattr(p, k, v)
    assert out is not None
    return out
