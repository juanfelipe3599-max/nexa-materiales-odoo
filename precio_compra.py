from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

# Variación máxima tolerada frente a la compra inmediatamente anterior.
# "Más de 15 %" es estrictamente mayor: exactamente 15 % no es desvío.
UMBRAL_DESVIO = 0.15


class NexaPrecioCompra(models.Model):
    """Precio al que realmente se compró un material en una fecha."""

    _name = "nexa.precio.compra"
    _description = "Precio de compra de material"
    _order = "fecha desc, id desc"
    _rec_name = "material_id"

    material_id = fields.Many2one(
        "nexa.material", string="Material", required=True, index=True,
        ondelete="restrict",
    )
    fecha = fields.Date(string="Fecha", required=True, index=True,
                        default=fields.Date.context_today)
    proveedor = fields.Char(string="Proveedor", required=True)
    currency_id = fields.Many2one(
        "res.currency", string="Moneda", required=True,
        default=lambda self: self.env.company.currency_id,
    )
    precio_unitario = fields.Monetary(
        string="Precio unitario", required=True, currency_field="currency_id",
    )
    cantidad = fields.Float(string="Cantidad", required=True, digits=(16, 3))
    unidad_medida = fields.Char(related="material_id.unidad_medida", string="Unidad")
    es_desvio = fields.Boolean(
        string="Desvío", compute="_compute_es_desvio", store=True, readonly=True,
        help="Verdadero si el precio varía más de 15 %, hacia arriba o hacia "
             "abajo, frente a la compra inmediatamente anterior del mismo "
             "material. La primera compra nunca es desvío.",
    )
    variacion_pct = fields.Float(
        string="Variación vs. anterior (%)", compute="_compute_es_desvio",
        store=True, readonly=True, digits=(16, 2),
    )

    _sql_constraints = [
        ("precio_positivo", "CHECK(precio_unitario > 0)",
         "El precio unitario debe ser mayor que cero."),
        ("cantidad_positiva", "CHECK(cantidad > 0)",
         "La cantidad debe ser mayor que cero."),
    ]

    _CAMPOS_CALCULADOS = {"es_desvio", "variacion_pct"}

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._rechazar_campos_calculados(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._rechazar_campos_calculados(vals)
        return super().write(vals)

    def _rechazar_campos_calculados(self, vals):
        prohibidos = self._CAMPOS_CALCULADOS.intersection(vals)
        if prohibidos:
            raise UserError(_(
                "Estos campos se calculan automáticamente y no se pueden escribir: %s",
                ", ".join(sorted(prohibidos)),
            ))

    @staticmethod
    def _orden_cronologico(compra):
        """Orden único y total: fecha y, en la misma fecha, orden de registro."""
        rid = compra.id if isinstance(compra.id, int) else (compra._origin.id or float("inf"))
        return (compra.fecha or date.min, rid)

    # Depende de las compras hermanas: si se registra o corrige una compra
    # anterior, el desvío de la siguiente se recalcula solo.
    @api.depends(
        "fecha", "precio_unitario", "currency_id", "material_id",
        "material_id.compra_ids.fecha",
        "material_id.compra_ids.precio_unitario",
        "material_id.compra_ids.currency_id",
    )
    def _compute_es_desvio(self):
        for compra in self:
            compra.es_desvio = False
            compra.variacion_pct = 0.0
            if not compra.material_id or not compra.fecha:
                continue
            hermanas = compra.material_id.compra_ids.filtered(
                lambda c: c.currency_id == compra.currency_id and c.fecha
            ).sorted(self._orden_cronologico)
            clave = self._orden_cronologico(compra)
            anteriores = hermanas.filtered(lambda c: self._orden_cronologico(c) < clave)
            anterior = anteriores[-1:]
            if not anterior or not anterior.precio_unitario:
                continue
            diferencia = abs(compra.precio_unitario - anterior.precio_unitario)
            compra.variacion_pct = (
                (compra.precio_unitario - anterior.precio_unitario)
                / anterior.precio_unitario * 100.0
            )
            compra.es_desvio = float_compare(
                diferencia, UMBRAL_DESVIO * anterior.precio_unitario,
                precision_digits=6,
            ) > 0
