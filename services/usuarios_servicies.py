from flask import current_app
from models.usuarios_model import usuarios

def listado_usuarios():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, nombre, username, password_hash, rol, activo, created_at, updated_at FROM usuarios"
    c.execute(sql)
    datos = c.fetchall()
    
    lista = []
    for p in datos:
        usuario = usuarios(
            id               = p[0],
            nombre           = p[1],
            username         = p[2],
            password_hash    = p[3],
            rol              = p[4],
            activo           = p[5],
            created_at       = p[6],
            updated_at       = p[7]
        ).toDic()
        lista.append(usuario)

    return lista        


def obtener_usuario(id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT id, nombre, username, rol, activo
        FROM usuarios 
        WHERE id = %s AND activo = 1
    """, (id,))
    usuario = c.fetchone()
    c.close()
    if usuario:
        return {
            "id"      : usuario[0],
            "nombre"  : usuario[1],
            "username": usuario[2],
            "rol"     : usuario[3],
            "activo"  : usuario[4]
        }
    return None