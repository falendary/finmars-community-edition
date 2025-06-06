Before start app

1. Create VPS
2. Create main and auth domain
2.5 What doing when cert doesnt created yet
3. Create cert by certbot
    docker compose run --rm certbot
4. Create realm finmars and user in keycloak 



*0 make import-sql (if nessary)
*0.2 change db scheme name to space00000 in core_realm00000 and workflow_realm00000 db and update core_realm00000/space00000/users_masteruser space_code on space00000

1. make migrate
2. make up

!!!Attention: remove .env file from frontend repositories