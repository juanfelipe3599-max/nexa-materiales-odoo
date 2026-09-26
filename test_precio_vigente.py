from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "nexa_materiales")
class TestPrecioVigente(TransactionCase):

    def test_compra_100_luego_130_es_desvio_y_precio_vigente_130(self):
        """Crear material → compra a 100 → compra a 130.

        Se ejecuta con un usuario del perfil Compras (no como superusuario)
        para que la prueba también pase por las reglas de acceso.
        """
        usuario_compras = self.env["res.users"].create({
            "name": "Usuario Compras (prueba)",
            "login": "compras_test@nexa.local",
            "groups_id": [(6, 0, [
                self.env.ref("base.group_user").id,
                self.env.ref("nexa_materiales.group_materiales_compras").id,
            ])],
        })
        env = self.env(user=usuario_compras)

        material = env["nexa.material"].create({
            "codigo": "TEST-CEM-001",
            "nombre": "Cemento gris prueba",
            "unidad_medida": "bulto",
        })
        self.assertFalse(material.tiene_precio, "Sin compras no debe haber precio vigente")

        compra_1 = env["nexa.precio.compra"].create({
            "material_id": material.id, "fecha": date(2026, 9, 1),
            "proveedor": "Proveedor A", "precio_unitario": 100.0, "cantidad": 10.0,
        })
        compra_2 = env["nexa.precio.compra"].create({
            "material_id": material.id, "fecha": date(2026, 9, 15),
            "proveedor": "Proveedor B", "precio_unitario": 130.0, "cantidad": 10.0,
        })

        self.assertEqual(material.precio_vigente, 130.0)
        self.assertTrue(compra_2.es_desvio, "130 vs 100 = +30 %: debe ser desvío")
        self.assertFalse(compra_1.es_desvio, "La primera compra nunca es desvío")
        self.assertTrue(material.ultima_compra_es_desvio)
