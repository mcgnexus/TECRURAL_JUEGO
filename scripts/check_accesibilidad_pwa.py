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
for s in ['"name"', '"theme_color"', '"lang"', '"icons"']:
    if s not in mani:
        errs.append(f"manifest falta {s}")
for f in ["apps/web/public/icon-512.svg", "apps/web/public/sw.js", "apps/web/.env.example"]:
    if not Path(f).exists():
        errs.append(f"falta {f}")
for s in ["VITE_API_URL", "Cuenta", "Guardar", "Previsi", "Historial", "sin garant"]:
    blob = app + Path("apps/web/src/main.tsx").read_text(encoding="utf-8")
    if s not in blob:
        errs.append(f"App.tsx/main falta {s}")
for s in ["profesional activado", "garantizado", "gemelo validado"]:
    if s in app.lower():
        errs.append(f"App promete de más: {s}")
if "serviceWorker" not in Path("apps/web/src/main.tsx").read_text(encoding="utf-8"):
    errs.append("main.tsx no registra SW")
print("ERRORES:" if errs else "ACCESIBILIDAD+PWA OK")
for e in errs:
    print("-", e)
raise SystemExit(1 if errs else 0)
