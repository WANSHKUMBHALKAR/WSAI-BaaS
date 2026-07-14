#!/usr/bin/env sh
set -e

echo "Starting backend entrypoint (ENVIRONMENT=${ENVIRONMENT:-development})"

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running alembic migrations..."
  alembic upgrade head
fi

exec "$@"
