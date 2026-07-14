#!/usr/bin/env sh
set -e

echo "Starting backend entrypoint (ENVIRONMENT=${ENVIRONMENT:-development})"

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running alembic migrations..."
  if command -v alembic >/dev/null 2>&1; then
    alembic upgrade head
  else
    echo "alembic command not found; skipping migrations in this image"
  fi
fi

exec "$@"
