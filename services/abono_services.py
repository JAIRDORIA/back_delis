from flask import current_app
from models.abonos_model import Abono
from datetime import datetime


def listado_abonos():
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT id, venta_id, corte_id, usuario_id,
               monto, fecha, observacion, medio_pago
        FROM abonos
    """)
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
    return lista


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