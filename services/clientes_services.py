from flask import current_app
from models.cliente_model import cliente

def listado_clientes(page, per_page):
    """Lista clientes con paginación (RF13)[cite: 1, 17]."""
    offset = (page - 1) * per_page
    c = current_app.mysql.connection.cursor()
    
    c.execute("SELECT COUNT(*) FROM clientes WHERE activo = 1")
    total = c.fetchone()[0]
    
    sql = """SELECT id,identificacion, nombre, telefono, direccion, email, activo, created_at, updated_at 
             FROM clientes WHERE activo = 1 LIMIT %s OFFSET %s"""
    c.execute(sql, (per_page, offset))
    datos = c.fetchall()
    
    lista = [cliente(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7],p[8]).toDic() for p in datos]
    return {"items": lista, "total": total, "page": page, "per_page": per_page}

def obtener_cliente(id):
    """
    Obtiene el detalle de un cliente específico (RF14).
    Esta es la función que el error indica como faltante.
    """
    c = current_app.mysql.connection.cursor()
    sql = """SELECT id, nombre,identificacion, telefono, direccion, email, activo, created_at, updated_at 
             FROM clientes WHERE id = %s AND activo = 1"""
    c.execute(sql, (id,))
    p = c.fetchone()
    if p:
        return cliente(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7],p[8]).toDic()
    return None

def existe_email(email, excluir_id=None):
    """Verifica si el email ya existe para evitar duplicados."""
    c = current_app.mysql.connection.cursor()
    if excluir_id:
        c.execute("SELECT id FROM clientes WHERE email = %s AND id != %s", (email, excluir_id))
    else:
        c.execute("SELECT id FROM clientes WHERE email = %s", (email,))
    return c.fetchone() is not None

def crear_clientes(nombre, identificacion, telefono, direccion, email):
    # Validar unicidad de identificación
    if existe_identificacion(identificacion):
        return {"error": "Ya existe un cliente con esa identificación"}, 400
    # Validar unicidad de teléfono
    if existe_telefono(telefono):
        return {"error": "Ya existe un cliente con ese número de teléfono"}, 400
    # Validar unicidad de email
    if existe_email(email):
        return {"error": "El correo electrónico ya está registrado"}, 400

    c = current_app.mysql.connection.cursor()
    # Orden de columnas: nombre, identificacion, telefono, direccion, email
    # Orden de valores: nombre, identificacion, telefono, direccion, email
    sql = """INSERT INTO clientes (nombre, identificacion, telefono, direccion, email, activo, created_at, updated_at)
             VALUES (%s, %s, %s, %s, %s, 1, NOW(), NOW())"""
    c.execute(sql, (nombre, identificacion, telefono, direccion, email))
    current_app.mysql.connection.commit()
    id_cliente = c.lastrowid
    return {
        "id": id_cliente,
        "nombre": nombre,
        "identificacion": identificacion,
        "telefono": telefono,
        "direccion": direccion,
        "email": email
    }

def service_actualizar_cliente(id, nombre, identificacion, telefono, direccion, email):
    # Validar unicidad excluyendo al propio cliente
    if existe_identificacion(identificacion, excluir_id=id):
        return {"error": "Ya existe otro cliente con esa identificación"}, 400
    if existe_telefono(telefono, excluir_id=id):
        return {"error": "Ya existe otro cliente con ese número de teléfono"}, 400
    if email and existe_email(email, excluir_id=id):
        return {"error": "El correo ya pertenece a otro cliente"}, 400

    c = current_app.mysql.connection.cursor()
    sql = """UPDATE clientes 
             SET nombre=%s, identificacion=%s, telefono=%s, direccion=%s, email=%s, updated_at=NOW() 
             WHERE id=%s AND activo = 1"""
    c.execute(sql, (nombre, identificacion, telefono, direccion, email, id))
    current_app.mysql.connection.commit()
    return {"id": id, "nombre": nombre, "identificacion": identificacion}

def existe_telefono(telefono, excluir_id=None):
    c = current_app.mysql.connection.cursor()
    if excluir_id:
        c.execute("SELECT id FROM clientes WHERE telefono = %s AND id != %s", (telefono, excluir_id))
    else:
        c.execute("SELECT id FROM clientes WHERE telefono = %s", (telefono,))
    resultado = c.fetchone()
    c.close()
    return resultado is not None

def existe_identificacion(identificacion, excluir_id=None):
    c = current_app.mysql.connection.cursor()
    if excluir_id:
        c.execute("SELECT id FROM clientes WHERE identificacion = %s AND id != %s", (identificacion, excluir_id))
    else:
        c.execute("SELECT id FROM clientes WHERE identificacion = %s", (identificacion,))
    resultado = c.fetchone()
    c.close()
    return resultado is not None

def service_eliminar_cliente(id):
    c = current_app.mysql.connection.cursor()

    c.execute("""
        UPDATE clientes
        SET activo = 0
        WHERE id = %s
    """, (id,))

    current_app.mysql.connection.commit()

    if c.rowcount > 0:
        c.close()
        return True

    c.close()
    return False


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