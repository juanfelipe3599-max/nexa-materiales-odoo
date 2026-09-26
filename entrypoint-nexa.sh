#!/bin/bash
# Arranque de la instancia. Todo sale de variables de entorno; nada va en la imagen.
#
#   DB_HOST, DB_PORT (5432), DB_USER, DB_PASSWORD, DB_NAME   conexión PostgreSQL
#   ODOO_ADMIN_PASSWD                                         clave maestra de Odoo
#   PORT (8069)                                               puerto HTTP (Render lo define)
#   NEXA_ACTUALIZAR=1                                         aplica la nueva versión del módulo al arrancar
#
# Primera vez (base vacía): instala el módulo, idioma es_CO, moneda COP y los usuarios.
set -euo pipefail

: "${DB_HOST:?Falta DB_HOST}"
: "${DB_USER:?Falta DB_USER}"
: "${DB_PASSWORD:?Falta DB_PASSWORD}"
: "${DB_NAME:?Falta DB_NAME}"
: "${ODOO_ADMIN_PASSWD:?Falta ODOO_ADMIN_PASSWD}"
ODOO_BIN="${ODOO_BIN:-odoo}"
export ODOO_RC="${ODOO_RC:-/tmp/odoo.conf}"

umask 077
cat > "$ODOO_RC" <<EOF
[options]
addons_path = ${ODOO_ADDONS_PATH:-/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons}
data_dir = ${ODOO_DATA_DIR:-/var/lib/odoo}
db_host = ${DB_HOST}
db_port = ${DB_PORT:-5432}
db_user = ${DB_USER}
db_password = ${DB_PASSWORD}
db_name = ${DB_NAME}
dbfilter = ^${DB_NAME}\$
db_sslmode = ${DB_SSLMODE:-prefer}
admin_passwd = ${ODOO_ADMIN_PASSWD}
http_port = ${PORT:-8069}
list_db = False
proxy_mode = True
without_demo = all
workers = ${ODOO_WORKERS:-0}
EOF

ESTADO="$(python3 "${NEXA_SCRIPTS:-/opt/nexa}/estado_bd.py")"
echo "[nexa] estado de la base: ${ESTADO}"

if [ "$ESTADO" != "instalado" ]; then
  echo "[nexa] primera instalación"
  "$ODOO_BIN" -c "$ODOO_RC" -i nexa_materiales --load-language=es_CO --stop-after-init
  "$ODOO_BIN" shell -c "$ODOO_RC" --no-http < "${NEXA_SCRIPTS:-/opt/nexa}/configurar_instancia.py"
elif [ "${NEXA_ACTUALIZAR:-0}" = "1" ]; then
  echo "[nexa] actualizando módulo (migración de versión)"
  "$ODOO_BIN" -c "$ODOO_RC" -u nexa_materiales --stop-after-init
fi

exec "$ODOO_BIN" -c "$ODOO_RC" "$@"
