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
