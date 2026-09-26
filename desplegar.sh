#!/bin/bash
# Servidor propio con Docker. Uso, dentro de deploy/:
#   ./desplegar.sh             -> construye y arranca (la primera vez instala todo)
#   ./desplegar.sh actualizar  -> aplica la nueva versión del módulo (migración)
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] || { echo "Falta deploy/.env (copie .env.example)"; exit 1; }
set -a; . ./.env; set +a
docker compose build odoo
if [ "${1:-}" = "actualizar" ]; then
  NEXA_ACTUALIZAR=1 docker compose up -d --force-recreate odoo
else
  docker compose up -d
fi
echo "Listo: https://${DOMAIN}"
