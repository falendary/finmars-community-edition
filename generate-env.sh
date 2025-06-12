#!/bin/bash

if [ -f .env ]; then
  read -p ".env already exists. Overwrite? (y/N): " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted. Keeping existing .env file."
    exit 0
  fi
fi

read -p "Enter MAIN_DOMAIN_NAME (e.g., ap-finmars.finmars.com): " MAIN_DOMAIN_NAME
read -p "Enter AUTH_DOMAIN_NAME (e.g., ap-finmars-auth.finmars.com): " AUTH_DOMAIN_NAME
read -p "Enter ADMIN_USERNAME: " ADMIN_USERNAME
read -sp "Enter ADMIN_PASSWORD: " ADMIN_PASSWORD
echo

ESCAPED_ADMIN_USERNAME=$(printf '%s\n' "$ADMIN_USERNAME" | sed -e 's/[\/&]/\\&/g')
ESCAPED_ADMIN_PASSWORD=$(printf '%s\n' "$ADMIN_PASSWORD" | sed -e 's/[\/&]/\\&/g')

SECRET_KEY=$(openssl rand -hex 4)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -hex 16)
KC_DB_PASSWORD=$(openssl rand -hex 16)

sed \
  -e "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" \
  -e "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${JWT_SECRET_KEY}|" \
  -e "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=${ENCRYPTION_KEY}|" \
  -e "s|^DB_PASSWORD=.*|DB_PASSWORD=${DB_PASSWORD}|" \
  -e "s|^KC_DB_PASSWORD=.*|KC_DB_PASSWORD=${KC_DB_PASSWORD}|" \
  -e "s|^DOMAIN_NAME=.*|DOMAIN_NAME=${MAIN_DOMAIN_NAME}|" \
  -e "s|^CSRF_COOKIE_DOMAIN=.*|CSRF_COOKIE_DOMAIN=${MAIN_DOMAIN_NAME}|" \
  -e "s|^CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=https://${MAIN_DOMAIN_NAME}|" \
  -e "s|^PROD_APP_HOST=.*|PROD_APP_HOST=https://${MAIN_DOMAIN_NAME}|" \
  -e "s|^APP_HOST=.*|APP_HOST=https://${MAIN_DOMAIN_NAME}|" \
  -e "s|^PROD_API_HOST=.*|PROD_API_HOST=https://${MAIN_DOMAIN_NAME}|" \
  -e "s|^API_HOST=.*|API_HOST=https://${MAIN_DOMAIN_NAME}|" \
  -e "s|^KEYCLOAK_SERVER_URL=.*|KEYCLOAK_SERVER_URL=https://${AUTH_DOMAIN_NAME}|" \
  -e "s|^KEYCLOAK_URL=.*|KEYCLOAK_URL=https://${AUTH_DOMAIN_NAME}|" \
  -e "s|^PROD_KEYCLOAK_URL=.*|PROD_KEYCLOAK_URL=https://${AUTH_DOMAIN_NAME}|" \
  -e "s|^ADMIN_USERNAME=.*|ADMIN_USERNAME=${ESCAPED_ADMIN_USERNAME}|" \
  -e "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${ESCAPED_ADMIN_PASSWORD}|" \
  -e "s|^MAIN_DOMAIN_NAME=.*|MAIN_DOMAIN_NAME=${MAIN_DOMAIN_NAME}|" \
  -e "s|^AUTH_DOMAIN_NAME=.*|AUTH_DOMAIN_NAME=${AUTH_DOMAIN_NAME}|" \
  -e "s|^REDIRECT_PATH=.*|REDIRECT_PATH=\"/realm00000/space00000/a/#!/dashboard\"|" \
  .env.sample > .env

echo ".env file created successfully from .env.sample."
