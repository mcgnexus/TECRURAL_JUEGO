"""Informe reproducible Fase 7 desde CSV autorizado (o ejemplo sintético)."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.validation import (mae, rmse, sesgo, cobertura_intervalos,
    sensibilidad_especificidad, comparar_con_base, separar_calibracion_prueba,
    comprobar_fuga, informe_reproducible)

def main(fcsv="data/validation/ejemplo_sintetico.csv"):
    rows = list(csv.DictReader(Path(fcsv).open(encoding="utf-8")))
    for r in rows:
        for k in ("cosecha_medida_kg", "cosecha_predicha_mid_kg", "cosecha_predicha_low_kg",
                  "cosecha_predicha_high_kg", "estres_obs", "estres_pred"):
            try: r[k] = float(r[k]) if r[k] not in ("", None) else None
            except: r[k] = None
        r["edad_grupo"] = "joven" if (r.get("edad_anios") or "").isdigit() and int(r["edad_anios"]) < 5 else "adulto"
    cal, pru = separar_calibracion_prueba(rows, {"FINCA-RESERVA"}, {"2026-27"})
    fugas = comprobar_fuga(cal, pru)
    base = pru if pru else rows
    obs = [r["cosecha_medida_kg"] for r in base if r["cosecha_medida_kg"] is not None]
    pred = [r["cosecha_predicha_mid_kg"] for r in base if r["cosecha_medida_kg"] is not None]
    low = [r["cosecha_predicha_low_kg"] for r in base if r["cosecha_medida_kg"] is not None]
    high = [r["cosecha_predicha_high_kg"] for r in base if r["cosecha_medida_kg"] is not None]
    import statistics
    media_cal = statistics.mean([r["cosecha_medida_kg"] for r in cal if r["cosecha_medida_kg"] is not None]) if cal else 0
    m = {"comparacion": comparar_con_base(obs, pred, [media_cal] * len(obs)),
         "sesgo": sesgo(obs, pred), "cobertura": cobertura_intervalos(obs, low, high)}
    yt = [int(r["estres_obs"]) for r in base if r["estres_obs"] is not None]
    yp = [int(r["estres_pred"]) for r in base if r["estres_obs"] is not None]
    if yt: m["estres"] = sensibilidad_especificidad(yt, yp)
    from packages.simulator.engine import MODEL_VERSION
    umb = json.loads(Path("packages/content/umbrales.json").read_text(encoding="utf-8"))["umbrales"]
    params_v = json.loads(Path("packages/content/default_game_params.json").read_text(encoding="utf-8"))["version"]
    inf = informe_reproducible(Path(fcsv).name, rows, m, fugas, MODEL_VERSION, params_v, umb)
    # Prospectivo: fecha_prediccion < fecha en todas las filas
    inf["prospectivo_ok"] = all(r.get("fecha_prediccion", "") <= r.get("fecha", "") for r in rows if r.get("fecha"))
    print(json.dumps(inf, indent=2, ensure_ascii=False))
    return 0 if inf["aprobable"] else 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "data/validation/ejemplo_sintetico.csv"))
