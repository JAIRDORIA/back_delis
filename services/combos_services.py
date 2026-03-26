from flask import current_app
from models.combos_model import combos

def listado_combos():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, nombre, descripcion, precio, activo, created_at, updated_at FROM combos"
    c.execute(sql)
    datos = c.fetchall()
    lista = []
    for p in datos:
        combo = combos(
            id=p[0],
            nombre=p[1],
            descripcion=p[2],
            precio=p[3],
            activo=p[4],
            created_at=p[5],
            updated_at=p[6]
        ).toDic()
        lista.append(combo)
    return lista

def obtener_combo(id):
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, nombre, descripcion, precio, activo, created_at, updated_at FROM combos WHERE id=%s"
    c.execute(sql, (id,))
    p = c.fetchone()
    if p:
        combo = combos(
            id=p[0],
            nombre=p[1],
            descripcion=p[2],
            precio=p[3],
            activo=p[4],
            created_at=p[5],
            updated_at=p[6]
        ).toDic()
        return combo
    return None

def crear_combos(data):
    c = current_app.mysql.connection.cursor()
    sql = """INSERT INTO combos(nombre, descripcion, precio, activo, created_at, updated_at)
             VALUES (%s, %s, %s, %s, NOW(), NOW())"""
    c.execute(sql, (data['nombre'], data['descripcion'], data['precio'], data['activo']))
    current_app.mysql.connection.commit()
    return {"mensaje": "Combo creado correctamente"}

def actualizar_combos(id, data):
    c = current_app.mysql.connection.cursor()
    sql = """UPDATE combos SET nombre=%s, descripcion=%s, precio=%s, activo=%s, updated_at=NOW()
             WHERE id=%s"""
    c.execute(sql, (data['nombre'], data['descripcion'], data['precio'], data['activo'], id))
    current_app.mysql.connection.commit()
    return {"mensaje": "Combo actualizado correctamente"}