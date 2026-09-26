{
    "name": "NEXA · Catálogo de materiales y precio vigente",
    "summary": "Catálogo único de materiales con precio vigente calculado "
               "desde las compras y alerta de desvío de precio.",
    "description": """
Referencia única de materiales para presupuestos y órdenes de compra.

* precio_vigente = precio unitario de la compra más reciente (calculado en servidor).
* es_desvio = la compra varía más de 15 % frente a la inmediatamente anterior.
* Dos perfiles: Compras (lee y escribe) y Consulta (solo lee), aplicados en el ORM.
* Los materiales nunca se borran: se archivan.
""",
    "version": "18.0.1.0.0",
    "category": "Inventory/Purchase",
    "author": "NEXA",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/nexa_materiales_security.xml",
        "security/ir.model.access.csv",
        "views/precio_compra_views.xml",
        "views/material_views.xml",
        "views/menus.xml",
    ],
    "application": True,
    "installable": True,
}
