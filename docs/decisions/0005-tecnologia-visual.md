# 0005 — Tecnología visual y dispositivo de referencia (Fase 0)

Fecha: 2026-11-08. Estado: decisión inicial medible.

Dispositivo referencia: POCO M7 Pro (gama media real): AMOLED 6.67" 1080×2400 (~395 ppp), 120 Hz, Dimensity 7025-Ultra, 8/12 GB RAM, Android 14/HyperOS. CSS aprox 412×915. Sirve como "estándar" de fluidez: si va bien aquí, va bien en la mayoría de gama media España.

Decisión: escena de prueba con Canvas 2D + SVG/DOM (cero dependencia pesada). PixiJS (MIT) queda como opción si la métrica lo exige (muchos árboles/animaciones). No se cierra tecnología hasta medir en dispositivo real.

Objetivos Fase 0 (revisar con prueba real):
- JS inicial < 200 KB gzip (sin PixiJS); PWA instalable, funciona con conexión débil.
- Interacción táctil ≥ 44 px, texto ≥ 14 sp, contraste AA, respuesta a tap < 100 ms.
- 60 fps en mapa (el panel es 120 Hz, pero 60 es el objetivo de juego).
- Medición: `scripts/measure_web.py` (tamaño dist) + prueba manual en POCO (fps, memoria, legibilidad). Sin prueba en dispositivo no se cierra.

Medido 2026-11-08 (Vite build): dist 145 KB, JS 144.7 KB, gzip real 48.25 KB → objetivo <200 KB: SÍ. Fuente propia 7.3 KB (React DOM). tsc sin errores. Fluidez/consumo en POCO real: pendiente prueba en dispositivo.
