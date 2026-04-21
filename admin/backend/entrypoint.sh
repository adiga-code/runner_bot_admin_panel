#!/bin/sh
set -e

# Strip driver prefix to get the raw file path: ./data/mock.db
DB_PATH="${DATABASE_URL#sqlite+aiosqlite:///}"

# Ensure the parent directory exists (needed on first run with a volume)
mkdir -p "$(dirname "$DB_PATH")"

if [ ! -f "$DB_PATH" ]; then
  echo "[entrypoint] Database not found — running seed..."
  python seed.py
  echo "[entrypoint] Seed complete."
else
  echo "[entrypoint] Database already exists, skipping seed."
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
