from flask import current_app, json
from models.venta_model import Ventas
from datetime import datetime
import math

def listado_ventas(pagina=1, limite=20, corte_id=None, q=None,cliente_id=None):
    offset = (pagina - 1) * limite
    c = current_app.mysql.connection.cursor()

    # Si no se especifica un corte, se trabaja con el corte abierto
    if corte_id is None:
        c.execute("SELECT id FROM cortes WHERE estado = 'abierto' LIMIT 1")
        corte_abierto = c.fetchone()
        corte_actual = corte_abierto[0] if corte_abierto else None
    else:
        corte_actual = corte_id

    # Construir cláusulas WHERE dinámicamente
    where_clause = "WHERE v.estado != 'anulada'"
    params_count = {}
    params_data = {'limite': limite, 'offset': offset}

    if cliente_id is not None:
        where_clause += " AND v.cliente_id = %(cliente_id)s"
        params_count['cliente_id'] = cliente_id
        params_data['cliente_id'] = cliente_id
    elif corte_actual is not None:
        where_clause += " AND (v.corte_id = %(corte)s OR (v.saldo_pendiente > 0 AND co.estado = 'cerrado'))"
        params_count['corte'] = corte_actual
        params_data['corte'] = corte_actual

    # Agregar búsqueda por texto (q)
    if q:
        q_param = f"%{q}%"
        where_clause += " AND (v.id LIKE %(q)s OR cl.nombre LIKE %(q)s OR v.estado LIKE %(q)s)"
        params_count['q'] = q_param
        params_data['q'] = q_param

    # Consulta de total
    sql_count = f"""
        SELECT COUNT(*)
        FROM ventas v
        JOIN clientes cl ON cl.id = v.cliente_id
        JOIN cortes co ON co.id = v.corte_id
        {where_clause}
    """
    c.execute(sql_count, params_count)
    total = c.fetchone()[0]

    # Consulta de datos paginada
    sql_data = f"""
        SELECT v.id, v.cliente_id, cl.nombre, v.corte_id, co.numero,
               v.usuario_id, v.fecha_venta, v.fecha_entrega,
               v.total, v.total_abonado, v.saldo_pendiente, v.estado
        FROM ventas v
        JOIN clientes cl ON cl.id = v.cliente_id
        JOIN cortes co ON co.id = v.corte_id
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
            corte_numero    = p[4],
            usuario_id      = p[5],
            fecha_venta     = p[6],
            fecha_entrega   = p[7],
            total           = p[8],
            total_abonado   = p[9],
            saldo_pendiente = p[10],
            estado          = p[11]
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

    # Borrar el detalle actual
    c.execute("DELETE FROM venta_detalle WHERE venta_id = %s", (id,))

    # Insertar los nuevos productos/combos y calcular el nuevo total
    nuevo_total = 0
    for item in nuevo_detalle:
        es_combo = 1 if item.get("tipo") == "combo" else 0
        combo_id = item.get("combo_id", None)

        c.execute("""
            INSERT INTO venta_detalle (venta_id, producto_id, combo_id, nombre_producto,
                                       cantidad, precio_unitario, es_combo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            id,
            item.get("producto_id"),       # None para combos
            combo_id,                       # None para productos
            item["nombre_producto"],
            item["cantidad"],
            float(item["precio_unitario"]),
            es_combo
        ))
        nuevo_total += item["cantidad"] * float(item["precio_unitario"])

    # Actualizar el total de la venta
    c.execute("""
        UPDATE ventas SET total = %s WHERE id = %s
    """, (nuevo_total, id))

    current_app.mysql.connection.commit()
    c.close()

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
               cantidad, precio_unitario, subtotal,es_combo, combo_id
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
                "subtotal"       : float(d[4]),
                "es_combo"       : d[5],   # ← Nuevo campo
                "combo_id"       : d[6]    # ← Nuevo campo
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
    
