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

def crear_combos(nombre, descripcion, precio):
    c = current_app.mysql.connection.cursor()
    # Usamos 1 por defecto para 'activo' y NOW() para las fechas
    sql = """INSERT INTO combos(nombre, descripcion, precio, activo, created_at, updated_at)
             VALUES (%s, %s, %s, 1, NOW(), NOW())"""
    c.execute(sql, (nombre, descripcion, precio))
    current_app.mysql.connection.commit()
    
    return {"nombre": nombre, "precio": precio}