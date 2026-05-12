from flask import current_app
from models.compra_model import compra


# ─────────────────────────────────────────────
#  HELPERS DE VALIDACIÓN DE EXISTENCIA (FK)
# ─────────────────────────────────────────────

def _existe(cursor, tabla, id):
    cursor.execute(f"SELECT id FROM {tabla} WHERE id = %s", (id,))
    return cursor.fetchone() is not None

def _compra_existe(cursor, id):
    cursor.execute("SELECT id FROM compras WHERE id = %s AND eliminada = 0", (id,))
    return cursor.fetchone() is not None


# ─────────────────────────────────────────────
#  LISTADO
# ─────────────────────────────────────────────

def listado_compra():
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()
        sql = """
            SELECT id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion
            FROM compras
            WHERE eliminada = 0
            ORDER BY fecha DESC
        """
        cursor.execute(sql)
        datos = cursor.fetchall()
        lista = []
        for fila in datos:
            com = compra(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5], fila[6])
            lista.append(com.toDic())
        cursor.close()
        return lista
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  OBTENER UNA POR ID
# ─────────────────────────────────────────────

def obtener_compra(id):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        if not _compra_existe(cursor, id):
            cursor.close()
            return None, "Compra no encontrada"

        cursor.execute(
            """SELECT id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion
               FROM compras WHERE id = %s AND eliminada = 0""",
            (id,)
        )
        fila = cursor.fetchone()
        cursor.close()
        com = compra(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5], fila[6])
        return com.toDic(), None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  REGISTRO
# ─────────────────────────────────────────────

def registro_compra(proveedor_id, corte_id, usuario_id, fecha, total, descripcion):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        # Validar FK: proveedor activo
        cursor.execute(
            "SELECT id FROM proveedores WHERE id = %s AND activo = 1", (proveedor_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            return None, f"El proveedor con id {proveedor_id} no existe o no está activo"

        # Validar FK: corte existe
        if not _existe(cursor, "cortes", corte_id):
            cursor.close()
            return None, f"El corte con id {corte_id} no existe"

        # Validar FK: usuario activo
        cursor.execute(
            "SELECT id FROM usuarios WHERE id = %s AND activo = 1", (usuario_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            return None, f"El usuario con id {usuario_id} no existe o no está activo"

        # Validar total positivo
        if float(total) <= 0:
            cursor.close()
            return None, "El total debe ser mayor a 0"

        sql = """
            INSERT INTO compras (proveedor_id, corte_id, usuario_id, fecha, total, descripcion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (proveedor_id, corte_id, usuario_id, fecha, total, descripcion))
        con.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        return compra(nuevo_id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion).toDic(), None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  ACTUALIZAR
# ─────────────────────────────────────────────

def actualizar_compra(id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        if not _compra_existe(cursor, id):
            cursor.close()
            return None, "Compra no encontrada"

        # Validar FK: proveedor activo
        cursor.execute(
            "SELECT id FROM proveedores WHERE id = %s AND activo = 1", (proveedor_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            return None, f"El proveedor con id {proveedor_id} no existe o no está activo"

        # Validar FK: corte existe
        if not _existe(cursor, "cortes", corte_id):
            cursor.close()
            return None, f"El corte con id {corte_id} no existe"

        # Validar FK: usuario activo
        cursor.execute(
            "SELECT id FROM usuarios WHERE id = %s AND activo = 1", (usuario_id,)
        )
        if not cursor.fetchone():
            cursor.close()
            return None, f"El usuario con id {usuario_id} no existe o no está activo"

        if float(total) <= 0:
            cursor.close()
            return None, "El total debe ser mayor a 0"

        sql = """
            UPDATE compras
            SET proveedor_id = %s, corte_id = %s, usuario_id = %s,
                fecha = %s, total = %s, descripcion = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        cursor.execute(sql, (proveedor_id, corte_id, usuario_id, fecha, total, descripcion, id))
        con.commit()
        cursor.close()
        return compra(id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion).toDic(), None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  ELIMINAR (soft delete → eliminada = 1)
# ─────────────────────────────────────────────

def eliminar_compra(id):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        if not _compra_existe(cursor, id):
            cursor.close()
            return False, "Compra no encontrada"

        cursor.execute(
            "UPDATE compras SET eliminada = 1, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (id,)
        )
        con.commit()
        cursor.close()
        return True, None
    except Exception as e:
        raise Exception(str(e))