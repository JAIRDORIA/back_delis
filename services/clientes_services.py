from flask import current_app
from models.cliente_model import cliente

def listado_clientes():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, nombre, telefono, direccion, email, activo, created_at, updated_at FROM clientes"
    c.execute(sql)
    datos = c.fetchall()

    lista = []
    for p in datos:
        cli = cliente(
            id=p[0], nombre=p[1], telefono=p[2], direccion=p[3],
            email=p[4], activo=p[5], created_at=p[6], updated_at=p[7]
        ).toDic()
        lista.append(cli)
    return lista

# --- NUEVA FUNCIÓN DE VALIDACIÓN ---
def existe_email(email):
    """Verifica si el email ya existe en la base de datos."""
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id FROM clientes WHERE email = %s"
    c.execute(sql, (email,))
    resultado = c.fetchone()
    return resultado is not None

def crear_clientes(nombre, telefono, direccion, email):
    # 1. Validar duplicidad antes de insertar
    if existe_email(email):
        return {"error": "El correo electrónico ya está registrado"}, 400

    c = current_app.mysql.connection.cursor()

    sql = """INSERT INTO clientes 
             (nombre, telefono, direccion, email, activo, created_at, updated_at)
             VALUES (%s, %s, %s, %s, 1, NOW(), NOW())"""

    c.execute(sql, (nombre, telefono, direccion, email))
    current_app.mysql.connection.commit()

    return {
        "nombre": nombre,
        "email": email
    }