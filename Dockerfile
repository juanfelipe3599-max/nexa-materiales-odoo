# Imagen oficial de Odoo 18 Community + el módulo propio.
# Este repositorio tiene los archivos en la raíz (subida web sin carpetas);
# aquí se reconstruye la estructura del módulo dentro de la imagen.
FROM odoo:18.0

USER root
ARG M=/mnt/extra-addons/nexa_materiales
COPY __init__.py __manifest__.py ${M}/
COPY ["__init__ (1).py", "/mnt/extra-addons/nexa_materiales/models/__init__.py"]
COPY material.py precio_compra.py ${M}/models/
COPY nexa_materiales_security.xml ir.model.access.csv ${M}/security/
COPY material_views.xml precio_compra_views.xml menus.xml ${M}/views/
COPY ["__init__ (2).py", "/mnt/extra-addons/nexa_materiales/tests/__init__.py"]
COPY test_precio_vigente.py ${M}/tests/
COPY icon.png ${M}/static/description/
COPY configurar_instancia.py estado_bd.py /opt/nexa/
COPY entrypoint-nexa.sh /usr/local/bin/entrypoint-nexa.sh
RUN chmod +x /usr/local/bin/entrypoint-nexa.sh && chown -R odoo:odoo /mnt/extra-addons /opt/nexa
USER odoo

# La configuración (con las credenciales) se genera al arrancar desde variables
# de entorno, en /tmp y con permisos 600. La imagen no contiene secretos.
ENV ODOO_RC=/tmp/odoo.conf
EXPOSE 8069
ENTRYPOINT ["/usr/local/bin/entrypoint-nexa.sh"]
CMD []
