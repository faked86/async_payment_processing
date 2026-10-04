#!/bin/sh

set -e

echo "Starting alembic migrations..."
alembic upgrade head

echo "Migrated successfully, starting app..."
exec uvicorn src.server.app:app --host 0.0.0.0 --port 8000
