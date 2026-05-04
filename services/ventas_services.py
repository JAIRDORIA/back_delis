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
    
    
    
    
    
    

def obtener_venta_detalle(id):
    c = current_app.mysql.connection.cursor()

    # datos de la venta
    c.execute("""
        SELECT v.id, v.cliente_id, cl.nombre, v.corte_id,
               v.usuario_id, v.fecha_venta, v.fecha_entrega,
               v.total, v.total_abonado, v.saldo_pendiente, v.estado
        FROM ventas v
        JOIN clientes cl ON cl.id = v.cliente_id
        WHERE v.id = %s
    """, (id,))
    venta = c.fetchone()

    if not venta:
        c.close()
        return None

    # detalle de productos
    c.execute("""
        SELECT producto_id, nombre_producto,
               cantidad, precio_unitario, subtotal
        FROM venta_detalle
        WHERE venta_id = %s
    """, (id,))
    detalle = c.fetchall()

    # abonos de la venta
    c.execute("""
        SELECT id, monto, fecha, medio_pago, observacion
        FROM abonos
        WHERE venta_id = %s
        ORDER BY fecha ASC
    """, (id,))
    abonos = c.fetchall()

    c.close()

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
        "estado"          : venta[10],
        "detalle"         : [
            {
                "producto_id"    : d[0],
                "nombre_producto": d[1],
                "cantidad"       : d[2],
                "precio_unitario": float(d[3]),
                "subtotal"       : float(d[4])
            } for d in detalle
        ],
        "abonos": [
            {
                "id"         : a[0],
                "monto"      : float(a[1]),
                "fecha"      : str(a[2]),
                "medio_pago" : a[3],
                "observacion": a[4]
            } for a in abonos
        ]
    }
    

def registro(cliente_id, corte_id, usuario_id,
             fecha_entrega, total, detalle, abono_inicial=None):
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
            INSERT INTO venta_detalle (venta_id, producto_id,
                                       nombre_producto, cantidad,
                                       precio_unitario)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            venta_id,
            item["producto_id"],
            item["nombre_producto"],
            item["cantidad"],
            item["precio_unitario"]
        ))

    # 3. insertar abono inicial si el cliente pago algo
    if abono_inicial and abono_inicial.get("monto", 0) > 0:
        c.execute("""
            INSERT INTO abonos (venta_id, corte_id, usuario_id,
                                monto, fecha, observacion, medio_pago)
            VALUES (%s, %s, %s, %s, NOW(), %s, %s)
        """, (
            venta_id,
            corte_id,
            usuario_id,
            abono_inicial["monto"],
            abono_inicial.get("observacion", None),
            abono_inicial.get("medio_pago", "efectivo")
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