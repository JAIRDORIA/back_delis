from flask import current_app
from models.inventario_model import inventarios

def listado_inventarios():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, producto_id, stock_actual, unidades_sueltas, stock_minimo, updated_at FROM inventario"
    c.execute(sql)
    datos = c.fetchall()
    
    lista = []
    for p in datos:
        inventario = inventarios(
            id               = p[0],
            producto_id      = p[1],
            stock_actual     = p[2],
            unidades_sueltas = p[3],
            stock_minimo     = p[4],
            updated_at       = p[5]
        ).toDic()
        lista.append(inventario)
    
    return lista  

def registro(producto_id):
    c = current_app.mysql.connection.cursor()
    sql = """
             INSERT INTO inventario (producto_id)
             VALUES 
             (%s)
             """
    c.execute(sql, (producto_id,))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    c.close()
    return inventarios(id, producto_id, 0, 0, 5, None).toDic()     

def existe_producto(producto_id):
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id FROM productos WHERE id = %s"
    c.execute(sql, (producto_id,))
    dato = c.fetchone()
    c.close()

    return dato is not None         

def existe_inventario(producto_id):
    c = current_app.mysql.connection.cursor()
    
    sql = "SELECT id FROM inventario WHERE producto_id = %s"
    c.execute(sql, (producto_id,))
    
    dato = c.fetchone()
    c.close()

    return dato is not None