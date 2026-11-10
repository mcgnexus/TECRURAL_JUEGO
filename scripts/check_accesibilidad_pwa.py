"""Accesibilidad/PWA Fase 8: comprobaciones estáticas mínimas."""
from pathlib import Path
errs = []
html = Path("apps/web/index.html").read_text(encoding="utf-8")
for s in ['lang="es"', 'name="viewport"', 'rel="manifest"', "<title>"]:
    if s not in html:
        errs.append(f"index.html falta {s}")
app = Path("apps/web/src/App.tsx").read_text(encoding="utf-8")
for s in ["aria-label", 'role="status"', 'role="alert"', "<button"]:
    if s not in app:
        errs.append(f"App.tsx falta {s}")
mani = Path("apps/web/public/manifest.webmanifest").read_text(encoding="utf-8")
for s in ['"name"', '"theme_color"', '"lang"']:
    if s not in mani:
        errs.append(f"manifest falta {s}")
print("ERRORES:" if errs else "ACCESIBILIDAD+PWA OK")
for e in errs:
    print("-", e)
raise SystemExit(1 if errs else 0)
