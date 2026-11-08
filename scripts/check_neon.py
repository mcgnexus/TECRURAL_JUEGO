"""Chequeo Neon sin exponer secretos: lee .env, conecta, verifica tablas."""
import os
from pathlib import Path

for line in Path(".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

print("db_configurada=", bool(os.getenv("DATABASE_URL")))
import psycopg

with psycopg.connect(os.getenv("DATABASE_URL"), autocommit=True) as c:
    with c.cursor() as cur:
        cur.execute("SELECT 1")
        print("select1=", cur.fetchone()[0])
        cur.execute(Path("services/api/schema.sql").read_text(encoding="utf-8"))
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname=%s AND tablename IN (%s,%s) ORDER BY 1",
            ("public", "games", "accounts"),
        )
        print("tablas=", [r[0] for r in cur.fetchall()])
print("neon_ok=True")
