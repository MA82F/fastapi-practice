#!/bin/bash
set -e

# echo "checking postgres is ready..."
# until nc -z "$DB_HOST" "$DB_PORT"; do
#   echo "Waiting for Postgres at $DB_HOST:$DB_PORT..."
#   sleep 10
# done
# echo "✅ postgres"

# echo "checking if redis is ready..."
# until nc -z "$REDIS_HOST" "$REDIS_PORT"; do
#   echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
#   sleep 3
# done
# echo "✅ redis"

echo "Running migrations..."
alembic upgrade heads

echo "starting fastapi app..."
exec fastapi run --host 0.0.0.0 --port 80