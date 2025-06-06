COMPOSE = docker compose

.PHONY: env migrate up down restart-nginx import-sql export-sql


env:
	@if [ -f .env ]; then \
		read -p ".env already exists. Overwrite? (y/N): " ans; \
		if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
			cp .env.sample .env; \
			echo ".env overwritten."; \
		else \
			echo "Skipped creating .env."; \
		fi; \
	else \
		cp .env.sample .env; \
		echo ".env created from .env.sample."; \
	fi

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
