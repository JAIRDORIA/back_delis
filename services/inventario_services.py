from flask import current_app
from models.inventario_model import inventarios

def listado_inventarios():
    c = current_app.mysql.connection.cursor()
    sql = """
        SELECT i.id, i.producto_id, p.nombre, i.stock_actual, 
               i.unidades_sueltas, i.stock_minimo, i.updated_at 
        FROM inventario i
        JOIN productos p ON p.id = i.producto_id
        WHERE p.activo = 1
    """
    c.execute(sql)
    datos = c.fetchall()

    lista = []
    for p in datos:
        inventario = {
            "id"              : p[0],
            "producto_id"     : p[1],
            "nombre_producto" : p[2],
            "stock_actual"    : p[3],
            "unidades_sueltas": p[4],
            "stock_minimo"    : p[5],
            "updated_at"      : str(p[6]) if p[6] else None
        }
        lista.append(inventario)

    c.close()
    return lista


def registro(producto_id):
    c = current_app.mysql.connection.cursor()
    sql = """
        INSERT INTO inventario (producto_id)
        VALUES (%s)
    """
    c.execute(sql, (producto_id,))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    c.close()
    return inventarios(id, producto_id, 0, 0, 5, None).toDic()


def existe_inventario(producto_id):
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id FROM inventario WHERE producto_id = %s"
    c.execute(sql, (producto_id,))
    dato = c.fetchone()
    c.close()
    return dato is not None


def obtener_inventario(id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT i.id, i.producto_id, p.nombre, i.stock_actual, 
               i.unidades_sueltas, i.stock_minimo, i.updated_at
        FROM inventario i
        JOIN productos p ON p.id = i.producto_id
        WHERE i.id = %s AND p.activo = 1
    """, (id,))
    inventario = c.fetchone()
    c.close()
    if inventario:
        return {
            "id"              : inventario[0],
            "producto_id"     : inventario[1],
            "nombre_producto" : inventario[2],
            "stock_actual"    : inventario[3],
            "unidades_sueltas": inventario[4],
            "stock_minimo"    : inventario[5],
            "updated_at"      : str(inventario[6]) if inventario[6] else None
        }
    return None  # ← esto faltaba antes


def actualizar_stock_minimo(id, stock_minimo):
    c = current_app.mysql.connection.cursor()
    sql = """
        UPDATE inventario 
        SET stock_minimo = %s
        WHERE id = %s
    """
    c.execute(sql, (stock_minimo, id))
    current_app.mysql.connection.commit()
    filas_afectadas = c.rowcount
    c.close()
    return filas_afectadas > 0


def productos_bajo_stock():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, nombre, stock_actual, stock_minimo FROM v_productos_bajo_stock"
    c.execute(sql)
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        lista.append({
            "id"          : p[0],
            "nombre"      : p[1],
            "stock_actual": p[2],
            "stock_minimo": p[3]
        })
    return lista