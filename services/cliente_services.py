from flask import current_app
from models.cliente_model import cliente


def listado_cliente():
    c = current_app.mysql.conection.cursor()
    sql = "select * from producto"
    c.execute(sql)
    datos = c.fetchall()
    return datos

    