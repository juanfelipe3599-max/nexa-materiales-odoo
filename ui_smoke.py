"""Recorrido de interfaz (humo) con navegador real: escritorio y celular.

Variables: ODOO_URL, NEXA_COMPRAS_LOGIN/PASSWORD, NEXA_CONSULTA_LOGIN/PASSWORD, SHOTS_DIR
"""
import os
import time
from playwright.sync_api import sync_playwright

URL = os.environ["ODOO_URL"].rstrip("/")
OUT = os.environ.get("SHOTS_DIR", "shots")
os.makedirs(OUT, exist_ok=True)
ACTION = "/odoo/action-nexa_materiales.nexa_material_action"


def login(page, prefijo):
    page.goto(f"{URL}/web/login")
    page.fill("input[name=login]", os.environ[f"{prefijo}_LOGIN"])
    page.fill("input[name=password]", os.environ[f"{prefijo}_PASSWORD"])
    page.click("button[type=submit]")
    page.wait_for_selector(".o_main_navbar", timeout=30000)


def esperar(page):
    # Odoo mantiene una conexión abierta (bus), así que no se espera "networkidle".
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector(".o_action_manager .o_view_controller", timeout=30000)
    time.sleep(1.5)


with sync_playwright() as p:
    b = p.chromium.launch()
    # ---------- Compras, escritorio ----------
    ctx = b.new_context(viewport={"width": 1366, "height": 800}, locale="es-CO")
    page = ctx.new_page()
    login(page, "NEXA_COMPRAS")
    page.goto(URL + ACTION); esperar(page)
    page.click("button.o_list_button_add"); esperar(page)
    codigo = f"UI-{int(time.time())}"
    page.fill("div[name=nombre] input", "Varilla corrugada 3/8 (UI)")
    page.fill("div[name=codigo] input", codigo)
    page.fill("div[name=unidad_medida] input", "und")
    page.fill("div[name=categoria] input", "Acero")
    for fecha, prov, precio in (("01/09/2026", "Ferretería A", "14250"), ("20/09/2026", "Ferretería B", "17000")):
        page.click("div[name=compra_ids] .o_field_x2many_list_row_add a"); esperar(page)
        fila = page.locator("div[name=compra_ids] tr.o_selected_row")
        fila.locator("div[name=fecha] input").fill(fecha)
        fila.locator("div[name=proveedor] input").fill(prov)
        fila.locator("div[name=cantidad] input").fill("10")
        fila.locator("div[name=precio_unitario] input").fill(precio)
    page.click("button.o_form_button_save"); esperar(page)
    errores = page.locator(".o_notification.border-danger, .o_error_dialog").count()
    page.screenshot(path=f"{OUT}/1_form_compras.png", full_page=True)
    precio = page.locator("div[name=precio_vigente]").inner_text()
    print("precio_vigente en formulario:", precio.strip(), "| errores:", errores)
    page.goto(URL + ACTION); esperar(page)
    page.screenshot(path=f"{OUT}/2_lista_compras.png", full_page=True)
    rojas = page.locator("tr.o_data_row.text-danger").count()
    print("filas en rojo (desvío) en la lista:", rojas)
    ctx.close()

    # ---------- Consulta, celular ----------
    ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True,
                        device_scale_factor=2, locale="es-CO")
    page = ctx.new_page()
    login(page, "NEXA_CONSULTA")
    page.goto(URL + ACTION); esperar(page)
    page.screenshot(path=f"{OUT}/3_celular_consulta_kanban.png")
    crear_visible = page.locator("button.o_list_button_add, button.o-kanban-button-new").count()
    print("botón 'Nuevo' visible para Consulta:", crear_visible)
    page.locator(".o_kanban_record").filter(has_text=codigo).first.click(); esperar(page)
    page.screenshot(path=f"{OUT}/4_celular_consulta_form.png", full_page=True)
    editable = page.locator("div[name=nombre] input").count()
    print("campo nombre editable para Consulta:", editable)
    ctx.close()
    b.close()
