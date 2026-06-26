import re
from flask import current_app
from models.proveedor_model import proveedores


# ─────────────────────────────────────────────
#  HELPERS DE VALIDACIÓN
# ─────────────────────────────────────────────

def _validar_nombre(nombre):
    """
    Valida el nombre del proveedor
    ✅ No vacío
    ✅ SIN NÚMEROS
    ✅ Mínimo 3 caracteres
    ✅ Máximo 100 caracteres
    ✅ Solo letras, espacios, guiones, puntos
    """
    if not nombre:
        return False, "El nombre no puede estar vacío"
    
    nombre_limpio = nombre.strip()
    
    if len(nombre_limpio) < 3:
        return False, "El nombre debe tener al menos 3 caracteres"
    
    if len(nombre_limpio) > 100:
        return False, "El nombre no puede exceder 100 caracteres"
    
    # ✅ IMPORTANTE: No puede contener números
    if re.search(r'\d', nombre_limpio):
        return False, "❌ El nombre NO puede contener números. Ej: 'Juan García' es válido, pero 'Empresa 123' no."
    
    # Validar caracteres permitidos: letras (con acentos), espacios, guiones y puntos
    patron_valido = r'^[a-záéíóúñA-ZÁÉÍÓÚÑ\s\-\.]+$'
    if not re.match(patron_valido, nombre_limpio):
        return False, "El nombre contiene caracteres no permitidos. Use solo letras, espacios, guiones y puntos"
    
    # No permitir espacios múltiples
    if '  ' in nombre_limpio:
        return False, "El nombre no puede contener espacios múltiples consecutivos"
    
    return True, None


def _validar_email(email):
    """
    Valida el email del proveedor
    ✅ No vacío
    ✅ Formato válido
    ✅ Máximo 100 caracteres
    """
    if not email:
        return False, "El email no puede estar vacío"
    
    email_limpio = email.strip().lower()
    
    if len(email_limpio) > 100:
        return False, "El email no puede exceder 100 caracteres"
    
    # Patrón para validar email
    patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron_email, email_limpio):
        return False, "El email no tiene un formato válido. Ej: empresa@ejemplo.com"
    
    # Validaciones adicionales
    if email_limpio.startswith('.') or email_limpio.endswith('.'):
        return False, "El email no puede comenzar o terminar con un punto"
    
    if '..' in email_limpio:
        return False, "El email no puede contener puntos consecutivos"
    
    return True, None


def _validar_telefono(telefono):
    """
    Valida el teléfono del proveedor
    ✅ No vacío
    ✅ Solo números y caracteres: +, -, (), espacios
    ✅ Mínimo 7 dígitos
    ✅ Máximo 20 caracteres
    """
    if not telefono:
        return False, "El teléfono no puede estar vacío"
    
    telefono_limpio = telefono.strip()
    
    if len(telefono_limpio) < 7:
        return False, "El teléfono debe tener al menos 7 dígitos"
    
    if len(telefono_limpio) > 20:
        return False, "El teléfono no puede exceder 20 caracteres"
    
    # Validar caracteres permitidos
    if not re.match(r'^[\d\s\+\-\(\)]+$', telefono_limpio):
        return False, "El teléfono solo puede contener números, +, -, paréntesis y espacios"
    
    # Contar dígitos efectivos
    digitos = re.sub(r'\D', '', telefono_limpio)
    if len(digitos) < 7:
        return False, "El teléfono debe contener al menos 7 dígitos efectivos"
    
    return True, None


def _validar_direccion(direccion):
    """
    Valida la dirección del proveedor
    ✅ No vacía
    ✅ Mínimo 5 caracteres
    ✅ Máximo 200 caracteres
    ✅ Permite: letras, números, espacios, guiones, puntos, comas, #
    """
    if not direccion:
        return False, "La dirección no puede estar vacía"
    
    direccion_limpia = direccion.strip()
    
    if len(direccion_limpia) < 5:
        return False, "La dirección debe tener al menos 5 caracteres"
    
    if len(direccion_limpia) > 200:
        return False, "La dirección no puede exceder 200 caracteres"
    
    # Permitir más caracteres en dirección que en nombre
    patron_valido = r'^[a-záéíóúñA-ZÁÉÍÓÚÑ0-9\s\-\.#,]+$'
    if not re.match(patron_valido, direccion_limpia):
        return False, "La dirección contiene caracteres no permitidos"
    
    # No permitir espacios múltiples
    if '  ' in direccion_limpia:
        return False, "La dirección no puede contener espacios múltiples consecutivos"
    
    return True, None


def _validar_activo(activo):
    """
    Valida el campo activo
    ✅ Debe ser 0 o 1
    ✅ Tipo debe ser int o bool
    """
    if not isinstance(activo, (int, bool)):
        return False, "El campo 'activo' debe ser un número entero (0 o 1)"
    
    if activo not in [0, 1]:
        return False, "El campo 'activo' debe ser 0 (inactivo) o 1 (activo)"
    
    return True, None


