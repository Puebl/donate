#!/bin/sh
set -e

echo "Syncing dependencies..."
uv sync --locked

echo "Running migrations..."
uv run alembic upgrade head

echo "Starting application..."
exec uv run uvicorn src.main:main_app --host 0.0.0.0 --port 8000 --reload
