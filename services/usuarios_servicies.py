from flask import current_app
from models.usuarios_model import usuarios
import bcrypt   
def listado_usuarios(pagina=1, limite=20):
    offset = (pagina - 1) * limite
    c = current_app.mysql.connection.cursor()
    
    c.execute("SELECT COUNT(*) FROM usuarios WHERE activo = 1")
    total = c.fetchone()[0]

    sql = """
        SELECT id, nombre, username, rol, activo, created_at, updated_at 
        FROM usuarios 
        WHERE activo = 1
        LIMIT %s OFFSET %s
    """
    c.execute(sql, (limite, offset))
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        usuario = usuarios(
            id            = p[0],
            nombre        = p[1],
            username      = p[2],
            password_hash = None,
            rol           = p[3],
            activo        = p[4],
            created_at    = p[5],
            updated_at    = p[6]
        ).toDic()
        lista.append(usuario)

    return {
        "datos"        : lista,
        "total"        : total,
        "pagina"       : pagina,
        "limite"       : limite,
        "total_paginas": -(-total // limite)
    } 

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
    
    sql = "UPDATE usuarios SET activo = 0 WHERE id = %s AND activo = 1"
    c.execute(sql, (id,))
    
    current_app.mysql.connection.commit()
    filas_afectadas = c.rowcount
    c.close()

    return filas_afectadas > 0

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

def actualizar(id, nombre, username, password_hash, rol):
    c = current_app.mysql.connection.cursor()
    if password_hash:
        sql = """UPDATE usuarios
                 SET nombre=%s, username=%s, password_hash=%s, rol=%s
                 WHERE id=%s"""
        c.execute(sql, (nombre, username, password_hash, rol, id))
    else:
        sql = """UPDATE usuarios
                 SET nombre=%s, username=%s, rol=%s
                 WHERE id=%s"""
        c.execute(sql, (nombre, username, rol, id))
    
    current_app.mysql.connection.commit()
    filas_afectadas = c.rowcount
    c.close()
    return filas_afectadas > 0

def existe_username_otro(username, id):
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id FROM usuarios WHERE username = %s AND id != %s"
    c.execute(sql, (username, id))
    dato = c.fetchone()
    c.close()

    return dato is not None

def login(username, password_plano):
    """
    Verifica credenciales y devuelve los datos del usuario (sin password hash)
    para generar el token. Retorna None si falla.
    """
    c = current_app.mysql.connection.cursor()
    sql = """SELECT id, nombre, username, password_hash, rol
             FROM usuarios
             WHERE username = %s AND activo = 1"""
    c.execute(sql, (username,))
    usuario = c.fetchone()
    c.close()

    if not usuario:
        return None

    hash_almacenado = usuario[3].encode('utf-8')
    if bcrypt.checkpw(password_plano.encode('utf-8'), hash_almacenado):
        return {
            "id": usuario[0],
            "nombre": usuario[1],
            "username": usuario[2],
            "rol": usuario[4]
        }
    return None


def existe_admin():
    """
    Verifica si ya existe al menos un usuario con rol 'admin' activo.
    Retorna True si existe, False si no.
    """
    c = current_app.mysql.connection.cursor()
    sql = "SELECT COUNT(*) FROM usuarios WHERE rol = 'admin' AND activo = 1"
    c.execute(sql)
    cantidad = c.fetchone()[0]
    c.close()
    return cantidad > 0