def _proveedor_existe(cursor, id):
    """Verifica si existe un proveedor por ID"""
    cursor.execute("SELECT id FROM proveedores WHERE id = %s", (id,))
    return cursor.fetchone() is not None


def _email_duplicado(cursor, email, excluir_id=None):
    """Verifica si existe un email duplicado (case-insensitive)"""
    if excluir_id:
        cursor.execute(
            "SELECT id FROM proveedores WHERE LOWER(email) = LOWER(%s) AND id != %s", 
            (email, excluir_id)
        )
    else:
        cursor.execute("SELECT id FROM proveedores WHERE LOWER(email) = LOWER(%s)", (email,))
    return cursor.fetchone() is not None


def _nombre_duplicado(cursor, nombre, excluir_id=None):
    """
    ✅ NUEVO: Verifica si existe un nombre duplicado (case-insensitive)
    Los nombres de proveedores deben ser ÚNICOS (regla legal)
    """
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
#  BÚSQUEDAS ADICIONALES
# ─────────────────────────────────────────────

def obtener_proveedor_por_nombre(nombre):
    """
    ✅ NUEVO: Obtiene un proveedor por nombre (case-insensitive)
    Retorna: (proveedor_dict, None) si existe, (None, error_msg) si no existe
    """
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()
        
        cursor.execute(
            "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE LOWER(nombre) = LOWER(%s)",
            (nombre.strip(),)
        )
        fila = cursor.fetchone()
        cursor.close()
        
        if fila:
            pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            return pro.todic(), None
        return None, "Proveedor no encontrado"
    except Exception as e:
        return None, f"Error al buscar proveedor: {str(e)}"


def obtener_proveedor_por_email(email):
    """
    ✅ NUEVO: Obtiene un proveedor por email (case-insensitive)
    Retorna: (proveedor_dict, None) si existe, (None, error_msg) si no existe
    """
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()
        
        cursor.execute(
            "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE LOWER(email) = LOWER(%s)",
            (email.strip(),)
        )
        fila = cursor.fetchone()
        cursor.close()
        
        if fila:
            pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            return pro.todic(), None
        return None, "Proveedor no encontrado"
    except Exception as e:
        return None, f"Error al buscar proveedor: {str(e)}"


# ─────────────────────────────────────────────
#  LISTADO
# ─────────────────────────────────────────────

def listado_proveedores():
    """Obtiene el listado completo de proveedores"""
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores ORDER BY nombre ASC"
        )
        datos = cursor.fetchall()
        cursor.close()
        
        lista = []
        for fila in datos:
            pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            lista.append(pro.todic())
        
        return lista
    except Exception as e:
        raise Exception(f"Error al obtener listado de proveedores: {str(e)}")


def listado_proveedores_activos():
    """✅ NUEVO: Obtiene solo los proveedores activos"""
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE activo = 1 ORDER BY nombre ASC"
        )
        datos = cursor.fetchall()
        cursor.close()
        
        lista = []
        for fila in datos:
            pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            lista.append(pro.todic())
        
        return lista
    except Exception as e:
        raise Exception(f"Error al obtener proveedores activos: {str(e)}")


def buscar_proveedores_por_nombre(nombre):
    """✅ NUEVO: Busca proveedores por nombre (búsqueda parcial)"""
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()
        
        cursor.execute(
            "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE LOWER(nombre) LIKE LOWER(%s) ORDER BY nombre ASC",
            (f"%{nombre}%",)
        )
        datos = cursor.fetchall()
        cursor.close()
        
        lista = []
        for fila in datos:
            pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            lista.append(pro.todic())
        
        return lista
    except Exception as e:
        raise Exception(f"Error al buscar proveedores: {str(e)}")


def buscar_proveedores_por_email(email):
    """✅ NUEVO: Busca proveedores por email (búsqueda parcial)"""
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()
        
        cursor.execute(
            "SELECT id, nombre, telefono, direccion, email, activo FROM proveedores WHERE LOWER(email) LIKE LOWER(%s) ORDER BY nombre ASC",
            (f"%{email}%",)
        )
        datos = cursor.fetchall()
        cursor.close()
        
        lista = []
        for fila in datos:
            pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5])
            lista.append(pro.todic())
        
        return lista
    except Exception as e:
        raise Exception(f"Error al buscar proveedores: {str(e)}")


# ─────────────────────────────────────────────
#  OBTENER UNO POR ID
# ─────────────────────────────────────────────

def obtener_proveedor(id):
    """Obtiene un proveedor específico por ID"""
    try:
        con = current_app.mysql.connection
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
        raise Exception(f"Error al obtener proveedor: {str(e)}")


# ─────────────────────────────────────────────
#  REGISTRO
# ─────────────────────────────────────────────

