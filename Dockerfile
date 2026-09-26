# Imagen oficial de Odoo 18 Community + el módulo propio, a partir de un solo archivo
# nexa_bundle.zip en la raíz del repositorio (así la subida web de GitHub no pierde carpetas).
FROM odoo:18.0

USER root
COPY nexa_bundle.zip /tmp/nexa_bundle.zip
# El módulo va en /opt/nexa/addons (no en /mnt/extra-addons, que la imagen oficial declara como volumen).
RUN python3 -c "import zipfile; zipfile.ZipFile('/tmp/nexa_bundle.zip').extractall('/opt/nexa')" \
 && test -f /opt/nexa/addons/nexa_materiales/__manifest__.py \
 && install -m 755 /opt/nexa/deploy/entrypoint-nexa.sh /usr/local/bin/entrypoint-nexa.sh \
 && cp /opt/nexa/deploy/estado_bd.py /opt/nexa/scripts/configurar_instancia.py /opt/nexa/ \
 && rm /tmp/nexa_bundle.zip && chown -R odoo:odoo /opt/nexa
USER odoo

# La configuración (con las credenciales) se genera al arrancar desde variables
# de entorno, en /tmp y con permisos 600. La imagen no contiene secretos.
ENV ODOO_RC=/tmp/odoo.conf \
    ODOO_ADDONS_PATH=/opt/nexa/addons,/usr/lib/python3/dist-packages/odoo/addons \
    NEXA_MANIFEST=/opt/nexa/addons/nexa_materiales/__manifest__.py \
    NEXA_SCRIPTS=/opt/nexa
EXPOSE 8069
ENTRYPOINT ["/usr/local/bin/entrypoint-nexa.sh"]
CMD []
