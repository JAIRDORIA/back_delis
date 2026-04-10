from flask import current_app
from models.proveedores_model import proveedores

def listado_proveedores():
    try:
        con = current_app.mysql.connection
        cursor = con.cursor()

        sql = "SELECT * FROM proveedores"
        cursor.execute(sql)

        datos = cursor.fetchall()
        lista_proveedores = []

        for fila in datos:
            pro = proveedores(fila[0], fila[1], fila[2], fila[3], fila[4])
            lista_proveedores.append(pro.todic())

        cursor.close()
        return lista_proveedores

    except Exception as e:
        raise Exception(str(e))
    
def registro_proveedor(id, nombre, telefono, direccion, email):
    c = current_app.mysql.connection.cursor()
    sql = "INSERT INTO proveedores (nombre, telefono, direccion, email) VALUES (%s, %s, %s, %s)"
    c.execute(sql, (nombre, telefono, direccion, email))  # ✅ Sin id, es AUTO_INCREMENT
    current_app.mysql.connection.commit()
    c.close()
    return proveedores(id, nombre, telefono, direccion, email).todic()