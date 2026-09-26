from odoo import _, api, fields, models
from odoo.exceptions import UserError


class NexaMaterial(models.Model):
    """Referencia única de material.

    Es el punto de encuentro entre el presupuesto (APU, cotización) y la
    compra (orden de compra, factura). Todo lo que hable de un material debe
    apuntar a este registro por su id, nunca por texto.
    """

    _name = "nexa.material"
    _description = "Material"
    _order = "codigo"
    _rec_names_search = ["codigo", "nombre"]

    codigo = fields.Char(
        string="Código", required=True, index=True,
        help="Código único del material. No se repite ni entre materiales archivados.",
    )
    nombre = fields.Char(string="Nombre", required=True, index=True)
    unidad_medida = fields.Char(
        string="Unidad de medida", required=True,
        help="Ejemplos: kg, m3, und, bulto, ml, gl.",
    )
    categoria = fields.Char(string="Categoría", index=True)
    # Se usa el nombre técnico estándar `active` (etiqueta "Activo") porque es
    # el que Odoo reconoce para archivar: los inactivos desaparecen de las
    # búsquedas normales pero siguen en la base y siguen siendo referenciables.
    active = fields.Boolean(string="Activo", default=True)

    compra_ids = fields.One2many(
        "nexa.precio.compra", "material_id", string="Precios de compra",
    )
    compra_count = fields.Integer(
        string="N.º de compras", compute="_compute_ultima_compra", store=True,
    )

    # --- Precio vigente: calculado y almacenado en el servidor -------------
    # Se guarda la compra que define el precio (no solo el número) para que el
    # APU y el motor de margen puedan saber fecha, proveedor y moneda del
    # precio que están usando.
    ultima_compra_id = fields.Many2one(
        "nexa.precio.compra", string="Compra vigente",
        compute="_compute_ultima_compra", store=True, readonly=True,
    )
    currency_id = fields.Many2one(
        related="ultima_compra_id.currency_id", store=True, string="Moneda",
    )
    precio_vigente = fields.Monetary(
        string="Precio vigente", currency_field="currency_id",
        compute="_compute_ultima_compra", store=True, readonly=True,
        help="Precio unitario de la compra más reciente. Se calcula solo; "
             "no se puede escribir. Sin compras, el material no tiene precio "
             "(ver 'Tiene precio').",
    )
    tiene_precio = fields.Boolean(
        string="Tiene precio", compute="_compute_ultima_compra", store=True,
        help="Falso cuando el material no tiene compras registradas. Odoo no "
             "guarda nulos en campos numéricos, así que este indicador es la "
             "forma confiable de saber si precio_vigente está vacío.",
    )
    fecha_precio_vigente = fields.Date(
        related="ultima_compra_id.fecha", store=True, string="Fecha del precio",
    )
    proveedor_precio_vigente = fields.Char(
        related="ultima_compra_id.proveedor", store=True, string="Proveedor del precio",
    )
    ultima_compra_es_desvio = fields.Boolean(
        related="ultima_compra_id.es_desvio", store=True,
        string="Última compra en desvío",
    )

    _sql_constraints = [
        ("codigo_unico", "unique(codigo)",
         "Ya existe un material con ese código (puede estar archivado). "
         "Use otro código o reactive el existente."),
    ]

    @api.depends("compra_ids.fecha", "compra_ids.precio_unitario", "compra_ids.currency_id")
    def _compute_ultima_compra(self):
        for material in self:
            compras = material.compra_ids.sorted(self.env["nexa.precio.compra"]._orden_cronologico)
            ultima = compras[-1:]
            material.ultima_compra_id = ultima
            material.precio_vigente = ultima.precio_unitario if ultima else 0.0
            material.tiene_precio = bool(ultima)
            material.compra_count = len(compras)

    def _precio_vigente_a_fecha(self, fecha):
        """Punto de extensión para APU y motor de margen.

        Devuelve la compra vigente a una fecha dada (la última con fecha <=
        `fecha`), o una compra vacía. Hoy no lo usa ninguna pantalla.
        """
        self.ensure_one()
        compras = self.compra_ids.filtered(lambda c: c.fecha and c.fecha <= fecha)
        return compras.sorted(self.env["nexa.precio.compra"]._orden_cronologico)[-1:]

    @api.depends("codigo", "nombre")
    def _compute_display_name(self):
        for material in self:
            material.display_name = f"[{material.codigo}] {material.nombre}" if material.codigo else material.nombre

    # Campos que solo el servidor calcula. Se rechazan si llegan desde un
    # cliente (formulario o API): en Odoo un campo calculado y almacenado sin
    # inverso se podría sobrescribir con write(), así que se bloquea aquí.
    _CAMPOS_CALCULADOS = {
        "precio_vigente", "tiene_precio", "ultima_compra_id", "compra_count",
        "currency_id", "fecha_precio_vigente", "proveedor_precio_vigente",
        "ultima_compra_es_desvio",
    }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._rechazar_campos_calculados(vals)
            self._normalizar_codigo(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._rechazar_campos_calculados(vals)
        self._normalizar_codigo(vals)
        return super().write(vals)

    def _rechazar_campos_calculados(self, vals):
        prohibidos = self._CAMPOS_CALCULADOS.intersection(vals)
        if prohibidos:
            raise UserError(_(
                "Estos campos se calculan automáticamente y no se pueden escribir: %s",
                ", ".join(sorted(prohibidos)),
            ))

    @staticmethod
    def _normalizar_codigo(vals):
        if vals.get("codigo"):
            vals["codigo"] = vals["codigo"].strip()

    def unlink(self):
        # Además de no dar permiso de borrado a ningún perfil (ver
        # ir.model.access.csv), se bloquea aquí para que ni el superusuario
        # ni código futuro puedan borrar un material por error.
        raise UserError(_(
            "Los materiales no se borran porque presupuestos y compras los "
            "referencian. Use la acción 'Archivar' para desactivarlo."
        ))
