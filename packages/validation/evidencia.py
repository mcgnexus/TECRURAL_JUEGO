"""Auditoría de evidencia cultivos/sanidad (prioridad 2).

Sin fuente primaria nueva, todo sigue juego/experimental y los tratamientos
concretos bloqueados. Falla si aparece un 'validado' sin aprobación o un
producto con vigente True sin registro verificable.
"""
from __future__ import annotations
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]


def auditar_evidencia() -> dict:
    problemas: list[str] = []
    fichas = (BASE / "packages/content/fichas_parametros.md").read_text(encoding="utf-8")
    # Ninguna fila marcada validado con valor: el grado validado exige barrera (ninguno aún)
    for linea in fichas.splitlines():
        if "| validado |" in linea and "ninguno" not in linea.lower():
            problemas.append(f"grado validado sin barrera: {linea.strip()[:120]}")
    fitos = json.loads((BASE / "packages/content/fitosanitarios.json").read_text(encoding="utf-8"))
    for p in fitos.get("productos", []):
        if p.get("vigente"):
            problemas.append(f"producto vigente sin verificación: {p.get('id')}")
        if p.get("usos"):
            problemas.append(f"uso declarado sin confirmación: {p.get('id')}")
    raif_nota = (BASE / "docs/evidence/METODOS_NUTRICION_SANIDAD.md").read_text(encoding="utf-8")
    low = raif_nota.lower()
    if "diagnóstico" not in low or not any(s in raif_nota or s in low for s in
            ["≠", "nunca diagnóstico", "no es diagnóstico", "sin diagnóstico", "no diagnostico"]):
        problemas.append("falta aviso regional ≠ diagnóstico")
    return {"ok": not problemas, "problemas": problemas}
