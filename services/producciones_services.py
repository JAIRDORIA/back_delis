from flask import current_app
from models.producciones_model import producciones

def listado_producciones(pagina=1, limite=20):
    offset = (pagina - 1) * limite
    c = current_app.mysql.connection.cursor()

    c.execute("SELECT COUNT(*) FROM producciones")
    total = c.fetchone()[0]

    sql = """
    SELECT p.id, p.producto_id, pr.nombre, p.cantidad, 
           p.usuario_id, u.nombre, p.fecha, p.observacion, p.created_at
    FROM producciones p
    JOIN productos pr ON pr.id = p.producto_id
    JOIN usuarios u ON u.id = p.usuario_id
    ORDER BY p.created_at DESC
    LIMIT %s OFFSET %s
    """
    c.execute(sql, (limite, offset))
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        producto = producciones(
            id                   = p[0],
            producto_id          = p[1],
            cantidad             = p[2],
            usuario_id           = p[3],
            fecha                = p[4],
            observacion          = p[5],
            created_at           = p[6]
        ).toDic()
        lista.append(producto)
        
    return {
        "datos"        : lista,
        "total"        : total,
        "pagina"       : pagina,
        "limite"       : limite,
        "total_paginas": -(-total // limite)
    } 

def registro(producto_id, cantidad, usuario_id, fecha, observacion):
    c = current_app.mysql.connection.cursor()
    sql = """
             INSERT INTO producciones (producto_id, cantidad, usuario_id, fecha, observacion)
             VALUES 
             (%s, %s, %s, %s, %s)
             """
    c.execute(sql, (producto_id, cantidad, usuario_id, fecha, observacion))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    c.close()
    return producciones(id, producto_id, cantidad, usuario_id, fecha, observacion, None).toDic() 


def obtener_produccion(id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT p.id, p.producto_id, pr.nombre, p.cantidad, 
               p.usuario_id, p.fecha, p.observacion, p.created_at
        FROM producciones p
        JOIN productos pr ON pr.id = p.producto_id
        WHERE p.id = %s
    """, (id,))
    dato = c.fetchone()
    c.close()
    if dato:
        return {
            "id"          : dato[0],
            "producto_id" : dato[1],
            "nombre_producto": dato[2],
            "cantidad"    : dato[3],
            "usuario_id"  : dato[4],
            "fecha"       : str(dato[5]),
            "observacion" : dato[6],
            "created_at"  : str(dato[7]) if dato[7] else None
        }
    return None
   