def registro_proveedor(nombre, telefono, direccion, email):
    """
    Registra un nuevo proveedor
    ✅ Validaciones aplicadas:
    - Nombre sin números
    - Nombre único (no duplicado)
    - Email válido y único
    - Teléfono válido
    - Dirección válida
    """
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()

        # ✅ VALIDACIÓN: Nombre
        es_valido, error = _validar_nombre(nombre)
        if not es_valido:
            cursor.close()
            return None, error

        # ✅ VALIDACIÓN: Email
        es_valido, error = _validar_email(email)
        if not es_valido:
            cursor.close()
            return None, error

        # ✅ VALIDACIÓN: Teléfono
        es_valido, error = _validar_telefono(telefono)
        if not es_valido:
            cursor.close()
            return None, error

        # ✅ VALIDACIÓN: Dirección
        es_valido, error = _validar_direccion(direccion)
        if not es_valido:
            cursor.close()
            return None, error

        # ✅ VALIDACIÓN: Nombre duplicado
        if _nombre_duplicado(cursor, nombre):
            cursor.close()
            return None, f"Ya existe un proveedor con el nombre '{nombre.strip()}'. Los nombres de proveedores deben ser únicos."

        # ✅ VALIDACIÓN: Email duplicado
        if _email_duplicado(cursor, email):
            cursor.close()
            return None, f"Ya existe un proveedor con el email '{email}'"

        sql = """
            INSERT INTO proveedores (nombre, telefono, direccion, email, activo, created_at, updated_at)
            VALUES (%s, %s, %s, %s, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        cursor.execute(sql, (nombre.strip(), telefono.strip(), direccion.strip(), email.strip().lower()))
        con.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        
        return proveedores(nuevo_id, nombre.strip(), telefono.strip(), direccion.strip(), email.strip().lower(), 1).todic(), None
    
    except Exception as e:
        raise Exception(f"Error al registrar proveedor: {str(e)}")


# ─────────────────────────────────────────────
#  ACTUALIZAR
# ─────────────────────────────────────────────

def actualizar_proveedor(id, nombre, telefono, direccion, email, activo):
    """
    Actualiza un proveedor existente
    ✅ Validaciones aplicadas:
    - Proveedor existe
    - Nombre sin números
    - Nombre único (si cambió)
    - Email válido y único (si cambió)
    - Teléfono válido
    - Dirección válida
    - Activo válido (0 o 1)
    """
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()

        # Validar que existe el proveedor
        if not _proveedor_existe(cursor, id):
            cursor.close()
            return None, "Proveedor no encontrado"

        # ✅ VALIDACIÓN: Nombre
        es_valido, error = _validar_nombre(nombre)
        if not es_valido:
            cursor.close()
            return None, error

        # ✅ VALIDACIÓN: Email
        es_valido, error = _validar_email(email)
        if not es_valido:
            cursor.close()
            return None, error

        # ✅ VALIDACIÓN: Teléfono
        es_valido, error = _validar_telefono(telefono)
        if not es_valido:
            cursor.close()
            return None, error

        # ✅ VALIDACIÓN: Dirección
        es_valido, error = _validar_direccion(direccion)
        if not es_valido:
            cursor.close()
            return None, error

        # ✅ VALIDACIÓN: Activo
        es_valido, error = _validar_activo(activo)
        if not es_valido:
            cursor.close()
            return None, error

        # ✅ VALIDACIÓN: Nombre duplicado (excluir el ID actual)
        if _nombre_duplicado(cursor, nombre, excluir_id=id):
            cursor.close()
            return None, f"Ya existe otro proveedor con el nombre '{nombre.strip()}'. Los nombres de proveedores deben ser únicos."

        # ✅ VALIDACIÓN: Email duplicado (excluir el ID actual)
        if _email_duplicado(cursor, email, excluir_id=id):
            cursor.close()
            return None, f"Ya existe otro proveedor con el email '{email}'"

        sql = """
            UPDATE proveedores
            SET nombre = %s, telefono = %s, direccion = %s, email = %s, activo = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        cursor.execute(sql, (nombre.strip(), telefono.strip(), direccion.strip(), email.strip().lower(), activo, id))
        con.commit()
        cursor.close()
        
        return proveedores(id, nombre.strip(), telefono.strip(), direccion.strip(), email.strip().lower(), activo).todic(), None
    
    except Exception as e:
        raise Exception(f"Error al actualizar proveedor: {str(e)}")


# ─────────────────────────────────────────────
#  ELIMINAR (soft delete → activo = 0)
# ─────────────────────────────────────────────

def eliminar_proveedor(id):
    """
    Elimina un proveedor (soft delete)
    Marca el proveedor como inactivo (activo = 0)
    """
    try:
        con = current_app.mysql.connection
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
        raise Exception(f"Error al eliminar proveedor: {str(e)}")