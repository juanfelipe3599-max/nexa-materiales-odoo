"""Configuración inicial de la instancia. Se ejecuta con `odoo shell`.

* Empresa en Colombia, moneda COP.
* Usuarios de los dos perfiles con credenciales tomadas de variables de entorno:
    NEXA_COMPRAS_LOGIN, NEXA_COMPRAS_PASSWORD
    NEXA_CONSULTA_LOGIN, NEXA_CONSULTA_PASSWORD
* Idioma es_CO y zona horaria de Bogotá para esos usuarios.

Es idempotente: se puede correr varias veces.
"""
import os

env = env  # noqa: F821  (inyectado por `odoo shell`)

# Adjuntos (incluidos los paquetes CSS/JS de la interfaz) dentro de PostgreSQL:
# así la instancia no depende de un disco persistente (plan gratis sin disco).
if os.environ.get("NEXA_ADJUNTOS_EN_BD", "1") == "1":
    env["ir.config_parameter"].sudo().set_param("ir_attachment.location", "db")
    env["ir.attachment"].force_storage()
    print("adjuntos: almacenados en la base de datos")
cop = env.ref("base.COP")
cop.active = True
company = env.company
company.write({
    "name": os.environ.get("NEXA_EMPRESA", "Constructora (demo NEXA)"),
    "country_id": env.ref("base.co").id,
    "currency_id": cop.id,
})
print(f"empresa: {company.name} · país CO · moneda {company.currency_id.name}")

perfiles = [
    ("Compras (demo)", "NEXA_COMPRAS", "nexa_materiales.group_materiales_compras"),
    ("Consulta (demo)", "NEXA_CONSULTA", "nexa_materiales.group_materiales_consulta"),
]
Users = env["res.users"].sudo().with_context(active_test=False)
for nombre, prefijo, grupo in perfiles:
    login = os.environ[f"{prefijo}_LOGIN"]
    vals = {
        "name": nombre, "login": login, "password": os.environ[f"{prefijo}_PASSWORD"],
        "groups_id": [(6, 0, [env.ref("base.group_user").id, env.ref(grupo).id])],
        "active": True, "lang": "es_CO", "tz": "America/Bogota",
    }
    user = Users.search([("login", "=", login)])
    user.write(vals) if user else Users.create(vals)
    print(f"usuario listo: {login} -> {grupo}")

env.ref("base.user_admin").write({"lang": "es_CO", "tz": "America/Bogota"})
env.cr.commit()
