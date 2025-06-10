Before start app

1. Create VPS
2. Create main and auth domain
2.5 What doing when cert doesnt created yet
3. Create cert by certbot
    docker compose run --rm certbot

Init app
1. make env
2. make init-keycloak
3. make migrate
4. make up

!!!Attention: remove .env file from frontend repositories