from flask import current_app
from models.abonos_model import abonos
from datetime import datetime

def listado_abonos():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, venta_id,  corte_id, monto, fecha,observacion FROM abonos"
    c.execute(sql)
    datos = c.fetchall()

    lista = []
    for p in datos:
        abono = abonos(
            id                    = p[0],
            venta_id                = p[1],
            corte_id          = p[3],
            monto               = p[4],
            fecha                = p[5],
            observacion            = p[6]
        ).todic()
        lista.append(abono)

    return lista        


def registro(venta_id, corte_id, usuario_id, monto, fecha, observacion):
    
    

    c = current_app.mysql.connection.cursor()
    sql = """
    INSERT INTO abonos (venta_id, corte_id,
                        usuario_id, monto, fecha, observacion)
    VALUES (%s, %s, %s, %s, %s, %s)"""
    c.execute(sql, (venta_id, corte_id,
                    usuario_id, monto, fecha, observacion))
    current_app.mysql.connection.commit()
    id = c.lastrowid

    # Consultar el registro recién insertado
    c.execute("""
        SELECT id, venta_id, corte_id, usuario_id, 
               monto, fecha, observacion
        FROM abonos 
        WHERE id = %s
    """, (id,))
    abono = c.fetchone()
    c.close()

    return {
        "id"         : abono[0],
        "venta_id"   : abono[1],
        "corte_id"   : abono[2],
        "usuario_id" : abono[3],
        "monto"      : float(abono[4]),
        "fecha"      : str(abono[5]),
        "observacion": abono[6]
    }