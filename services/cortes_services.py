from flask import current_app
from models.corte_model import cortes

def listado_cortes():
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, numero, fecha_inicio, fecha_cierre, estado, \
           saldo_inicial FROM cortes"
    c.execute(sql)
    datos = c.fetchall()
    print(datos)
    lista = []
    for p in datos:
        corte = cortes(
            id               = p[0],
            numero           = p[1],
            fecha_inicio     = p[2],
            fecha_cierre     = p[3],
            estado           = p[4],
            saldo_inicial    = p[5]
        ).to_dict()
        lista.append(corte)
    
    return lista

    