Before start app

1. Create VPS
2. Create main and auth domain
2.5 What doing when cert doesnt created yet
3. Create cert by certbot
    docker compose run --rm certbot
4. Create realm finmars and user in keycloak 


Init app

1. make migrate
2. make up

!!!Attention: remove .env file from frontend repositories