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

def obtener_corte(id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT id, numero, fecha_inicio, fecha_cierre, estado, saldo_inicial
        FROM cortes 
        WHERE id = %s
    """, (id,))
    corte = c.fetchone()
    c.close()
    if corte:
        return {
            "id"           : corte[0],
            "numero"       : corte[1],
            "fecha_inicio" : str(corte[2]) if corte[2] else None,
            "fecha_cierre" : str(corte[3]) if corte[3] else None,
            "estado"       : corte[4],
            "saldo_inicial": float(corte[5])
        }
    return None