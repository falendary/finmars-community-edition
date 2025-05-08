#!/bin/bash
set -e

echo "🚀 Starting PostgreSQL container..."
docker compose up -d db

echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec $(docker compose ps -q db) pg_isready -U postgres > /dev/null 2>&1; do
  sleep 1
done

echo "✅ PostgreSQL is ready."

for SERVICE_NAME in core workflow; do
  echo "🚚 Importing from data from dumps for $SERVICE_NAME..."
	docker exec -i finmars-community-edition-db-1 psql -U postgres -d ${SERVICE_NAME}_realm00000 < ../finmars-${SERVICE_NAME}/${SERVICE_NAME}.sql
done

docker compose down
echo "✅ Done!"
