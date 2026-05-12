from flask import current_app
from models.cliente_model import cliente

def listado_clientes(page, per_page):
    """Lista clientes con paginación (RF13)[cite: 1, 17]."""
    offset = (page - 1) * per_page
    c = current_app.mysql.connection.cursor()
    
    c.execute("SELECT COUNT(*) FROM clientes WHERE activo = 1")
    total = c.fetchone()[0]
    
    sql = """SELECT id, nombre, telefono, direccion, email, activo, created_at, updated_at 
             FROM clientes WHERE activo = 1 LIMIT %s OFFSET %s"""
    c.execute(sql, (per_page, offset))
    datos = c.fetchall()
    
    lista = [cliente(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]).toDic() for p in datos]
    return {"items": lista, "total": total, "page": page, "per_page": per_page}

def obtener_cliente(id):
    """
    Obtiene el detalle de un cliente específico (RF14).
    Esta es la función que el error indica como faltante.
    """
    c = current_app.mysql.connection.cursor()
    sql = """SELECT id, nombre, telefono, direccion, email, activo, created_at, updated_at 
             FROM clientes WHERE id = %s AND activo = 1"""
    c.execute(sql, (id,))
    p = c.fetchone()
    if p:
        return cliente(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]).toDic()
    return None

def existe_email(email, excluir_id=None):
    """Verifica si el email ya existe para evitar duplicados."""
    c = current_app.mysql.connection.cursor()
    if excluir_id:
        c.execute("SELECT id FROM clientes WHERE email = %s AND id != %s", (email, excluir_id))
    else:
        c.execute("SELECT id FROM clientes WHERE email = %s", (email,))
    return c.fetchone() is not None

def crear_clientes(nombre, telefono, direccion, email):
    """Registrar un nuevo cliente (RF10)[cite: 1, 14]."""
    if existe_email(email):
        return {"error": "El correo electrónico ya está registrado"}, 400
    c = current_app.mysql.connection.cursor()
    sql = """INSERT INTO clientes (nombre, telefono, direccion, email, activo, created_at, updated_at)
             VALUES (%s, %s, %s, %s, 1, NOW(), NOW())"""
    c.execute(sql, (nombre, telefono, direccion, email))
    current_app.mysql.connection.commit()
    return {"nombre": nombre, "email": email}

def service_actualizar_cliente(id, nombre, telefono, direccion, email):
    """Editar la información de los clientes (RF11)[cite: 1, 15]."""
    c = current_app.mysql.connection.cursor()
    sql = """UPDATE clientes SET nombre=%s, telefono=%s, direccion=%s, email=%s, updated_at=NOW() 
             WHERE id=%s AND activo = 1"""
    c.execute(sql, (nombre, telefono, direccion, email, id))
    current_app.mysql.connection.commit()
    return {"id": id, "nombre": nombre}

def service_eliminar_cliente(id):
    """Eliminar clientes mediante borrado lógico (RF12)[cite: 1, 16]."""
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT id, nombre, telefono, direccion, email, activo
        FROM clientes
        WHERE id = %s AND activo = 1
    """, (id,))
    cliente = c.fetchone()
    c.close()
    if cliente:
        return {
            "id"       : cliente[0],
            "nombre"   : cliente[1],
            "telefono" : cliente[2],
            "direccion": cliente[3],
            "email"    : cliente[4],
            "activo"   : cliente[5]
        }
    return None


def clientes_top(limite=5):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT 
            cl.id,
            cl.nombre,
            cl.telefono,
            COUNT(v.id)        AS total_ventas,
            COALESCE(SUM(v.total), 0) AS total_comprado,
            COALESCE(SUM(v.saldo_pendiente), 0) AS saldo_pendiente
        FROM clientes cl
        LEFT JOIN ventas v ON v.cliente_id = cl.id
            AND v.estado != 'anulada'
        WHERE cl.activo = 1
        GROUP BY cl.id, cl.nombre, cl.telefono
        ORDER BY total_comprado DESC
        LIMIT %s
    """, (limite,))
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        lista.append({
            "id"              : p[0],
            "nombre"          : p[1],
            "telefono"        : p[2],
            "total_ventas"    : p[3],
            "total_comprado"  : float(p[4]),
            "saldo_pendiente" : float(p[5])
        })
    return lista