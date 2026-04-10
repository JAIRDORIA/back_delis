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

def registro(nombre, username, password_hash, rol):
    c = current_app.mysql.connection.cursor()
    sql = """
             INSERT INTO usuarios (nombre, username, password_hash, rol)
             VALUES 
             (%s, %s, %s, %s)
             """
    c.execute(sql, (nombre, username, password_hash, rol))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    c.close()
    return usuarios(id, nombre, username, password_hash, rol,1, None, None).toDic()

def existe_username(username):
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id FROM usuarios WHERE username = %s"
    c.execute(sql, (username,))
    dato = c.fetchone()
    c.close()

    return dato is not None

def eliminar(id):
    c = current_app.mysql.connection.cursor()
    
    sql = "UPDATE usuarios SET activo = 0 WHERE id = %s"
    c.execute(sql, (id,))
    
    current_app.mysql.connection.commit()
    filas_afectadas = c.rowcount
    c.close()

    return filas_afectadas > 0

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

