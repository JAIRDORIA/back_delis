from flask import current_app
from models.inventario_model import inventarios

def listado_inventarios():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, producto_id, stock_actual, unidades_sueltas, stock_minimo, updated_at FROM inventarios"
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