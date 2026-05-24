from flask import current_app
from models.proveedor_model import proveedores


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
    c = current_app.mysql.connection.cursor()
    sql = "SELECT ID_Proveedor, PROO_Nombre, PROO_Contacto, PROODireccion, ID_Compra FROM proveedor"
    c.execute(sql)
    datos = c.fetchall()
    lista = []
    for p in datos:
        item = proveedor(
            id        = p[0],
            nombre    = p[1],
            contacto  = p[2],
            direccion = p[3],
            compra    = p[4]
        ).todic()
        lista.append(item)
    c.close()
    return lista

def registrar_proveedor(nombre, contacto, direccion, compra):
    c = current_app.mysql.connection.cursor()
    sql = """
        INSERT INTO proveedor (PROO_Nombre, PROO_Contacto, PROODireccion, ID_Compra)
        VALUES (%s, %s, %s, %s)
    """
    c.execute(sql, (nombre, contacto, direccion, compra))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    c.close()
    return proveedor(id, nombre, contacto, direccion, compra).todic()

def actualizar_proveedor(id, nombre, contacto, direccion, compra):
    c = current_app.mysql.connection.cursor()
    sql = """
        UPDATE proveedor
        SET PROO_Nombre=%s, PROO_Contacto=%s, PROODireccion=%s, ID_Compra=%s
        WHERE ID_Proveedor=%s
    """
    c.execute(sql, (nombre, contacto, direccion, compra, id))
    current_app.mysql.connection.commit()
    filas = c.rowcount
    c.close()
    return filas > 0

def eliminar_proveedor(id):
    c = current_app.mysql.connection.cursor()
    sql = "DELETE FROM proveedor WHERE ID_Proveedor = %s"
    c.execute(sql, (id,))
    current_app.mysql.connection.commit()
    filas = c.rowcount
    c.close()
    return filas > 0

def existe_proveedor(id):
    c = current_app.mysql.connection.cursor()
    c.execute("SELECT ID_Proveedor FROM proveedor WHERE ID_Proveedor = %s", (id,))
    dato = c.fetchone()
    c.close()
    return dato is not None
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
