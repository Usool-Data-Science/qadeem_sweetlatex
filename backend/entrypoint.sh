#!/bin/sh
set -e

# ── Wait for PostgreSQL ───────────────────────────────────────────────────────
# Uses pg_isready which is more reliable than nc for Postgres health checks.
# DB_HOST and DB_PORT are set via env_file in docker-compose.
echo "Waiting for PostgreSQL at $DB_HOST:${DB_PORT:-5432}..."
until pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "${POSTGRES_USER:-postgres}" -q; do
  sleep 1
done
echo "PostgreSQL is ready."

# ── Database migrations ───────────────────────────────────────────────────────
echo "Running migrations..."
python manage.py migrate --noinput

# ── Create default admin ──────────────────────────────────────────────────────
python manage.py create_default_admin

# ── Static files ──────────────────────────────────────────────────────────────
echo "Collecting static files..."
python manage.py collectstatic --noinput

# ── ML bootstrap (first-run only) ────────────────────────────────────────────
# seed_rag: bulk-indexes all existing products into Pinecone via Celery tasks.
# Only runs when the Pinecone index is empty (idempotent — safe to restart).
# This fires tasks onto the `ml` Celery queue; celery_ml worker picks them up.
echo "Seeding RAG index (queues tasks — non-blocking)..."
python manage.py seed_rag --if-empty || echo "seed_rag skipped or not yet available."

echo "Starting server..."
exec "$@"