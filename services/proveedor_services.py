from flask import current_app
from models.proveedores_model import proveedores


# ─────────────────────────────────────────────
#  HELPERS DE VALIDACIÓN
# ─────────────────────────────────────────────

def _proveedor_existe(cursor, id):
    cursor.execute("SELECT id FROM proveedores WHERE id = %s", (id,))
    return cursor.fetchone() is not None

def _email_duplicado(cursor, email, excluir_id=None):
    if excluir_id:
        cursor.execute(
            "SELECT id FROM proveedores WHERE email = %s AND id != %s", (email, excluir_id)
        )
    else:
        cursor.execute("SELECT id FROM proveedores WHERE email = %s", (email,))
    return cursor.fetchone() is not None


# ─────────────────────────────────────────────
#  LISTADO
# ─────────────────────────────────────────────

def listado_proveedores():
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores"
        )
        datos = cursor.fetchall()
        lista = []
        for fila in datos:
            pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            lista.append(pro.todic())
        cursor.close()
        return lista
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  OBTENER UNO POR ID
# ─────────────────────────────────────────────

def obtener_proveedor(id):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()
        if not _proveedor_existe(cursor, id):
            cursor.close()
            return None, "Proveedor no encontrado"
        cursor.execute(
            "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE id = %s",
            (id,)
        )
        fila = cursor.fetchone()
        cursor.close()
        pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
        return pro.todic(), None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  REGISTRO
# ─────────────────────────────────────────────

def registro_proveedor(id, nombre, telefono, direccion, email):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        if _email_duplicado(cursor, email):
            cursor.close()
            return None, f"Ya existe un proveedor con el email '{email}'"

        sql = """
            INSERT INTO proveedores (nombre, telefono, direccion, email)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (nombre, telefono, direccion, email))
        con.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        return proveedores(nuevo_id, nombre, telefono, direccion, email).todic(), None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  ACTUALIZAR
# ─────────────────────────────────────────────

def actualizar_proveedor(id, nombre, telefono, direccion, email, activo):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        if not _proveedor_existe(cursor, id):
            cursor.close()
            return None, "Proveedor no encontrado"

        if _email_duplicado(cursor, email, excluir_id=id):
            cursor.close()
            return None, f"Ya existe otro proveedor con el email '{email}'"

        sql = """
            UPDATE proveedores
            SET nombre = %s, telefono = %s, direccion = %s, email = %s, activo = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        cursor.execute(sql, (nombre, telefono, direccion, email, activo, id))
        con.commit()
        cursor.close()
        return proveedores(id, nombre, telefono, direccion, email, activo).todic(), None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  ELIMINAR (soft delete → activo = 0)
# ─────────────────────────────────────────────

def eliminar_proveedor(id):
    try:
        con    = current_app.mysql.connection
        cursor = con.cursor()

        if not _proveedor_existe(cursor, id):
            cursor.close()
            return False, "Proveedor no encontrado"

        cursor.execute(
            "UPDATE proveedores SET activo = 0, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (id,)
        )
        con.commit()
        cursor.close()
        return True, None
    except Exception as e:
        raise Exception(str(e))