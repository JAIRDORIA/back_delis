from flask import current_app
from models.inventario_model import inventarios
import json

def listado_inventarios(pagina=1, limite=20):
    offset = (pagina - 1) * limite
    c = current_app.mysql.connection.cursor()

    c.execute("""
        SELECT COUNT(*) FROM inventario i
        JOIN productos p ON p.id = i.producto_id
        WHERE p.activo = 1
    """)
    total = c.fetchone()[0]

    sql = """
        SELECT i.id, i.producto_id, p.nombre, i.stock_actual, 
               i.unidades_sueltas, i.stock_minimo, i.updated_at 
        FROM inventario i
        JOIN productos p ON p.id = i.producto_id
        WHERE p.activo = 1
        LIMIT %s OFFSET %s
    """
    c.execute(sql, (limite, offset))
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        lista.append({
            "id"              : p[0],
            "producto_id"     : p[1],
            "nombre_producto" : p[2],
            "stock_actual"    : p[3],
            "unidades_sueltas": p[4],
            "stock_minimo"    : p[5],
            "updated_at"      : str(p[6]) if p[6] else None
        })

    return {
        "datos"        : lista,
        "total"        : total,
        "pagina"       : pagina,
        "limite"       : limite,
        "total_paginas": -(-total // limite)
    }

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
    return None  

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



def obtener_unidades_por_bandeja(producto_id):
    c = current_app.mysql.connection.cursor()
    c.execute("SELECT unidades_por_bandeja FROM productos WHERE id = %s", (producto_id,))
    row = c.fetchone()
    c.close()
    return row[0] if row else None
 
 
def normalizar_bandejas_sueltas(stock_actual, unidades_sueltas, unidades_por_bandeja):
    """
    Convierte un par (bandejas, sueltas) potencialmente "roto" (ej: sueltas
    que igualan o superan unidades_por_bandeja) a su forma normalizada,
    usando la misma formula que ya usa el sistema al descontar por ventas:
 
        total = (stock_actual * unidades_por_bandeja) + unidades_sueltas
        nuevas_bandejas = int(total / unidades_por_bandeja)
        nuevas_sueltas  = total - (nuevas_bandejas * unidades_por_bandeja)
    """
    total = (stock_actual * unidades_por_bandeja) + unidades_sueltas
    nuevas_bandejas = int(total / unidades_por_bandeja)
    nuevas_sueltas = total - (nuevas_bandejas * unidades_por_bandeja)
    return nuevas_bandejas, nuevas_sueltas
 
 
def actualizar_cantidades(id, stock_actual, unidades_sueltas, usuario_id):
    """
    Edita manualmente stock_actual/unidades_sueltas de un registro de
    inventario, normalizando el resultado y dejando registro en auditoria
    con el valor anterior y el nuevo.
    """
    inventario_actual = obtener_inventario(id)
    if not inventario_actual:
        return None
 
    producto_id = inventario_actual["producto_id"]
    unidades_por_bandeja = obtener_unidades_por_bandeja(producto_id)
    if not unidades_por_bandeja:
        raise Exception("El producto no tiene unidades_por_bandeja configurado")
 
    nuevas_bandejas, nuevas_sueltas = normalizar_bandejas_sueltas(
        stock_actual, unidades_sueltas, unidades_por_bandeja
    )
 
    c = current_app.mysql.connection.cursor()
 
    c.execute("""
        UPDATE inventario
        SET stock_actual = %s, unidades_sueltas = %s
        WHERE id = %s
    """, (nuevas_bandejas, nuevas_sueltas, id))
 
    c.execute("""
        INSERT INTO auditoria (usuario_id, accion, tabla_afectada, registro_id,
                                descripcion, datos_anteriores, datos_nuevos)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        usuario_id,
        'editar',
        'inventario',
        id,
        f"Edicion manual de cantidades de inventario (producto_id {producto_id})",
        json.dumps({
            "stock_actual": inventario_actual["stock_actual"],
            "unidades_sueltas": inventario_actual["unidades_sueltas"],
        }),
        json.dumps({
            "stock_actual": nuevas_bandejas,
            "unidades_sueltas": nuevas_sueltas,
        }),
    ))
 
    current_app.mysql.connection.commit()
    c.close()
 
    return {
        "id": id,
        "producto_id": producto_id,
        "stock_actual": nuevas_bandejas,
        "unidades_sueltas": nuevas_sueltas,
        "unidades_por_bandeja": unidades_por_bandeja,
    }