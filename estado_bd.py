"""Espera a que PostgreSQL responda e informa el estado de la base de Odoo.

Imprime una de: vacia | sin_modulo | instalado
"""
import os
import sys
import time

import psycopg2

params = dict(
    host=os.environ["DB_HOST"], port=int(os.environ.get("DB_PORT", "5432")),
    user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
    dbname=os.environ["DB_NAME"], sslmode=os.environ.get("DB_SSLMODE", "prefer"),
)
for intento in range(60):
    try:
        conn = psycopg2.connect(**params)
        break
    except psycopg2.OperationalError as exc:
        print(f"[nexa] esperando PostgreSQL ({intento + 1}/60): {exc}".strip(), file=sys.stderr)
        time.sleep(2)
else:
    sys.exit("[nexa] PostgreSQL no respondió")

with conn, conn.cursor() as cr:
    cr.execute("SELECT to_regclass('public.ir_module_module')")
    if cr.fetchone()[0] is None:
        print("vacia")
    else:
        cr.execute("SELECT state FROM ir_module_module WHERE name = 'nexa_materiales'")
        fila = cr.fetchone()
        print("instalado" if fila and fila[0] == "installed" else "sin_modulo")
conn.close()
