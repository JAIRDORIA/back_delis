from flask import current_app
from models.abonos_model import Abono
from datetime import datetime

def listado_abonos(pagina=1, limite=20):
    offset = (pagina - 1) * limite

    c = current_app.mysql.connection.cursor()

    c.execute("SELECT COUNT(*) FROM abonos")
    total = c.fetchone()[0]

    c.execute("""
        SELECT id, venta_id, corte_id, usuario_id,
               monto, fecha, observacion, medio_pago
        FROM abonos
        LIMIT %s OFFSET %s
    """, (limite, offset))
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        abono = Abono(
            id          = p[0],
            venta_id    = p[1],
            corte_id    = p[2],
            usuario_id  = p[3],
            monto       = p[4],
            fecha       = p[5],
            observacion = p[6],
            medio_pago  = p[7]
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
        SELECT id, venta_id, corte_id, usuario_id,
               monto, fecha, observacion, medio_pago
        FROM abonos WHERE id = %s
    """, (id,))
    abono = c.fetchone()
    c.close()
    if abono:
        return Abono(
            id          = abono[0],
            venta_id    = abono[1],
            corte_id    = abono[2],
            usuario_id  = abono[3],
            monto       = abono[4],
            fecha       = abono[5],
            observacion = abono[6],
            medio_pago  = abono[7]
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