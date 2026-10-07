from flask import current_app
from models.usuarios_model import usuarios
import os
from dotenv import load_dotenv
from utils.db import cursor_ctx
load_dotenv()

CLAVE_MAESTRA = os.getenv("CLAVE_MAESTRA", "SnackFlow2026*")

def verificar_clave_maestra(clave):
    return clave == CLAVE_MAESTRA

import bcrypt   
def listado_usuarios(pagina=1, limite=20):
    offset = (pagina - 1) * limite
    with cursor_ctx() as c:
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
    with cursor_ctx() as c:
        sql = """
                 INSERT INTO usuarios (nombre, username, password_hash, rol)
                 VALUES 
                 (%s, %s, %s, %s)
                 """
        c.execute(sql, (nombre, username, password_hash, rol))
        current_app.mysql.connection.commit()
        id = c.lastrowid
    return usuarios(id, nombre, username, password_hash, rol,1, None, None).toDic()

def existe_username(username):
    with cursor_ctx() as c:
        sql = "SELECT id FROM usuarios WHERE username = %s"
        c.execute(sql, (username,))
        dato = c.fetchone()

    return dato is not None

def existe_username_otro(username, id):
    with cursor_ctx() as c:
        sql = "SELECT id FROM usuarios WHERE username = %s AND id != %s"
        c.execute(sql, (username, id))
        dato = c.fetchone()

    return dato is not None

def eliminar(id):
    with cursor_ctx() as c:
        sql = "UPDATE usuarios SET activo = 0 WHERE id = %s AND activo = 1"
        c.execute(sql, (id,))

        current_app.mysql.connection.commit()
        filas_afectadas = c.rowcount

    return filas_afectadas > 0

def obtener_usuario(id):
    with cursor_ctx() as c:
        c.execute("""
            SELECT id, nombre, username, rol, activo
            FROM usuarios 
            WHERE id = %s AND activo = 1
        """, (id,))
        usuario = c.fetchone()
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
    with cursor_ctx() as c:
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
    return filas_afectadas > 0



def login(username, password_plano):
    """
    Verifica credenciales y devuelve los datos del usuario (sin password hash)
    para generar el token. Retorna None si falla.
    """
    with cursor_ctx() as c:
        sql = """SELECT id, nombre, username, password_hash, rol
                 FROM usuarios
                 WHERE username = %s AND activo = 1"""
        c.execute(sql, (username,))
        usuario = c.fetchone()

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
    with cursor_ctx() as c:
        sql = "SELECT COUNT(*) FROM usuarios WHERE rol = 'admin' AND activo = 1"
        c.execute(sql)
        cantidad = c.fetchone()[0]
    return cantidad > 0

def eliminar(id):
    if int(id) == 1:
        return None  

    with cursor_ctx() as c:
        sql = "UPDATE usuarios SET activo = 0 WHERE id = %s AND activo = 1"
        c.execute(sql, (id,))
        current_app.mysql.connection.commit()
        filas_afectadas = c.rowcount
    return filas_afectadas > 0


CLAVE_MAESTRA = "SnackFlow2026*"  

def verificar_clave_maestra(clave):
    return clave == CLAVE_MAESTRA

def cambiar_password_maestra(username, nueva_password):
    with cursor_ctx() as c:
        c.execute("SELECT id FROM usuarios WHERE username = %s AND activo = 1", (username,))
        usuario = c.fetchone()
    if not usuario:
        return None
    nuevo_hash = bcrypt.hashpw(nueva_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    with cursor_ctx() as c:
        c.execute("UPDATE usuarios SET password_hash = %s WHERE username = %s", (nuevo_hash, username))
        current_app.mysql.connection.commit()
    return True

def obtener_usuario_por_username(username):
    with cursor_ctx() as c:
        sql = """
            SELECT id, nombre, username, rol, activo
            FROM usuarios
            WHERE username = %s AND activo = 1
        """

        c.execute(sql, (username,))
        usuario = c.fetchone()

    if usuario:
        return {
            "id": usuario[0],
            "nombre": usuario[1],
            "username": usuario[2],
            "rol": usuario[3],
            "activo": usuario[4]
        }

    return None