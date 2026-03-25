from flask import current_app
from models.productos_model import productos

def listado_productos():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, nombre, descripcion, precio_venta, unidades_por_bandeja, activo, created_at, updated_at FROM productos"
    c.execute(sql)
    datos = c.fetchall()

    lista = []
    for p in datos:
        producto = productos(
            id                    = p[0],
            nombre                = p[1],
            descripcion           = p[2],
            precio_venta          = p[3],
            unidades_por_bandeja  = p[4],
            activo                = p[5],
            created_at            = p[6],
            updated_at            = p[7]
        ).toDic()
        lista.append(producto)

    return lista        

