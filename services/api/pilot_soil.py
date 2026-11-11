"""Parámetros de suelo de juego, no calibrados ni aptos para asesoramiento."""
import math

# Valores deliberadamente ficticios para diferenciar escenarios; no son tablas agronómicas.
CAPACITIES = {'desconocido': 80.0, 'otro': 80.0, 'arenoso': 50.0, 'franco': 80.0, 'arcilloso': 110.0}


def resolve_soil(texture: str, capacity_mm: float | None = None, initial_mm: float | None = None) -> dict:
    if texture not in CAPACITIES:
        raise ValueError('Tipo de suelo desconocido.')
    capacity = CAPACITIES[texture] if capacity_mm is None else capacity_mm
    initial = capacity * 0.5 if initial_mm is None else initial_mm
    if not math.isfinite(capacity) or not 1 <= capacity <= 500:
        raise ValueError('La capacidad debe estar entre 1 y 500 mm.')
    if not math.isfinite(initial) or not 0 <= initial <= capacity:
        raise ValueError('El agua inicial debe estar entre cero y la capacidad.')
    return {'texture': texture, 'capacity_mm': capacity, 'initial_mm': initial,
            'capacity_source': 'supuesto de juego no validado' if capacity_mm is None else 'introducido por el usuario, sin verificar',
            'initial_source': 'supuesto: 50 % de la capacidad' if initial_mm is None else 'introducido por el usuario, sin verificar'}
