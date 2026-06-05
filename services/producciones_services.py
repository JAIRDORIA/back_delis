from flask import current_app
from models.producciones_model import producciones

def listado_producciones(pagina=1, limite=20):
    offset = (pagina - 1) * limite
    c = current_app.mysql.connection.cursor()

    c.execute("SELECT COUNT(*) FROM producciones")
    total = c.fetchone()[0]

    sql = """
    SELECT p.id, p.producto_id, p.cantidad, p.unidades_sueltas,
           p.usuario_id, u.nombre as nombre_usuario, 
           pr.nombre as nombre_producto,
           p.fecha, p.observacion, p.created_at
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
        # Ahora con 10 columnas (incluyendo los nuevos nombres)
        lista.append({
            "id":                 p[0],
            "producto_id":        p[1],
            "cantidad":           p[2],
            "unidades_sueltas":   p[3],
            "usuario_id":         p[4],
            "nombre_usuario":     p[5],      
            "nombre_producto":    p[6],     
            "fecha":          str(p[7]),          
            "observacion":        p[8],         
            "created_at":     str(p[9]) if p[9] else None
        })
        
    return {
        "datos": lista,
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": -(-total // limite)
    }

def registro(producto_id, cantidad, unidades_sueltas, usuario_id, fecha, observacion):
    c = current_app.mysql.connection.cursor()
    sql = """
             INSERT INTO producciones (producto_id, cantidad, unidades_sueltas, usuario_id, fecha, observacion)
             VALUES 
             (%s, %s, %s, %s, %s, %s)
             """
    c.execute(sql, (producto_id, cantidad, unidades_sueltas, usuario_id, fecha, observacion))
    current_app.mysql.connection.commit()
    id = c.lastrowid
    c.close()
    return producciones(id, producto_id, cantidad, unidades_sueltas , usuario_id, fecha, observacion, None).toDic() 


def obtener_produccion(id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT p.id, p.producto_id, pr.nombre as nombre_producto, 
               p.cantidad, p.unidades_sueltas,
               p.usuario_id, u.nombre as nombre_usuario,
               p.fecha, p.observacion, p.created_at
        FROM producciones p
        JOIN productos pr ON pr.id = p.producto_id
        JOIN usuarios u ON u.id = p.usuario_id
        WHERE p.id = %s
    """, (id,))
    dato = c.fetchone()
    c.close()
    if dato:
        return {
            "id":                dato[0],
            "producto_id":       dato[1],
            "nombre_producto":   dato[2],
            "cantidad":          dato[3],
            "unidades_sueltas":  dato[4],
            "usuario_id":        dato[5],
            "nombre_usuario":    dato[6],
            "fecha":          str(dato[7]),
            "observacion":        dato[8],
            "created_at":     str(dato[9]) if dato[9] else None
        }
    return None