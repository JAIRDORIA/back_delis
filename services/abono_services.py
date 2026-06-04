from flask import current_app
from models.abonos_model import Abono
from datetime import datetime

def listado_abonos(pagina=1, limite=20):
    offset = (pagina - 1) * limite

    c = current_app.mysql.connection.cursor()

    c.execute("SELECT COUNT(*) FROM abonos")
    total = c.fetchone()[0]

    c.execute("""
       SELECT a.id, a.venta_id, a.monto, a.medio_pago, a.fecha, a.observacion,
       a.corte_id, a.usuario_id,
       v.estado AS venta_estado,
       v.saldo_pendiente AS venta_saldo_pendiente,
       cl.nombre AS nombre_cliente
FROM abonos a
JOIN ventas v ON v.id = a.venta_id
JOIN clientes cl ON cl.id = v.cliente_id
ORDER BY a.id DESC
LIMIT %(limite)s OFFSET %(offset)s
    """, {"limite":limite,"offset": offset})
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        
        abono = Abono(
            id          = p[0],
            venta_id    = p[1],
            corte_id    = p[6],
            usuario_id  = p[7],
            monto       = p[2],
            fecha       = p[4],
            observacion = p[5],
            medio_pago  = p[3],
            venta_estado=p[8],
            venta_saldo_pendiente=p[9],
            nombre_cliente= p[10],
        ).to_dict()
        lista.append(abono)

    return {
        "total"        : total,
        "pagina"       : pagina,
        "limite"       : limite,
        "total_paginas": -(-total // limite),
        "datos"        : lista
    }


def registro(venta_id, corte_id, usuario_id, monto, fecha, observacion, medio_pago):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        INSERT INTO abonos (venta_id, corte_id, usuario_id,
                            monto, fecha, observacion, medio_pago)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (venta_id, corte_id, usuario_id, monto, fecha, observacion, medio_pago))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    
    c.close()
    return obtener_abono(id)
    
def generar_recibo(abono_id):
    c = current_app.mysql.connection.cursor()

    # traer datos del abono
    c.execute("""
        SELECT a.id, a.monto, a.fecha, a.medio_pago,
               a.observacion, a.venta_id
        FROM abonos a
        WHERE a.id = %s
    """, (abono_id,))
    abono = c.fetchone()

    if not abono:
        c.close()
        return None

    venta_id = abono[5]

    # traer datos de la venta y cliente
    c.execute("""
        SELECT v.id, cl.nombre, v.total,
               v.total_abonado, v.saldo_pendiente
        FROM ventas v
        JOIN clientes cl ON cl.id = v.cliente_id
        WHERE v.id = %s
    """, (venta_id,))
    venta = c.fetchone()

    # traer numero de comprobante si existe
    c.execute("""
        SELECT numero FROM comprobantes
        WHERE venta_id = %s
    """, (venta_id,))
    comp = c.fetchone()

    # generar numero de recibo
    numero_recibo = f"REC-{str(abono_id).zfill(4)}"

    c.close()

    return {
        "numero_recibo"   : numero_recibo,
        "abono_id"        : abono[0],
        "monto"           : float(abono[1]),
        "fecha"           : str(abono[2]),
        "medio_pago"      : abono[3],
        "observacion"     : abono[4],
        "numero_comp"     : comp[0] if comp else None,
        "nombre_cliente"  : venta[1],
        "total_venta"     : float(venta[2]),
        "total_abonado"   : float(venta[3]),
        "saldo_pendiente" : float(venta[4])
    }

def obtener_abono(id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT a.id, a.venta_id, a.monto, a.medio_pago, a.fecha, a.observacion,
               a.corte_id, a.usuario_id,
               v.estado AS venta_estado,
               v.saldo_pendiente AS venta_saldo_pendiente,
               cl.nombre AS nombre_cliente
        FROM abonos a
        JOIN ventas v ON v.id = a.venta_id
        JOIN clientes cl ON cl.id = v.cliente_id
        WHERE a.id = %s
    """, (id,))
    abono = c.fetchone()
    c.close()
    if abono:
        return Abono(
             id          = abono[0],
            venta_id    = abono[1],
            corte_id    = abono[6],
            usuario_id  =   abono[7],
            monto       = abono[2],
            fecha       = abono[4],
            observacion =   abono[5],
            medio_pago  =  abono[3],
            venta_estado=abono[8],
            venta_saldo_pendiente=abono[9],
            nombre_cliente= abono[10],
        ).to_dict()
    return None


def actualizar_abono(id, monto, fecha, observacion, medio_pago):
    abono_actual = obtener_abono(id)
    diferencia   = monto - abono_actual["monto"]

    c = current_app.mysql.connection.cursor()
    c.execute("""
        UPDATE abonos
        SET monto       = %s,
            fecha       = %s,
            observacion = %s,
            medio_pago  = %s
        WHERE id = %s
    """, (monto, fecha, observacion, medio_pago, id))

    c.execute("""
        UPDATE ventas
        SET total_abonado = total_abonado + %s
        WHERE id = %s
    """, (diferencia, abono_actual["venta_id"]))

    current_app.mysql.connection.commit()
    c.close()
    return obtener_abono(id)


def eliminar_abono(id):
    c = current_app.mysql.connection.cursor()
    c.execute("DELETE FROM abonos WHERE id = %s", (id,))
    current_app.mysql.connection.commit()
    c.close()
    return {"mensaje": f"abono {id} eliminado correctamente"}