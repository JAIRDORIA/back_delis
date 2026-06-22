from flask import current_app

def listar_auditoria(pagina=1, limite=20):
    offset = (pagina - 1) * limite
    c = current_app.mysql.connection.cursor()

    # Contar total de registros
    c.execute("SELECT COUNT(*) FROM auditoria")
    total = c.fetchone()[0]

    # Obtener registros con JOIN a usuarios
    c.execute("""
        SELECT a.id, a.usuario_id, u.nombre as usuario_nombre,
               a.accion, a.tabla_afectada, a.registro_id,
               a.descripcion, a.fecha
        FROM auditoria a
        JOIN usuarios u ON u.id = a.usuario_id
        ORDER BY a.fecha DESC
        LIMIT %s OFFSET %s
    """, (limite, offset))
    
    datos = c.fetchall()
    c.close()

    return {
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": -(-total // limite) if limite else 0,
        "datos": [
            {
                "id": d[0],
                "usuario_id": d[1],
                "usuario_nombre": d[2],
                "accion": d[3],
                "tabla_afectada": d[4],
                "registro_id": d[5],
                "descripcion": d[6],
                "fecha": str(d[7])
            } for d in datos
        ]
    }