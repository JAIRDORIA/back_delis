import re
from flask import current_app
from models.proveedor_model import proveedores
from utils.db import cursor_ctx


# ─────────────────────────────────────────────
#  HELPERS DE VALIDACIÓN
# ─────────────────────────────────────────────

def _validar_nombre(nombre):
    """Valida el nombre - SIN NÚMEROS"""
    if not nombre:
        return False, "El nombre no puede estar vacío"
    
    nombre_limpio = nombre.strip()
    
    if len(nombre_limpio) < 3:
        return False, "El nombre debe tener al menos 3 caracteres"
    
    if len(nombre_limpio) > 100:
        return False, "El nombre no puede exceder 100 caracteres"
    
    # ✅ NO PUEDE CONTENER NÚMEROS
    if re.search(r'\d', nombre_limpio):
        return False, "❌ El nombre NO puede contener números. Ej: 'Juan García' es válido, pero 'Empresa 123' no."
    
    patron_valido = r'^[a-záéíóúñA-ZÁÉÍÓÚÑ\s\-\.]+$'
    if not re.match(patron_valido, nombre_limpio):
        return False, "El nombre contiene caracteres no permitidos"
    
    if '  ' in nombre_limpio:
        return False, "El nombre no puede contener espacios múltiples"
    
    return True, None


def _proveedor_existe(cursor, id):
    cursor.execute("SELECT id FROM proveedores WHERE id = %s", (id,))
    return cursor.fetchone() is not None





def _nombre_duplicado(cursor, nombre, excluir_id=None):
    """Verifica si existe un nombre duplicado"""
    if excluir_id:
        cursor.execute(
            "SELECT id FROM proveedores WHERE LOWER(nombre) = LOWER(%s) AND id != %s", 
            (nombre.strip(), excluir_id)
        )
    else:
        cursor.execute(
            "SELECT id FROM proveedores WHERE LOWER(nombre) = LOWER(%s)", 
            (nombre.strip(),)
        )
    return cursor.fetchone() is not None


# ─────────────────────────────────────────────
#  LISTADO
# ─────────────────────────────────────────────

def listado_proveedores():
    try:
        with cursor_ctx() as cursor:
            cursor.execute(
                "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores"
            )
            datos = cursor.fetchall()
            lista = []
            for fila in datos:
                pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
                lista.append(pro.todic())
        return lista
    except Exception as e:
        raise Exception(str(e))


def listado_proveedores_activos():
    """Obtiene solo los proveedores activos"""
    try:
        with cursor_ctx() as cursor:
            cursor.execute(
                "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE activo = 1"
            )
            datos = cursor.fetchall()
            lista = []
            for fila in datos:
                pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
                lista.append(pro.todic())
        return lista
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  OBTENER UNO POR ID
# ─────────────────────────────────────────────

def obtener_proveedor(id):
    try:
        with cursor_ctx() as cursor:
            if not _proveedor_existe(cursor, id):
                return None, "Proveedor no encontrado"
            cursor.execute(
                "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE id = %s",
                (id,)
            )
            fila = cursor.fetchone()
        pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
        return pro.todic(), None
    except Exception as e:
        raise Exception(str(e))


def obtener_proveedor_por_nombre(nombre):
    """Busca un proveedor por nombre"""
    try:
        with cursor_ctx() as cursor:
            cursor.execute(
                "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE LOWER(nombre) = LOWER(%s)",
                (nombre.strip(),)
            )
            fila = cursor.fetchone()
        if fila:
            pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            return pro.todic(), None
        return None, "Proveedor no encontrado"
    except Exception as e:
        raise Exception(str(e))


def buscar_proveedores_por_nombre(nombre):
    """Busca proveedores por nombre (parcial)"""
    try:
        with cursor_ctx() as cursor:
            cursor.execute(
                "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE LOWER(nombre) LIKE LOWER(%s)",
                (f"%{nombre}%",)
            )
            datos = cursor.fetchall()
            lista = []
            for fila in datos:
                pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
                lista.append(pro.todic())
        return lista
    except Exception as e:
        raise Exception(str(e))


def buscar_proveedores_por_email(email):
    """Busca proveedores por email (parcial)"""
    try:
        with cursor_ctx() as cursor:
            cursor.execute(
                "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE LOWER(email) LIKE LOWER(%s)",
                (f"%{email}%",)
            )
            datos = cursor.fetchall()
            lista = []
            for fila in datos:
                pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
                lista.append(pro.todic())
        return lista
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  REGISTRO
# ─────────────────────────────────────────────

def registro_proveedor(nombre, telefono, direccion, email):
    try:
        with cursor_ctx() as cursor:
            # ✅ VALIDACIÓN: Nombre (SIN NÚMEROS)
            es_valido, error = _validar_nombre(nombre)
            if not es_valido:
                return None, error

            # ✅ VALIDACIÓN: Nombre duplicado
            if _nombre_duplicado(cursor, nombre):
                return None, f"Ya existe un proveedor con el nombre '{nombre.strip()}'. Los nombres de proveedores deben ser únicos."

            # ✅ VALIDACIÓN: Email duplicado (original)
            

            # MISMO SQL DEL ORIGINAL (sin cambios)
            sql = """
                INSERT INTO proveedores (nombre, telefono, direccion, email)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (nombre, telefono, direccion, email))
            current_app.mysql.connection.commit()
            nuevo_id = cursor.lastrowid
        return proveedores(nuevo_id, nombre, telefono, direccion, email, 1).todic(), None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  ACTUALIZAR
# ─────────────────────────────────────────────

def actualizar_proveedor(id, nombre, telefono, direccion, email, activo):
    try:
        with cursor_ctx() as cursor:
            if not _proveedor_existe(cursor, id):
                return None, "Proveedor no encontrado"

            # ✅ VALIDACIÓN: Nombre (SIN NÚMEROS)
            es_valido, error = _validar_nombre(nombre)
            if not es_valido:
                return None, error

            # ✅ VALIDACIÓN: Nombre duplicado (excluir el ID actual)
            if _nombre_duplicado(cursor, nombre, excluir_id=id):
                return None, f"Ya existe otro proveedor con el nombre '{nombre.strip()}'. Los nombres deben ser únicos."

            # ✅ VALIDACIÓN: Email duplicado (original)
            

            # MISMO SQL DEL ORIGINAL (sin cambios)
            sql = """
                UPDATE proveedores
                SET nombre = %s, telefono = %s, direccion = %s, email = %s, activo = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            cursor.execute(sql, (nombre, telefono, direccion, email, activo, id))
            current_app.mysql.connection.commit()
        return proveedores(id, nombre, telefono, direccion, email, activo).todic(), None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  ELIMINAR (soft delete → activo = 0)
# ─────────────────────────────────────────────

def eliminar_proveedor(id):
    try:
        with cursor_ctx() as cursor:
            if not _proveedor_existe(cursor, id):
                return False, "Proveedor no encontrado"

            cursor.execute(
                "UPDATE proveedores SET activo = 0, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (id,)
            )
            current_app.mysql.connection.commit()
        return True, None
    except Exception as e:
        raise Exception(str(e))