# nexa_materiales — Catálogo de materiales con precio vigente (Odoo 18 Community)

Primera pieza de la plataforma de materiales: la **referencia única de material** a la que
apuntarán el presupuesto (APU, cotización) y la compra (orden de compra, factura).

## Qué hace

| Requisito | Dónde está |
|---|---|
| Material: codigo (único), nombre, unidad_medida, categoria, activo | `models/material.py` |
| PrecioCompra: material, fecha, proveedor, precio_unitario > 0, cantidad > 0 | `models/precio_compra.py` (CHECK en PostgreSQL) |
| `precio_vigente` = precio de la compra más reciente (en servidor, almacenado) | `_compute_ultima_compra` |
| `es_desvio` = variación > 15 % vs. la compra inmediatamente anterior | `_compute_es_desvio` |
| Desactivar, nunca borrar | campo `active` + `unlink()` bloqueado + ningún perfil tiene permiso de borrado |
| Perfiles Compras (lee/escribe) y Consulta (solo lee) | `security/` (grupos + `ir.model.access.csv`) |
| Lista con desvío visible, búsqueda por código y nombre, vista de celular | `views/` |
| Prueba automática 100 → 130 | `tests/test_precio_vigente.py` |
| Demostración de permisos por API | `scripts/demo_permisos_api.py` |

## Correr la prueba

```bash
odoo-bin --addons-path=<odoo>/addons,addons -d prueba -i nexa_materiales \
  --test-enable --test-tags /nexa_materiales --stop-after-init
# esperado: "0 failed, 0 error(s) of 1 tests"
```
En GitHub corre sola en cada push (`.github/workflows/pruebas.yml`).

## Desplegar

### Gratis: Render (Blueprint)
1. Subir este repositorio a GitHub (público o conectado a Render).
2. Abrir `https://render.com/deploy?repo=https://github.com/<usuario>/<repo>` e iniciar sesión.
3. "Apply": Render crea la base PostgreSQL y el servicio web a partir de `render.yaml`.
   El primer arranque instala el módulo, el idioma es_CO, la moneda COP y los dos usuarios.
4. Las claves generadas quedan en Render → servicio → Environment.

Límites del plan gratis: el servicio se duerme a los 15 min sin tráfico (el siguiente acceso tarda
en despertar) y la base gratuita vence a los 30 días. Los adjuntos van dentro de PostgreSQL, así que
la falta de disco persistente no rompe la interfaz. Consumo medido de Odoo en reposo: ~270 MB.

### Servidor propio (VPS con Docker y dominio)
```bash
cd deploy && cp .env.example .env   # llenar credenciales y DOMAIN
./desplegar.sh                      # primera vez
./desplegar.sh actualizar           # versión nueva del módulo
```
HTTPS automático con Caddy. Ninguna credencial está en el código.

## Demostrar que Consulta no puede escribir por API

```bash
export ODOO_URL=https://<dominio> ODOO_DB=<base> \
  NEXA_COMPRAS_LOGIN=... NEXA_COMPRAS_PASSWORD=... \
  NEXA_CONSULTA_LOGIN=... NEXA_CONSULTA_PASSWORD=...
python3 scripts/demo_permisos_api.py   # sale con 0 solo si todo intento no autorizado fue rechazado
```
También se puede correr desde GitHub: Actions → "demo-permisos-api" (pide la URL; las claves van como secretos).

## Esquema y migraciones

En Odoo el esquema **se declara en los modelos** (archivos versionados en git) y lo aplica el
servidor al instalar (`-i`) o actualizar (`-u`) el módulo. La versión está en `__manifest__.py`.
Los cambios que el ORM no resuelve solo (renombrar campos, mover datos) van como scripts en
`migrations/<nueva_versión>/pre-*.py` o `post-*.py`, que Odoo ejecuta una vez al actualizar.
Nada se crea por consola ni por la interfaz de administración.

## Patrón de permisos para los próximos modelos

1. Grupos por perfil en `security/*_security.xml` (el de escritura implica el de lectura).
2. `ir.model.access.csv`: qué operaciones por modelo y grupo (nadie con `perm_unlink` en datos maestros).
3. Visibilidad por registro con `ir.rule` (reglas de registro). Ejemplo para el futuro modelo de obra:
   `domain_force = [('residente_ids', 'in', [user.id])]` para el grupo Residente.
   Odoo aplica estas reglas en el ORM a toda lectura/escritura, venga de la interfaz, de la API o de un agente.
4. Campos calculados protegidos contra escritura manual (`_rechazar_campos_calculados`).
