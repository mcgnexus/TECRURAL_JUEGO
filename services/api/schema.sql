-- Esquema TecRural como código (v1). Ejecutar con conexión directa para migraciones
-- serias; este DDL inicial es seguro en pooled con autocommit.
CREATE TABLE IF NOT EXISTS accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  label TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS games (
  id TEXT PRIMARY KEY,
  account_id UUID NULL REFERENCES accounts(id) ON DELETE SET NULL,
  ephemeral BOOLEAN NOT NULL DEFAULT TRUE,
  seed INTEGER NOT NULL DEFAULT 1234,
  state_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_games_account ON games(account_id);
