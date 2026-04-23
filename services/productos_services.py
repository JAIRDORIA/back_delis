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

def registro(nombre, descripcion, precio_venta, unidades_por_bandeja):
    c = current_app.mysql.connection.cursor()
    sql = """
             INSERT INTO productos (nombre, descripcion, precio_venta, unidades_por_bandeja)
             VALUES 
             (%s, %s, %s, %s)
             """
    c.execute(sql, (nombre, descripcion, precio_venta, unidades_por_bandeja))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    c.close()
    return productos(id, nombre, descripcion, precio_venta, unidades_por_bandeja, 1, None, None).toDic() 

def existe_nombre(nombre):
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id FROM productos WHERE nombre = %s"
    c.execute(sql, (nombre,))
    dato = c.fetchone()
    c.close()

    return dato is not None


def existe_producto(producto_id):
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id FROM productos WHERE id = %s"
    c.execute(sql, (producto_id,))
    dato = c.fetchone()
    c.close()

    return dato is not None     

def eliminar(id):
    c = current_app.mysql.connection.cursor()
    
    sql = "UPDATE productos SET activo = 0 WHERE id = %s"
    c.execute(sql, (id,))
    
    current_app.mysql.connection.commit()
    filas_afectadas = c.rowcount
    c.close()

    return filas_afectadas > 0    

def productos_mas_vendidos(limite=5):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT
            p.id,
            p.nombre,
            p.precio_venta,
            COALESCE(SUM(vd.cantidad), 0) AS unidades_vendidas,
            COALESCE(SUM(vd.subtotal), 0) AS total_ingresos
        FROM productos p
        LEFT JOIN venta_detalle vd ON vd.producto_id = p.id
        LEFT JOIN ventas v ON v.id = vd.venta_id
            AND v.estado != 'anulada'
        WHERE p.activo = 1
        GROUP BY p.id, p.nombre, p.precio_venta
        ORDER BY total_ingresos DESC
        LIMIT %s
    """, (limite,))
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        lista.append({
            "id"              : p[0],
            "nombre"          : p[1],
            "precio_venta"    : float(p[2]),
            "unidades_vendidas": int(p[3]),
            "total_ingresos"  : float(p[4])
        })
    return lista