"""Demostración: el perfil Consulta no puede escribir ni llamando la API directamente.

Se salta la interfaz y habla con el servidor por XML-RPC y por JSON-RPC,
como lo haría cualquier script o agente. Todas las credenciales vienen de
variables de entorno:

    ODOO_URL, ODOO_DB,
    NEXA_CONSULTA_LOGIN, NEXA_CONSULTA_PASSWORD,
    NEXA_COMPRAS_LOGIN, NEXA_COMPRAS_PASSWORD

Sale con código 0 solo si TODOS los intentos de escritura de Consulta fueron
rechazados por el servidor y Compras sí pudo escribir.
"""
import json
import os
import sys
import urllib.request
import xmlrpc.client
from datetime import date

URL = os.environ["ODOO_URL"].rstrip("/")
DB = os.environ["ODOO_DB"]
fallos = []


def xmlrpc_login(prefijo):
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid = common.authenticate(DB, os.environ[f"{prefijo}_LOGIN"], os.environ[f"{prefijo}_PASSWORD"], {})
    if not uid:
        sys.exit(f"No se pudo autenticar {prefijo}")
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
    pwd = os.environ[f"{prefijo}_PASSWORD"]
    return lambda model, method, *args, **kw: models.execute_kw(DB, uid, pwd, model, method, list(args), kw)


def jsonrpc(prefijo, model, method, args):
    """Mismo intento por el otro protocolo (JSON-RPC)."""
    payload = {"jsonrpc": "2.0", "method": "call", "id": 1, "params": {
        "service": "object", "method": "execute_kw",
        "args": [DB, UIDS[prefijo], os.environ[f"{prefijo}_PASSWORD"], model, method, args],
    }}
    req = urllib.request.Request(f"{URL}/jsonrpc", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def debe_fallar(etiqueta, fn):
    try:
        fn()
    except xmlrpc.client.Fault as e:
        lineas = [l.strip() for l in e.faultString.strip().splitlines() if l.strip()]
        motivo = next((l for l in lineas if "not allowed" in l or "no se" in l.lower() or "calculan" in l), lineas[-1])[:140]
        print(f"  RECHAZADO  {etiqueta}\n             servidor: {motivo}")
        return
    print(f"  ¡PERMITIDO! {etiqueta}  <-- FALLA DE SEGURIDAD")
    fallos.append(etiqueta)


compras = xmlrpc_login("NEXA_COMPRAS")
consulta = xmlrpc_login("NEXA_CONSULTA")
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
UIDS = {p: common.authenticate(DB, os.environ[f"{p}_LOGIN"], os.environ[f"{p}_PASSWORD"], {})
        for p in ("NEXA_COMPRAS", "NEXA_CONSULTA")}

print(f"Servidor: {URL}  base: {DB}\n")
print("1) Compras crea un material y dos compras (100 y 130) por API")
codigo = f"DEMO-API-{date.today():%Y%m%d}-{os.getpid()}"
mid = compras("nexa.material", "create", {"codigo": codigo, "nombre": "Material demo API", "unidad_medida": "und"})
compras("nexa.precio.compra", "create", {"material_id": mid, "fecha": "2026-09-01", "proveedor": "A", "precio_unitario": 100, "cantidad": 1})
cid = compras("nexa.precio.compra", "create", {"material_id": mid, "fecha": "2026-09-15", "proveedor": "B", "precio_unitario": 130, "cantidad": 1})
m = compras("nexa.material", "read", [mid], fields=["precio_vigente", "ultima_compra_es_desvio"])[0]
c = compras("nexa.precio.compra", "read", [cid], fields=["es_desvio"])[0]
print(f"  precio_vigente={m['precio_vigente']}  ultima_compra_es_desvio={m['ultima_compra_es_desvio']}  compra2.es_desvio={c['es_desvio']}")
if m["precio_vigente"] != 130 or not c["es_desvio"]:
    fallos.append("cálculo en servidor")

print("\n2) Consulta SÍ puede leer")
leidos = consulta("nexa.material", "search_read", [("id", "=", mid)], fields=["codigo", "precio_vigente"])
print(f"  leído: {leidos}")

print("\n3) Consulta intenta escribir por XML-RPC (todo debe ser rechazado)")
debe_fallar("crear material", lambda: consulta("nexa.material", "create", {"codigo": codigo + "-X", "nombre": "x", "unidad_medida": "und"}))
debe_fallar("editar nombre", lambda: consulta("nexa.material", "write", [mid], {"nombre": "hackeado"}))
debe_fallar("archivar (active=False)", lambda: consulta("nexa.material", "write", [mid], {"active": False}))
debe_fallar("método action_archive", lambda: consulta("nexa.material", "action_archive", [mid]))
debe_fallar("borrar material", lambda: consulta("nexa.material", "unlink", [mid]))
debe_fallar("registrar compra", lambda: consulta("nexa.precio.compra", "create", {"material_id": mid, "fecha": "2026-09-20", "proveedor": "C", "precio_unitario": 1, "cantidad": 1}))
debe_fallar("editar precio de una compra", lambda: consulta("nexa.precio.compra", "write", [cid], {"precio_unitario": 1}))

print("\n4) Consulta intenta escribir por JSON-RPC")
r = jsonrpc("NEXA_CONSULTA", "nexa.material", "write", [[mid], {"nombre": "hackeado por json"}])
if "error" in r:
    print(f"  RECHAZADO  editar nombre\n             servidor: {r['error']['data']['message'].splitlines()[0][:140]}")
else:
    print("  ¡PERMITIDO! editar nombre por JSON-RPC  <-- FALLA"); fallos.append("json-rpc write")

print("\n5) Ni siquiera Compras puede escribir campos calculados ni borrar")
debe_fallar("Compras escribe precio_vigente a mano", lambda: compras("nexa.material", "write", [mid], {"precio_vigente": 1}))
debe_fallar("Compras escribe es_desvio a mano", lambda: compras("nexa.precio.compra", "write", [cid], {"es_desvio": False}))
debe_fallar("Compras borra el material", lambda: compras("nexa.material", "unlink", [mid]))

nombre = compras("nexa.material", "read", [mid], fields=["nombre"])[0]["nombre"]
print(f"\nVerificación final: el nombre sigue siendo '{nombre}'")
compras("nexa.material", "write", [mid], {"active": False})
print("Limpieza: Compras archivó el material de demostración (no se borra).")

print("\nRESULTADO:", "OK — ningún intento no autorizado fue aceptado" if not fallos else f"FALLAS: {fallos}")
sys.exit(1 if fallos else 0)
