# Guía de estilo TecRural juego (Fase 8) + catálogo de recursos

Identidad: verde campo #1a6b3c, fondo claro, tipografía sistema, botones ≥48px táctil.
Terreno isométrico Canvas 2D (POCO M7 Pro verificado Fase 0); cultivos por color+forma,
no solo color (accesibilidad). Agua en azul con etiqueta m³; maquinaria gris con icono;
feedback inmediato (riego/avería/cosecha) + historial. Incertidumbre siempre visible:
"estimado, no medido · juego orientativo".

## Catálogo (ver `packages/content/recursos.json`)
Todo recurso con licencia compatible; sin recurso sin licencia. Pantallas pequeñas
360px y conexión móvil 3G: build < 300 kB js, sin imágenes pesadas, offline primero.

## Accesibilidad mínima
`lang=es`, labels en formularios, foco visible, contraste AA, teclado completo,
lector de pantalla (roles status/alert), sin gestos como única vía.