def descontar_inventario_combo(combo_id, cantidad_combos, c):
    # traer productos del combo
    c.execute("""
        SELECT cd.producto_id, cd.cantidad_unidades,
               p.unidades_por_bandeja
        FROM combo_detalle cd
        JOIN productos p ON p.id = cd.producto_id
        WHERE cd.combo_id = %s
    """, (combo_id,))
    productos = c.fetchall()

    for producto in productos:
        producto_id          = producto[0]
        unidades_necesarias  = producto[1] * cantidad_combos
        unidades_por_bandeja = producto[2]

        # traer inventario actual
        c.execute("""
            SELECT stock_actual, unidades_sueltas
            FROM inventario WHERE producto_id = %s
        """, (producto_id,))
        inv = c.fetchone()

        if inv:
            stock_actual     = inv[0]
            unidades_sueltas = inv[1]
        else:
            stock_actual     = 0
            unidades_sueltas = 0

        # calcular total disponible en unidades
        total_disponible = (stock_actual * unidades_por_bandeja) + unidades_sueltas
        total_restante   = total_disponible - unidades_necesarias

        # Fórmula corregida: permite sueltas negativas
        nuevas_bandejas = int(total_restante / unidades_por_bandeja)
        nuevas_sueltas  = total_restante - (nuevas_bandejas * unidades_por_bandeja)

        # actualizar inventario
        if inv:
            c.execute("""
                UPDATE inventario
                SET stock_actual     = %s,
                    unidades_sueltas = %s
                WHERE producto_id = %s
            """, (nuevas_bandejas, nuevas_sueltas, producto_id))
        else:
            c.execute("""
                INSERT INTO inventario (producto_id, stock_actual, unidades_sueltas)
                VALUES (%s, %s, %s)
            """, (producto_id, nuevas_bandejas, nuevas_sueltas))
            
            
            
            
            
            

def descontar_inventario_combo_personalizado(productos_personalizados, cantidad_combos, c):
    for producto in productos_personalizados:
        producto_id          = producto["producto_id"]
        unidades_necesarias  = producto["cantidad_unidades"] * cantidad_combos

        # Obtener unidades_por_bandeja del producto real
        c.execute("SELECT unidades_por_bandeja FROM productos WHERE id = %s", (producto_id,))
        prod = c.fetchone()
        if not prod:
            continue
        unidades_por_bandeja = prod[0]

        # Obtener inventario actual
        c.execute("""
            SELECT stock_actual, unidades_sueltas
            FROM inventario WHERE producto_id = %s
        """, (producto_id,))
        inv = c.fetchone()

        if inv:
            stock_actual     = inv[0]
            unidades_sueltas = inv[1]
        else:
            stock_actual     = 0
            unidades_sueltas = 0

        total_disponible = (stock_actual * unidades_por_bandeja) + unidades_sueltas
        total_restante = total_disponible - unidades_necesarias

        nuevas_bandejas = int(total_restante / unidades_por_bandeja)
        nuevas_sueltas  = total_restante - (nuevas_bandejas * unidades_por_bandeja)

        if inv:
            c.execute("""
                UPDATE inventario
                SET stock_actual     = %s,
                    unidades_sueltas = %s
                WHERE producto_id = %s
            """, (nuevas_bandejas, nuevas_sueltas, producto_id))
        else:
            c.execute("""
                INSERT INTO inventario (producto_id, stock_actual, unidades_sueltas)
                VALUES (%s, %s, %s)
            """, (producto_id, nuevas_bandejas, nuevas_sueltas))
            


            
