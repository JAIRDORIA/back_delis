from flask import current_app
from models.venta_model import Ventas
from datetime import datetime


def listado_ventas(pagina=1, limite=20, corte_id=None):
    offset = (pagina - 1) * limite
    c = current_app.mysql.connection.cursor()

    # Si no se especifica un corte, se trabaja con el corte abierto
    if corte_id is None:
        c.execute("SELECT id FROM cortes WHERE estado = 'abierto' LIMIT 1")
        corte_abierto = c.fetchone()
        corte_actual = corte_abierto[0] if corte_abierto else None
    else:
        corte_actual = corte_id

    # Construir cláusulas WHERE según si tenemos un corte de referencia
    if corte_actual is not None:
        where_clause = """
            WHERE v.estado != 'anulada'
              AND (v.corte_id = %(corte)s OR (v.saldo_pendiente > 0 AND v.corte_id != %(corte)s))
        """
        params_count = {'corte': corte_actual}
        params_data  = {'corte': corte_actual, 'limite': limite, 'offset': offset}
    else:
        # Si no hay corte abierto y no se pidió uno específico, mostrar todas las activas
        where_clause = "WHERE v.estado != 'anulada'"
        params_count = {}
        params_data  = {'limite': limite, 'offset': offset}

    # Consulta de total
    sql_count = f"""
        SELECT COUNT(*)
        FROM ventas v
        JOIN clientes cl ON cl.id = v.cliente_id
        {where_clause}
    """
    c.execute(sql_count, params_count)
    total = c.fetchone()[0]

    # Consulta de datos paginada
    sql_data = f"""
        SELECT v.id, v.cliente_id, cl.nombre, v.corte_id, v.usuario_id,
               v.fecha_venta, v.fecha_entrega, v.total,
               v.total_abonado, v.saldo_pendiente, v.estado
        FROM ventas v
        JOIN clientes cl ON cl.id = v.cliente_id
        {where_clause}
        ORDER BY v.id DESC
        LIMIT %(limite)s OFFSET %(offset)s
    """
    c.execute(sql_data, params_data)
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
        "total_paginas": -(-total // limite) if limite else 0,
        "datos"        : lista
    }
    
    
    
    
    
def actualizar_detalle_venta(id, nuevo_detalle):
    c = current_app.mysql.connection.cursor()

    # Verificar que la venta existe y está pendiente
    c.execute("SELECT id, total_abonado, estado FROM ventas WHERE id = %s", (id,))
    venta = c.fetchone()
    if not venta or venta[2] != 'pendiente':
        c.close()
        return None

    total_abonado = float(venta[1])

    # Borrar el detalle actual
    c.execute("DELETE FROM venta_detalle WHERE venta_id = %s", (id,))

    # Insertar los nuevos productos y calcular el nuevo total
    nuevo_total = 0
    for item in nuevo_detalle:
        subtotal = item['cantidad'] * float(item['precio_unitario'])
        c.execute("""
            INSERT INTO venta_detalle (venta_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id, item['producto_id'], item['nombre_producto'], item['cantidad'], float(item['precio_unitario']), subtotal))
        nuevo_total += subtotal

    # Actualizar la venta: total y saldo pendiente
    saldo_pendiente = nuevo_total - total_abonado
    c.execute("""
        UPDATE ventas SET total = %s, saldo_pendiente = %s WHERE id = %s
    """, (nuevo_total, saldo_pendiente, id))

    current_app.mysql.connection.commit()
    c.close()

    # Devolver el detalle actualizado (igual que el endpoint de consulta)
    return obtener_venta_detalle(id)    

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
    
    

def generar_comprobante(venta_id):
    c = current_app.mysql.connection.cursor()

    # verificar si ya existe comprobante
    c.execute("""
        SELECT id, numero, fecha_emision
        FROM comprobantes
        WHERE venta_id = %s
    """, (venta_id,))
    comp_existente = c.fetchone()

    # si no existe lo creamos
    if not comp_existente:
        # generar numero secuencial
        c.execute("SELECT COUNT(*) FROM comprobantes")
        total = c.fetchone()[0]
        numero = f"COMP-{str(total + 1).zfill(4)}"

        c.execute("""
            INSERT INTO comprobantes (venta_id, numero)
            VALUES (%s, %s)
        """, (venta_id, numero))
        current_app.mysql.connection.commit()

        c.execute("""
            SELECT id, numero, fecha_emision
            FROM comprobantes WHERE venta_id = %s
        """, (venta_id,))
        comp = c.fetchone()
    else:
        comp = comp_existente

    # traer datos completos de la venta
    c.execute("""
        SELECT v.id, cl.nombre, v.fecha_venta, v.fecha_entrega,
               v.total, v.total_abonado, v.saldo_pendiente, v.estado
        FROM ventas v
        JOIN clientes cl ON cl.id = v.cliente_id
        WHERE v.id = %s
    """, (venta_id,))
    venta = c.fetchone()

    # traer detalle de productos
    c.execute("""
        SELECT nombre_producto, cantidad,
               precio_unitario, subtotal
        FROM venta_detalle
        WHERE venta_id = %s
    """, (venta_id,))
    detalle = c.fetchall()

    c.close()

    return {
        "numero"          : comp[1],
        "fecha_emision"   : str(comp[2]),
        "venta_id"        : venta[0],
        "nombre_cliente"  : venta[1],
        "fecha_venta"     : str(venta[2]),
        "fecha_entrega"   : str(venta[3]),
        "total"           : float(venta[4]),
        "total_abonado"   : float(venta[5]),
        "saldo_pendiente" : float(venta[6]),
        "estado"          : venta[7],
        "detalle"         : [
            {
                "nombre_producto": d[0],
                "cantidad"       : d[1],
                "precio_unitario": float(d[2]),
                "subtotal"       : float(d[3])
            } for d in detalle
        ]
    }

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