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
            id=p[0], nombre=p[1], descripcion=p[2], precio=p[3],
            activo=p[4], created_at=p[5], updated_at=p[6]
        ).toDic()
        lista.append(combo)
    return lista

def existe_combo(nombre):
    """Verifica si ya existe un combo con ese nombre para evitar duplicados."""
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id FROM combos WHERE nombre = %s"
    c.execute(sql, (nombre,))
    return c.fetchone() is not None

def crear_combos(nombre, descripcion, precio):
    # 1. Validar duplicado
    if existe_combo(nombre):
        return {"error": f"Ya existe un combo con el nombre '{nombre}'"}, 400

    # 2. Insertar si no existe
    c = current_app.mysql.connection.cursor()
    sql = """INSERT INTO combos(nombre, descripcion, precio, activo, created_at, updated_at)
             VALUES (%s, %s, %s, 1, NOW(), NOW())"""
    c.execute(sql, (nombre, descripcion, precio))
    current_app.mysql.connection.commit()
    
    return {"nombre": nombre, "precio": precio}