COMPOSE = docker compose

.PHONY: generate-env migrate up down restart-nginx import-sql export-sql


generate-env:
	./generate-env.sh

init-keycloak:
	./init-keycloak.sh

init-cert:
	docker compose up certbot

migrate:
	./migrate.sh

up:
	$(COMPOSE) up --build \
	--remove-orphans \
	--scale core-migration=0 \
	--scale workflow-migration=0 \
	--scale certbot=0

down:
	$(COMPOSE) down

restart-nginx:
	docker exec -i finmars-community-edition-nginx-1 nginx -s reload

import-sql: 
	./import-sql.sh

export-sql:
	./export-sql.sh

db:
	docker compose up -d db

db-authorizer:
	docker compose up -d db-authorizer
