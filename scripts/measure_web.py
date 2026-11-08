"""Mide tamaño inicial web y objetivos POCO M7 Pro. Sin secretos."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "apps" / "web"
print("fuente_tsx=", sorted([p.name for p in (ROOT / "src").glob("*.tsx")]))
src_kb = sum(p.stat().st_size for p in ROOT.rglob("*") if p.suffix in (".ts", ".tsx", ".html", ".css") and "node_modules" not in p.parts and "dist" not in p.parts) / 1024
print(f"fuente_kb={src_kb:.1f}")
dist = ROOT / "dist"
if dist.exists():
    total = sum(p.stat().st_size for p in dist.rglob("*") if p.is_file()) / 1024
    js = sum(p.stat().st_size for p in dist.rglob("*.js") if p.is_file()) / 1024
    gzip_est = js * 0.35
    print(f"dist_kb={total:.1f} js_kb={js:.1f} js_gzip_est_kb={gzip_est:.1f} objetivo_js_inicial_lt_200={'SI' if gzip_est < 200 else 'NO (revisar)'})")
else:
    print("dist=ausente (ejecutar npm run build en apps/web)")
print("objetivos=60fps, tap>=44px, texto>=14sp, TTI<3s 4G débil, POCO M7 Pro 1080x2400 120Hz; prueba real en dispositivo pendiente")
