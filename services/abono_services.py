from flask import current_app
from models.abonos_model import Abono
from datetime import datetime
from utils.db import cursor_ctx
from services.medios_pago_services import resolver_medio_pago

def listado_abonos(pagina=1, limite=20):
    offset = (pagina - 1) * limite

    with cursor_ctx() as c:
        c.execute("SELECT COUNT(*) FROM abonos")
        total = c.fetchone()[0]

        c.execute("""
       SELECT a.id, a.venta_id, a.monto, a.medio_pago, a.fecha, a.observacion,
       a.corte_id, a.usuario_id,
       a.medio_pago_id, a.es_domicilio, mp.nombre AS medio_pago_nombre,
       v.estado AS venta_estado,
       v.saldo_pendiente AS venta_saldo_pendiente,
       cl.nombre AS nombre_cliente
FROM abonos a
JOIN ventas v ON v.id = a.venta_id
JOIN clientes cl ON cl.id = v.cliente_id
LEFT JOIN medios_pago mp ON mp.id = a.medio_pago_id
ORDER BY a.id DESC
LIMIT %(limite)s OFFSET %(offset)s
    """, {"limite":limite,"offset": offset})
        datos = c.fetchall()

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
            medio_pago_id     = p[8],
            medio_pago_nombre = p[10],
            es_domicilio      = p[9],
            venta_estado=p[11],
            venta_saldo_pendiente=p[12],
            nombre_cliente= p[13],
        ).to_dict()
        lista.append(abono)

    return {
        "total"        : total,
        "pagina"       : pagina,
        "limite"       : limite,
        "total_paginas": -(-total // limite),
        "datos"        : lista
    }


def registro(venta_id, corte_id, usuario_id, monto, fecha, observacion,
             medio_pago, medio_pago_id=None, es_domicilio=0):
    with cursor_ctx() as c:
        c.execute("""
            INSERT INTO abonos (venta_id, corte_id, usuario_id,
                                monto, fecha, observacion, medio_pago,
                                medio_pago_id, es_domicilio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (venta_id, corte_id, usuario_id, monto, fecha, observacion,
              medio_pago, medio_pago_id, es_domicilio))
        current_app.mysql.connection.commit()
        id = c.lastrowid

    return obtener_abono(id)


def obtener_suma_abonos_por_tipo(venta_id):
    """Devuelve (pagado_productos, pagado_domicilio) de una venta.

    productos: abonos con es_domicilio = 0; domicilio: es_domicilio = 1."""
    with cursor_ctx() as c:
        c.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN es_domicilio = 0 THEN monto ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN es_domicilio = 1 THEN monto ELSE 0 END), 0)
            FROM abonos
            WHERE venta_id = %s
        """, (venta_id,))
        fila = c.fetchone()
    return float(fila[0]), float(fila[1])


def obtener_es_domicilio_abono(abono_id):
    """Devuelve 0 o 1 segun el tipo guardado del abono, o None si no existe."""
    with cursor_ctx() as c:
        c.execute("SELECT es_domicilio FROM abonos WHERE id = %s", (abono_id,))
        fila = c.fetchone()
    return int(fila[0]) if fila else None
    
def generar_recibo(abono_id):
    with cursor_ctx() as c:
        # traer datos del abono
        c.execute("""
            SELECT a.id, a.monto, a.fecha, a.medio_pago,
                   a.observacion, a.venta_id,
                   a.medio_pago_id, a.es_domicilio,
                   mp.nombre AS medio_pago_nombre
            FROM abonos a
            LEFT JOIN medios_pago mp ON mp.id = a.medio_pago_id
            WHERE a.id = %s
        """, (abono_id,))
        abono = c.fetchone()

        if not abono:
            return None

        venta_id = abono[5]

        # traer datos de la venta y cliente
        c.execute("""
            SELECT v.id, cl.nombre, v.total, v.valor_domicilio,
                   v.total_abonado, v.saldo_pendiente, v.estado
            FROM ventas v
            JOIN clientes cl ON cl.id = v.cliente_id
            WHERE v.id = %s
        """, (venta_id,))
        venta = c.fetchone()

        # lo pagado por tipo de la venta (una sola consulta agregada)
        c.execute("""
            SELECT COALESCE(SUM(CASE WHEN es_domicilio = 0 THEN monto ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN es_domicilio = 1 THEN monto ELSE 0 END), 0)
            FROM abonos
            WHERE venta_id = %s
        """, (venta_id,))
        pagado = c.fetchone()

        # traer numero de comprobante si existe
        c.execute("""
            SELECT numero FROM comprobantes
            WHERE venta_id = %s
        """, (venta_id,))
        comp = c.fetchone()

    # generar numero de recibo
    numero_recibo = f"REC-{str(abono_id).zfill(4)}"

    es_anulada = venta[6] == 'anulada'
    pagado_productos = 0.0 if es_anulada else float(pagado[0])
    pagado_domicilio = 0.0 if es_anulada else float(pagado[1])
    domicilio_pendiente = 0.0 if es_anulada else float(venta[3]) - pagado_domicilio
    productos_pendiente = 0.0 if es_anulada else (float(venta[2]) - float(venta[3])) - pagado_productos

    return {
        "numero_recibo"   : numero_recibo,
        "abono_id"        : abono[0],
        "monto"           : float(abono[1]),
        "fecha"           : str(abono[2]),
        "medio_pago"      : abono[3],
        "medio_pago_id"    : abono[6],
        "es_domicilio"     : bool(abono[7]),
        "medio_pago_nombre": abono[8],
        "observacion"     : abono[4],
        "numero_comp"     : comp[0] if comp else None,
        "nombre_cliente"  : venta[1],
        "total_venta"     : float(venta[2]),
        "valor_domicilio" : float(venta[3]),
        "domicilio_pendiente" : domicilio_pendiente,
        "productos_pendiente" : productos_pendiente,
        "total_abonado"   : float(venta[4]),
        "saldo_pendiente" : float(venta[5])
    }

def obtener_abono(id):
    with cursor_ctx() as c:
        c.execute("""
            SELECT a.id, a.venta_id, a.monto, a.medio_pago, a.fecha, a.observacion,
                   a.corte_id, a.usuario_id,
                   a.medio_pago_id, a.es_domicilio, mp.nombre AS medio_pago_nombre,
                   v.estado AS venta_estado,
                   v.saldo_pendiente AS venta_saldo_pendiente,
                   cl.nombre AS nombre_cliente
            FROM abonos a
            JOIN ventas v ON v.id = a.venta_id
            JOIN clientes cl ON cl.id = v.cliente_id
            LEFT JOIN medios_pago mp ON mp.id = a.medio_pago_id
            WHERE a.id = %s
        """, (id,))
        abono = c.fetchone()
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
            medio_pago_id     = abono[8],
            medio_pago_nombre = abono[10],
            es_domicilio      = abono[9],
            venta_estado=abono[11],
            venta_saldo_pendiente=abono[12],
            nombre_cliente= abono[13],
        ).to_dict()
    return None


