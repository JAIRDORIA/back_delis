from flask import current_app
from models.cliente_model import cliente

def listado_clientes():
    c = current_app.mysql.connection.cursor()
    
    sql = "SELECT id, nombre, telefono, direccion, email, activo,created_at, updated_at FROM clientes"
    
    c.execute(sql)
    datos = c.fetchall()

    lista = []
    for p in datos:
        cli = cliente(
            id=p[0],
            nombre=p[1],
            telefono=p[2],
            direccion=p[3],
            email=p[4],
            activo=p[5],
            created_at=p[6],
            updated_at=p[7]
        ).toDic()

        lista.append(cli)

    return lista


def obtener_clientes(id):
    c = current_app.mysql.connection.cursor()

    sql = """SELECT id, nombre, telefono, direccion, email, activo,
             created_at, updated_at FROM clientes WHERE id = %s"""

    c.execute(sql, (id,))
    dato = c.fetchone()

    if dato:
        return cliente(
            id=dato[0],
            nombre=dato[1],
            telefono=dato[2],
            direccion=dato[3],
            email=dato[4],
            activo=dato[5],
            created_at=dato[6],
            updated_at=dato[7]
        ).toDic()

    return None


def crear_clientes(data):
    c = current_app.mysql.connection.cursor()

    sql = """INSERT INTO clientes 
             (nombre, telefono, direccion, email, activo, created_at, updated_at)
             VALUES (%s, %s, %s, %s, %s, NOW(), NOW())"""

    c.execute(sql, (
        data["nombre"],
        data["telefono"],
        data["direccion"],
        data["email"],
        data.get("activo", 1)
    ))

    current_app.mysql.connection.commit()

    return {"message": "Cliente creado"}


def actualizar_clientes(id, data):
    c = current_app.mysql.connection.cursor()

    sql = """UPDATE clientes SET 
             nombre=%s,
             telefono=%s,
             direccion=%s,
             email=%s,
             activo=%s,
             updated_at=NOW()
             WHERE id=%s"""

    c.execute(sql, (
        data["nombre"],
        data["telefono"],
        data["direccion"],
        data["email"],
        data["activo"],
        id
    ))

    current_app.mysql.connection.commit()

    return {"message": "Cliente actualizado"}


def eliminar_clientes(id):
    c = current_app.mysql.connection.cursor()

    sql = "DELETE FROM clientes WHERE id = %s"

    c.execute(sql, (id,))
    current_app.mysql.connection.commit()

    return {"message": "Cliente eliminado"}