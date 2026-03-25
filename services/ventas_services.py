from flask import current_app
from models.venta_model import Ventas

def listado_ventas():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, cliente_id, corte_id, usuario_id, nombre_cliente, \
           fecha_venta, fecha_entrega, total, total_abonado, \
           saldo_pendiente, estado FROM ventas"
    c.execute(sql)
    datos = c.fetchall()
    print(datos)
    lista = []
    for p in datos:
        venta = Ventas(
            id               = p[0],
            cliente_id       = p[1],
            corte_id         = p[2],
            usuario_id       = p[3],
            nombre_cliente   = p[4],
            fecha_venta      = p[5],
            fecha_entrega    = p[6],
            total            = p[7],
            total_abonado    = p[8],
            saldo_pendiente  = p[9],
            estado           = p[10]
        ).to_dict()
        lista.append(venta)
    
    return lista

    