def actualizar_abono(id, monto, fecha, observacion, medio_pago, medio_pago_id=None):
    abono_actual = obtener_abono(id)
    diferencia   = monto - abono_actual["monto"]

    # Si el medio no cambia y no viene cuenta, se conserva la cuenta actual
    # sin validar (permite editar solo el monto de abonos antiguos).
    if medio_pago == abono_actual.get("medio_pago") and medio_pago_id is None:
        medio_pago_id = abono_actual.get("medio_pago_id")
    else:
        medio_pago, medio_pago_id = resolver_medio_pago(medio_pago, medio_pago_id)

    with cursor_ctx() as c:
        c.execute("""
            UPDATE abonos
            SET monto        = %s,
                fecha        = %s,
                observacion  = %s,
                medio_pago   = %s,
                medio_pago_id = %s
            WHERE id = %s
        """, (monto, fecha, observacion, medio_pago, medio_pago_id, id))

        c.execute("""
            UPDATE ventas
            SET total_abonado = total_abonado + %s
            WHERE id = %s
        """, (diferencia, abono_actual["venta_id"]))

        current_app.mysql.connection.commit()

    return obtener_abono(id)


def eliminar_abono(id):
    with cursor_ctx() as c:
        c.execute("DELETE FROM abonos WHERE id = %s", (id,))
        current_app.mysql.connection.commit()
    return {"mensaje": f"abono {id} eliminado correctamente"}