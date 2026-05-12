from flask import current_app
from models.proveedor_model import proveedor

def listado_proveedores():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT ID_Proveedor, PROO_Nombre, PROO_Contacto, PROODireccion, ID_Compra FROM proveedor"
    c.execute(sql)
    datos = c.fetchall()
    lista = []
    for p in datos:
        item = proveedor(
            id        = p[0],
            nombre    = p[1],
            contacto  = p[2],
            direccion = p[3],
            compra    = p[4]
        ).todic()
        lista.append(item)
    c.close()
    return lista

def registrar_proveedor(nombre, contacto, direccion, compra):
    c = current_app.mysql.connection.cursor()
    sql = """
        INSERT INTO proveedor (PROO_Nombre, PROO_Contacto, PROODireccion, ID_Compra)
        VALUES (%s, %s, %s, %s)
    """
    c.execute(sql, (nombre, contacto, direccion, compra))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    c.close()
    return proveedor(id, nombre, contacto, direccion, compra).todic()

def actualizar_proveedor(id, nombre, contacto, direccion, compra):
    c = current_app.mysql.connection.cursor()
    sql = """
        UPDATE proveedor
        SET PROO_Nombre=%s, PROO_Contacto=%s, PROODireccion=%s, ID_Compra=%s
        WHERE ID_Proveedor=%s
    """
    c.execute(sql, (nombre, contacto, direccion, compra, id))
    current_app.mysql.connection.commit()
    filas = c.rowcount
    c.close()
    return filas > 0

def eliminar_proveedor(id):
    c = current_app.mysql.connection.cursor()
    sql = "DELETE FROM proveedor WHERE ID_Proveedor = %s"
    c.execute(sql, (id,))
    current_app.mysql.connection.commit()
    filas = c.rowcount
    c.close()
    return filas > 0

def existe_proveedor(id):
    c = current_app.mysql.connection.cursor()
    c.execute("SELECT ID_Proveedor FROM proveedor WHERE ID_Proveedor = %s", (id,))
    dato = c.fetchone()
    c.close()
    return dato is not None