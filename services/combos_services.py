from flask import current_app
from models.combos_model import combos

def listado_combos(page, per_page):
    """
    Lista los productos/combos disponibles con paginación (RF24).
    """
    offset = (page - 1) * per_page
    c = current_app.mysql.connection.cursor()
    
    # Obtener el total de combos activos para la metadata de paginación 
    c.execute("SELECT COUNT(*) FROM combos WHERE activo = 1")
    total = c.fetchone()[0]
    
    # Consulta paginada filtrando solo los activos 
    sql = """SELECT id, nombre, descripcion, precio_frito,precio_congelado, activo, created_at, updated_at 
             FROM combos WHERE activo = 1 LIMIT %s OFFSET %s"""
    c.execute(sql, (per_page, offset))
    datos = c.fetchall()
    
    lista = []
    for p in datos:
        combo = combos(
            id=p[0], nombre=p[1], descripcion=p[2], precio_frito=p[3],precio_congelado=p[4],
            activo=p[5], created_at=p[6], updated_at=p[7]
        ).toDic()

        # Traer productos del combo desde combo_detalle
        c.execute("""
            SELECT cd.producto_id, pr.nombre, cd.cantidad_unidades
            FROM combo_detalle cd
            JOIN productos pr ON pr.id = cd.producto_id
            WHERE cd.combo_id = %s
        """, (combo['id'],))
        prods = c.fetchall()
        combo['productos'] = [
            {'producto_id': r[0], 'nombre': r[1], 'cantidad_unidades': r[2]}
            for r in prods
        ]

        lista.append(combo)
        
    return {
        "items": lista,
        "total": total,
        "page": page,
        "per_page": per_page
    }

def existe_combo(nombre, solo_activos=True, excluir_id=None):
    c = current_app.mysql.connection.cursor()
    
    sql = "SELECT id FROM combos WHERE nombre = %s"
    params = [nombre]
    
    if solo_activos:
        sql += " AND activo = 1"
    
    if excluir_id is not None:
        sql += " AND id != %s"
        params.append(excluir_id)
    
    c.execute(sql, params)
    resultado = c.fetchone()
    c.close()
    return resultado is not None

def obtener_combo_id(id):
    """
    Obtiene el detalle de un combo específico si está activo.
    """
    c = current_app.mysql.connection.cursor()
    sql = "SELECT id, nombre, descripcion, precio_frito,precio_congelado, activo, created_at, updated_at FROM combos WHERE id = %s AND activo = 1"
    c.execute(sql, (id,))
    p = c.fetchone()
    if p:
        combo = combos(p[0], p[1], p[2], p[3], p[4], p[5], p[6],p[7]).toDic()

        # Traer productos del combo
        c.execute("""
            SELECT cd.producto_id, pr.nombre, cd.cantidad_unidades
            FROM combo_detalle cd
            JOIN productos pr ON pr.id = cd.producto_id
            WHERE cd.combo_id = %s
        """, (combo['id'],))
        prods = c.fetchall()
        combo['productos'] = [
            {'producto_id': r[0], 'nombre': r[1], 'cantidad_unidades': r[2]}
            for r in prods
        ]
        return combo
    return None

def crear_combo(nombre,precio_frito,precio_congelado, productos):
    # Solo verifica combos activos
    if existe_combo(nombre, solo_activos=True):
        return {"error": f"Ya existe un combo activo con el nombre '{nombre}'"}, 400

    c = current_app.mysql.connection.cursor()

    # 1. insertar el combo
    c.execute("""
        INSERT INTO combos (nombre, precio_frito,precio_congelado, activo, created_at, updated_at)
        VALUES (%s, %s,%s, 1, NOW(), NOW())
    """, (nombre, precio_frito,precio_congelado,))

    combo_id = c.lastrowid

    # 2. insertar cada producto del detalle
    for item in productos:
        c.execute("""
            INSERT INTO combo_detalle (combo_id, producto_id, cantidad_unidades)
            VALUES (%s, %s, %s)
        """, (
            combo_id,
            item["producto_id"],
            item["cantidad_unidades"]
        ))

    current_app.mysql.connection.commit()

    # 3. traer el combo recién creado con su detalle
    c.execute("""
        SELECT id, nombre, descripcion,precio_frito,precio_congelado, activo
        FROM combos WHERE id = %s
    """, (combo_id,))
    combo = c.fetchone()

    c.execute("""
        SELECT cd.producto_id, p.nombre, cd.cantidad_unidades
        FROM combo_detalle cd
        JOIN productos p ON p.id = cd.producto_id
        WHERE cd.combo_id = %s
    """, (combo_id,))
    detalle = c.fetchall()

    c.close()

    return {
        "id"         : combo[0],
        "nombre"     : combo[1],
        "descripcion": combo[2],
        "precio_frito"     : float(combo[3]),
        "precio_congelado" : float (combo[4]),
        "activo"     : combo[5],
        "productos"  : [
            {
                "producto_id"      : d[0],
                "nombre_producto"  : d[1],
                "cantidad_unidades": d[2]
            } for d in detalle
        ]
    }

def actualizar_combos(id, nombre, descripcion, precio_frito,precio_congelado,):
    # Verifica que no exista otro combo activo con el mismo nombre
    if existe_combo(nombre, solo_activos=True, excluir_id=id):
        return {"error": f"Ya existe otro combo activo con el nombre '{nombre}'"}, 400

    c = current_app.mysql.connection.cursor()
    sql = """UPDATE combos 
             SET nombre=%s, descripcion=%s, precio_frito=%s,precio_congelado=%s, updated_at=NOW() 
             WHERE id=%s AND activo = 1"""
    c.execute(sql, (nombre, descripcion, precio_frito,precio_congelado, id))
    current_app.mysql.connection.commit()
    return {"id": id, "nombre": nombre}

def eliminar_combos(id):
    """
    Realiza el borrado lógico de un producto (RF23).
    """
    c = current_app.mysql.connection.cursor()
    sql = "UPDATE combos SET activo = 0, updated_at = NOW() WHERE id = %s"
    c.execute(sql, (id,))
    current_app.mysql.connection.commit()
    return True
