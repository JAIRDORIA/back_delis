from flask import current_app
from models.compra_model import compra

def listado_compra():
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()
        sql = "SELECT id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion FROM compras WHERE eliminada = 0"
        cursor.execute(sql)
        datos = cursor.fetchall()
        lista_compras = []
        for fila in datos:
            com = compra(fila[0], fila[1], fila[2], fila[3], fila[4], fila[5], fila[6])
            lista_compras.append(com.toDic())
        cursor.close()
        return lista_compras
    except Exception as e:
        raise Exception(str(e))

def registro_compra(proveedor_id, corte_id, usuario_id, fecha, total, descripcion):
    c = current_app.mysql.connection.cursor()
    sql = """INSERT INTO compras (proveedor_id, corte_id, usuario_id, fecha, total, descripcion) 
             VALUES (%s, %s, %s, %s, %s, %s)"""
    c.execute(sql, (proveedor_id, corte_id, usuario_id, fecha, total, descripcion))
    current_app.mysql.connection.commit()
    c.close()
    return compra(None, proveedor_id, corte_id, usuario_id, fecha, total, descripcion).toDic()