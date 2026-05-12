from flask import current_app
from models.compra_model import compra

def listado_compras():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT ID_Compra, proveedor_id, corte_id, usuario_id, COM_Fecha, COM_Total, COM_Descripcion FROM compra"
    c.execute(sql)
    datos = c.fetchall()
    lista = []
    for p in datos:
        item = compra(
            id           = p[0],
            proveedor_id = p[1],
            corte_id     = p[2],
            usuario_id   = p[3],
            fecha        = p[4],
            total        = p[5],
            descripcion  = p[6]
        ).toDic()
        lista.append(item)
    c.close()
    return lista

def registrar_compra(proveedor_id, corte_id, usuario_id, fecha, total, descripcion):
    c = current_app.mysql.connection.cursor()
    sql = """
        INSERT INTO compra (proveedor_id, corte_id, usuario_id, COM_Fecha, COM_Total, COM_Descripcion)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    c.execute(sql, (proveedor_id, corte_id, usuario_id, fecha, total, descripcion))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    c.close()
    return compra(id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion).toDic()

def actualizar_compra(id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion):
    c = current_app.mysql.connection.cursor()
    sql = """
        UPDATE compra
        SET proveedor_id=%s, corte_id=%s, usuario_id=%s, COM_Fecha=%s, COM_Total=%s, COM_Descripcion=%s
        WHERE ID_Compra=%s
    """
    c.execute(sql, (proveedor_id, corte_id, usuario_id, fecha, total, descripcion, id))
    current_app.mysql.connection.commit()
    filas = c.rowcount
    c.close()
    return filas > 0

def eliminar_compra(id):
    c = current_app.mysql.connection.cursor()
    sql = "DELETE FROM compra WHERE ID_Compra = %s"
    c.execute(sql, (id,))
    current_app.mysql.connection.commit()
    filas = c.rowcount
    c.close()
    return filas > 0

def existe_compra(id):
    c = current_app.mysql.connection.cursor()
    c.execute("SELECT ID_Compra FROM compra WHERE ID_Compra = %s", (id,))
    dato = c.fetchone()
    c.close()
    return dato is not None