def registro(cliente_id, corte_id, usuario_id,
             fecha_entrega, total, detalle, abonos_iniciales=None):
    c = current_app.mysql.connection.cursor()

    # obtener nombre del cliente
    c.execute("SELECT nombre FROM clientes WHERE id = %s", (cliente_id,))
    cliente = c.fetchone()
    nombre_cliente = cliente[0] if cliente else ''

    # 1. insertar la venta (ahora con nombre_cliente)
    c.execute("""
        INSERT INTO ventas (cliente_id, corte_id, usuario_id,
                            fecha_entrega, total, nombre_cliente)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (cliente_id, corte_id, usuario_id, fecha_entrega, total, nombre_cliente))

    venta_id = c.lastrowid

    # 2. insertar cada producto del detalle
    for item in detalle:
        es_combo = 1 if item.get("tipo") == "combo" else 0
        combo_id = item.get("combo_id", None)
        productos_personalizados = item.get("productos", None)
        combo_productos_json = None
        if es_combo and productos_personalizados and isinstance(productos_personalizados, list):
            combo_productos_json = json.dumps(productos_personalizados)

        c.execute("""
            INSERT INTO venta_detalle (venta_id, producto_id, nombre_producto,
                                       cantidad, precio_unitario, es_combo, combo_id,combo_productos)
            VALUES (%s, %s, %s, %s, %s, %s, %s,%s)
        """, (
            venta_id,
            item.get("producto_id"),
            item["nombre_producto"],
            item["cantidad"],
            item["precio_unitario"],
            es_combo,
            combo_id,
            combo_productos_json
        ))

        # si es combo descontar inventario con lógica de unidades y sueltas
        if es_combo:
            if productos_personalizados and isinstance(productos_personalizados, list):
                descontar_inventario_combo_personalizado(
                    productos_personalizados,
                    item["cantidad"],
                    c
                    )
            else:
                descontar_inventario_combo(
            item["combo_id"],
            item["cantidad"],
            c
        )    
        
    
    
          


    # 3. insertar abono inicial si el cliente pago algo
    if abonos_iniciales:
        for abono in abonos_iniciales:
            if abono.get("monto", 0) <= 0:
                continue
            c.execute("""
                INSERT INTO abonos (venta_id, corte_id, usuario_id,
                                    monto, fecha, observacion, medio_pago)
                VALUES (%s, %s, %s, %s, NOW(), %s, %s)
            """, (
                venta_id,
                corte_id,
                usuario_id,
                abono["monto"],
                abono.get("observacion", None),
                abono.get("medio_pago", "efectivo")
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

def revertir_inventario_detalle(venta_id):
    c = current_app.mysql.connection.cursor()
    
    # Obtener solo el detalle de los combos de la venta
    c.execute("""
        SELECT producto_id, cantidad, es_combo, combo_id, combo_productos
        FROM venta_detalle
        WHERE venta_id = %s AND es_combo = 1
    """, (venta_id,))
    detalles_combos = c.fetchall()

    for d in detalles_combos:
        producto_id = d[0]
        cantidad = d[1]          # Cantidad de combos
        es_combo = d[2]
        combo_id = d[3]
        combo_productos_json = d[4]

        # Siempre será un combo, así que podemos omitir la verificación de es_combo
        if combo_productos_json:
            # Combo personalizado: revertir usando la lista guardada
            productos_personalizados = json.loads(combo_productos_json)
            for prod in productos_personalizados:
                pid = prod["producto_id"]
                unidades_a_sumar = prod["cantidad_unidades"] * cantidad
                
                # Sumar al inventario (inverso de descontar)
                _sumar_inventario(pid, unidades_a_sumar, c)
        else:
            # Combo normal: obtener componentes del combo real
            c.execute("SELECT producto_id, cantidad_unidades FROM combo_detalle WHERE combo_id = %s", (combo_id,))
            componentes = c.fetchall()
            for comp in componentes:
                pid = comp[0]
                unidades_a_sumar = comp[1] * cantidad
                _sumar_inventario(pid, unidades_a_sumar, c)

    current_app.mysql.connection.commit()
    c.close()



def _sumar_inventario(producto_id, unidades_a_sumar, cursor):
    """
    Suma unidades a un producto respetando la lógica de bandejas/unidades sueltas.
    """
    # Obtener unidades por bandeja del producto
    cursor.execute("SELECT unidades_por_bandeja FROM productos WHERE id = %s", (producto_id,))
    prod = cursor.fetchone()
    if not prod:
        return
    unidades_por_bandeja = prod[0]

    # Obtener inventario actual
    cursor.execute("""
        SELECT stock_actual, unidades_sueltas
        FROM inventario WHERE producto_id = %s
    """, (producto_id,))
    inv = cursor.fetchone()

    if inv:
        stock_actual = inv[0]
        unidades_sueltas = inv[1]
    else:
        stock_actual = 0
        unidades_sueltas = 0

    # Calcular total disponible en unidades
    total_disponible = (stock_actual * unidades_por_bandeja) + unidades_sueltas
    total_nuevo = total_disponible + unidades_a_sumar

    # Calcular nuevas bandejas y sueltas
    nuevas_bandejas = int(total_nuevo / unidades_por_bandeja)
    nuevas_sueltas  = total_nuevo - (nuevas_bandejas * unidades_por_bandeja)
    # Actualizar inventario
    if inv:
        cursor.execute("""
            UPDATE inventario
            SET stock_actual = %s, unidades_sueltas = %s
            WHERE producto_id = %s
        """, (nuevas_bandejas, nuevas_sueltas, producto_id))
    else:
        cursor.execute("""
            INSERT INTO inventario (producto_id, stock_actual, unidades_sueltas)
            VALUES (%s, %s, %s)
        """, (producto_id, nuevas_bandejas, nuevas_sueltas))
        
       
        
def anular_venta(id):
    c = current_app.mysql.connection.cursor()
     # Obtener venta
    venta = obtener_venta(id)
    if not venta or venta['estado'] != 'pendiente':
        return None

    # Revertir inventario de combos (personalizados y normales)
    revertir_inventario_detalle(id)
    
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