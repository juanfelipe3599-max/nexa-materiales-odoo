# Imagen oficial de Odoo 18 Community + el módulo propio.
FROM odoo:18.0

USER root
COPY addons/ /mnt/extra-addons/
COPY scripts/configurar_instancia.py deploy/estado_bd.py /opt/nexa/
COPY deploy/entrypoint-nexa.sh /usr/local/bin/entrypoint-nexa.sh
RUN chmod +x /usr/local/bin/entrypoint-nexa.sh && chown -R odoo:odoo /mnt/extra-addons /opt/nexa
USER odoo

# La configuración (con las credenciales) se genera al arrancar desde variables
# de entorno, en /tmp y con permisos 600. La imagen no contiene secretos.
ENV ODOO_RC=/tmp/odoo.conf
EXPOSE 8069
ENTRYPOINT ["/usr/local/bin/entrypoint-nexa.sh"]
CMD []
