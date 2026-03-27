from flask import current_app
from models.abonos_model import abonos

def listado_abonos():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, venta_id, corte_id, usuario_id, monto, fecha,observacion FROM abonos"
    c.execute(sql)
    datos = c.fetchall()

    lista = []
    for p in datos:
        abono = abonos(
            id                    = p[0],
            venta_id                = p[1],
            corte_id               = p[2],
            usuario_id          = p[3],
            monto               = p[4],
            fecha                = p[5],
            observacion            = p[6]
        ).todic()
        lista.append(abono)

    return lista        
