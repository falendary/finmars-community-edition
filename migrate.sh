#!/bin/bash
set -e

echo "🚀 Starting Redis container..."
docker compose up -d redis

echo "🚀 Starting PostgreSQL container..."
docker compose up -d db

echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec $(docker compose ps -q db) pg_isready -U postgres > /dev/null 2>&1; do
  sleep 1
done

echo "✅ PostgreSQL is ready."

echo "📦 Creating databases..."
for DB_NAME in core_realm00000 workflow_realm00000 oplap_realm0000; do
  echo "🔍 Checking if database '$DB_NAME' exists..."
  if docker exec -i $(docker compose ps -q db) psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
    echo "✅ Database '$DB_NAME' already exists."
  else
    echo "➕ Creating database '$DB_NAME'..."
    docker exec -i $(docker compose ps -q db) psql -U postgres -c "CREATE DATABASE $DB_NAME;"
  fi
done

echo "🚚 Running migrations core"
docker compose run --rm core-migration

echo "🚚 Running migrations workflow"
docker compose run --rm workflow-migration

# olap migration

docker compose down
echo "✅ Done!"
