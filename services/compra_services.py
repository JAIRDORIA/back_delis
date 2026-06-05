from flask import current_app
from models.compra_model import compra
from services.cortes_services import obtener_corte_abierto, obtener_corte


def _existe(cursor, tabla, id):
    cursor.execute(f"SELECT id FROM {tabla} WHERE id = %s", (id,))
    return cursor.fetchone() is not None

def _compra_existe(cursor, id):
    cursor.execute("SELECT id FROM compras WHERE id = %s AND eliminada = 0", (id,))
    return cursor.fetchone() is not None


def listado_compra(pagina=1, limite=20, corte_id=None):
    try:
        offset = (pagina - 1) * limite
        con    = current_app.mysql.connection
        cursor = con.cursor()

        cursor.execute("SELECT COUNT(*) FROM compras WHERE eliminada = 0 AND corte_id = %s", (corte_id,))
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT c.id, c.proveedor_id, p.nombre, c.corte_id, c.usuario_id,
                   c.fecha, c.total, c.descripcion
            FROM compras c
            JOIN proveedores p ON p.id = c.proveedor_id
            WHERE c.eliminada = 0 AND c.corte_id = %s
            ORDER BY c.fecha DESC
            LIMIT %s OFFSET %s
        """, (corte_id, limite, offset))

        datos = cursor.fetchall()
        cursor.close()

        lista = []
        for fila in datos:
            com = compra(fila[0], fila[1], fila[3], fila[4], fila[5], fila[6], fila[7])
            d = com.toDic()
            d['nombre_proveedor'] = fila[2]
            lista.append(d)

        return {
            "total"        : total,
            "pagina"       : pagina,
            "limite"       : limite,
            "total_paginas": -(-total // limite),
            "compras"      : lista
        }
    except Exception as e:
        raise Exception(str(e))


def obtener_compra(id):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        if not _compra_existe(cursor, id):
            cursor.close()
            return None, "Compra no encontrada"

        cursor.execute("""
            SELECT c.id, c.proveedor_id, p.nombre, c.corte_id, c.usuario_id,
                   c.fecha, c.total, c.descripcion
            FROM compras c
            JOIN proveedores p ON p.id = c.proveedor_id
            WHERE c.id = %s AND c.eliminada = 0
        """, (id,))
        fila = cursor.fetchone()
        cursor.close()

        com = compra(fila[0], fila[1], fila[3], fila[4], fila[5], fila[6], fila[7])
        d = com.toDic()
        d['nombre_proveedor'] = fila[2]
        return d, None
    except Exception as e:
        raise Exception(str(e))


def registro_compra(proveedor_id, corte_id, usuario_id, fecha, total, descripcion):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        cursor.execute("SELECT id FROM proveedores WHERE id = %s AND activo = 1", (proveedor_id,))
        if not cursor.fetchone():
            cursor.close()
            return None, f"El proveedor con id {proveedor_id} no existe o no está activo"

        if not _existe(cursor, "cortes", corte_id):
            cursor.close()
            return None, f"El corte con id {corte_id} no existe"

        cursor.execute("SELECT id FROM usuarios WHERE id = %s AND activo = 1", (usuario_id,))
        if not cursor.fetchone():
            cursor.close()
            return None, f"El usuario con id {usuario_id} no existe o no está activo"

        if float(total) <= 0:
            cursor.close()
            return None, "El total debe ser mayor a 0"

        cursor.execute("""
            INSERT INTO compras (proveedor_id, corte_id, usuario_id, fecha, total, descripcion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (proveedor_id, corte_id, usuario_id, fecha, total, descripcion))
        con.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        return compra(nuevo_id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion).toDic(), None
    except Exception as e:
        raise Exception(str(e))


def actualizar_compra(id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        if not _compra_existe(cursor, id):
            cursor.close()
            return None, "Compra no encontrada"

        cursor.execute("SELECT id FROM proveedores WHERE id = %s AND activo = 1", (proveedor_id,))
        if not cursor.fetchone():
            cursor.close()
            return None, f"El proveedor con id {proveedor_id} no existe o no está activo"

        if not _existe(cursor, "cortes", corte_id):
            cursor.close()
            return None, f"El corte con id {corte_id} no existe"

        cursor.execute("SELECT id FROM usuarios WHERE id = %s AND activo = 1", (usuario_id,))
        if not cursor.fetchone():
            cursor.close()
            return None, f"El usuario con id {usuario_id} no existe o no está activo"

        if float(total) <= 0:
            cursor.close()
            return None, "El total debe ser mayor a 0"

        cursor.execute("""
            UPDATE compras
            SET proveedor_id = %s, corte_id = %s, usuario_id = %s,
                fecha = %s, total = %s, descripcion = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (proveedor_id, corte_id, usuario_id, fecha, total, descripcion, id))
        con.commit()
        cursor.close()
        return compra(id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion).toDic(), None
    except Exception as e:
        raise Exception(str(e))


def eliminar_compra(id):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        if not _compra_existe(cursor, id):
            cursor.close()
            return False, "Compra no encontrada"

        cursor.execute(
            "UPDATE compras SET eliminada = 1, updated_at = CURRENT_TIMESTAMP WHERE id = %s", (id,)
        )
        con.commit()
        cursor.close()
        return True, None
    except Exception as e:
        raise Exception(str(e))