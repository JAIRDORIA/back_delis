from flask import current_app
from models.venta_model import Ventas
from datetime import datetime


def listado_ventas(pagina=1, limite=20):
    offset = (pagina - 1) * limite
    c = current_app.mysql.connection.cursor()

    c.execute("SELECT COUNT(*) FROM ventas")
    total = c.fetchone()[0]

    c.execute("""
        SELECT v.id, v.cliente_id, c.nombre, v.corte_id, v.usuario_id,
               v.fecha_venta, v.fecha_entrega, v.total,
               v.total_abonado, v.saldo_pendiente, v.estado
        FROM ventas v
        JOIN clientes c ON c.id = v.cliente_id
        LIMIT %s OFFSET %s
    """, (limite, offset))
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        venta = Ventas(
            id              = p[0],
            cliente_id      = p[1],
            nombre_cliente  = p[2],
            corte_id        = p[3],
            usuario_id      = p[4],
            fecha_venta     = p[5],
            fecha_entrega   = p[6],
            total           = p[7],
            total_abonado   = p[8],
            saldo_pendiente = p[9],
            estado          = p[10]
        ).to_dict()
        lista.append(venta)

    return {
        "total"        : total,
        "pagina"       : pagina,
        "limite"       : limite,
        "total_paginas": -(-total // limite),
        "datos"        : lista
    }
    
    
    
    


def registro(cliente_id, corte_id, usuario_id, fecha_entrega, total, detalle):
    c = current_app.mysql.connection.cursor()

    # 1. insertar la venta
    c.execute("""
        INSERT INTO ventas (cliente_id, corte_id, usuario_id,
                            fecha_entrega, total)
        VALUES (%s, %s, %s, %s, %s)
    """, (cliente_id, corte_id, usuario_id, fecha_entrega, total))

    venta_id = c.lastrowid

    # 2. insertar cada producto del detalle
    for item in detalle:
        c.execute("""
            INSERT INTO venta_detalle (venta_id, producto_id, nombre_producto,
                                       cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            venta_id,
            item["producto_id"],
            item["nombre_producto"],
            item["cantidad"],
            item["precio_unitario"]
        ))

    current_app.mysql.connection.commit()
    c.close()
    return obtener_venta(venta_id)
    
    

def obtener_venta(id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT v.id, v.cliente_id, c.nombre, v.corte_id, v.usuario_id,
               v.fecha_venta, v.fecha_entrega, v.total,
               v.total_abonado, v.saldo_pendiente, v.estado
        FROM ventas v
        JOIN clientes c ON c.id = v.cliente_id
        WHERE v.id = %s
    """, (id,))
    venta = c.fetchone()
    c.close()
    if venta:
        return {
            "id"              : venta[0],
            "cliente_id"      : venta[1],
            "nombre_cliente"  : venta[2],
            "corte_id"        : venta[3],
            "usuario_id"      : venta[4],
            "fecha_venta"     : str(venta[5]),
            "fecha_entrega"   : str(venta[6]),
            "total"           : float(venta[7]),
            "total_abonado"   : float(venta[8]),
            "saldo_pendiente" : float(venta[9]),
            "estado"          : venta[10]
        }
    return None


def actualizar_venta(id, fecha_entrega, total, estado):
    # total_abonado ya no se toca aqui
    try:
        fecha_entrega = datetime.strptime(
            fecha_entrega, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        pass

    c = current_app.mysql.connection.cursor()
    c.execute("""
        UPDATE ventas
        SET fecha_entrega = %s,
            total         = %s,
            estado        = %s
        WHERE id = %s
    """, (fecha_entrega, total, estado, id))
    current_app.mysql.connection.commit()
    c.close()
    return obtener_venta(id)

def anular_venta(id):
    c = current_app.mysql.connection.cursor()
    
    # 1. Cambiar estado a anulada (dispara el trigger)
    c.execute("""
        UPDATE ventas SET estado = 'anulada'
        WHERE id = %s
    """, (id,))
    
    # 2. Resetear total_abonado a 0
    # lo hacemos aqui y no en el trigger para evitar
    # el error de MySQL de tabla en uso
    c.execute("""
        UPDATE ventas SET total_abonado = 0
        WHERE id = %s
    """, (id,))
    
    current_app.mysql.connection.commit()
    c.close()
    return obtener_venta(id)