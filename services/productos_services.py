from flask import current_app
from models.productos_model import productos
from utils.db import cursor_ctx

def listado_productos(pagina=1, limite=20, busqueda=None):
    offset = (pagina - 1) * limite
    where = "WHERE activo = 1"
    params = []
    if busqueda:
        where += " AND (nombre LIKE %s OR descripcion LIKE %s)"
        like = f"%{busqueda}%"
        params += [like, like]

    with cursor_ctx() as c:
        c.execute(f"SELECT COUNT(*) FROM productos {where}", tuple(params))
        total = c.fetchone()[0]

        sql = f"""
            SELECT id, nombre, descripcion, precio_detal, precio_almayor,unidades_por_bandeja, activo, created_at, updated_at 
            FROM productos 
            {where}
            ORDER BY id ASC
            LIMIT %s OFFSET %s
        """
        c.execute(sql, tuple(params + [limite, offset]))
        datos = c.fetchall()

    lista = []
    for p in datos:
        producto = productos(
            id                   = p[0],
            nombre               = p[1],
            descripcion          = p[2],
            precio_detal         = p[3],
            precio_almayor=p[4],
            unidades_por_bandeja = p[5],
            activo               = p[6],
            created_at           = p[7],
            updated_at           = p[8]
        ).toDic()
        lista.append(producto)

    return {
        "datos"        : lista,
        "total"        : total,
        "pagina"       : pagina,
        "limite"       : limite,
        "total_paginas": -(-total // limite)
    } 

def registro(nombre, descripcion,  precio_detal, precio_almayor, unidades_por_bandeja):
    with cursor_ctx() as c:
        sql = """
                 INSERT INTO productos (nombre, descripcion, precio_detal, precio_almayor, unidades_por_bandeja)
                 VALUES 
                 (%s, %s, %s, %s,%s)
                 """
        c.execute(sql, (nombre, descripcion, precio_detal, precio_almayor, unidades_por_bandeja))
        current_app.mysql.connection.commit()
        id = c.lastrowid
    return productos(id, nombre, descripcion, precio_detal, precio_almayor, unidades_por_bandeja, 1, None, None).toDic() 

def existe_nombre(nombre):
    with cursor_ctx() as c:
        sql = "SELECT id FROM productos WHERE nombre = %s"
        c.execute(sql, (nombre,))
        dato = c.fetchone()

    return dato is not None


def existe_producto(producto_id):
    with cursor_ctx() as c:
        sql = "SELECT id FROM productos WHERE id = %s AND activo = 1"
        c.execute(sql, (producto_id,))
        dato = c.fetchone()

    return dato is not None     

def eliminar(id):
    with cursor_ctx() as c:
        sql = "UPDATE productos SET activo = 0 WHERE id = %s AND activo = 1"
        c.execute(sql, (id,))

        current_app.mysql.connection.commit()
        filas_afectadas = c.rowcount

    return filas_afectadas > 0    

def actualizar(id, nombre, descripcion, precio_detal, precio_almayor, unidades_por_bandeja):
    with cursor_ctx() as c:
        sql = """
              UPDATE productos 
              SET nombre = %s, descripcion = %s, precio_detal =%s, precio_almayor=%s, unidades_por_bandeja = %s, updated_at = NOW() 
              WHERE id = %s
              """
        c.execute(sql, (nombre, descripcion, precio_detal, precio_almayor, unidades_por_bandeja, id))

        current_app.mysql.connection.commit()
        filas_afectadas = c.rowcount

    return filas_afectadas > 0

def obtener_producto(id):
    with cursor_ctx() as c:
        c.execute("""
            SELECT id, nombre, descripcion, precio_detal, precio_almayor, unidades_por_bandeja, activo
            FROM productos 
            WHERE id = %s AND activo = 1
        """, (id,))
        producto = c.fetchone()
    if producto:
        return {
            "id"                    : producto[0],
            "nombre"                : producto[1],
            "descripcion"           : producto[2],
            "precio_detal"          : producto[3],
            "precio_almayor"        :producto [4], 
            "unidades_por_bandeja"  : producto[5],
            "activo"                : producto[6]
        }
    return None

def existe_nombre_otro(nombre, id):
    with cursor_ctx() as c:
        sql = "SELECT id FROM productos WHERE nombre = %s AND id != %s"
        c.execute(sql, (nombre, id))
        dato = c.fetchone()

    return dato is not None

def productos_mas_vendidos(limite=5):
    with cursor_ctx() as c:
        c.execute("""
            SELECT
                p.id,
                p.nombre,
                p.precio_detal,
                COALESCE(SUM(vd.cantidad), 0) AS unidades_vendidas,
                COALESCE(SUM(vd.subtotal), 0) AS total_ingresos
            FROM productos p
            LEFT JOIN venta_detalle vd ON vd.producto_id = p.id
            LEFT JOIN ventas v ON v.id = vd.venta_id
                AND v.estado != 'anulada'
            WHERE p.activo = 1
            GROUP BY p.id, p.nombre, p.precio_detal
            ORDER BY total_ingresos DESC
            LIMIT %s
        """, (limite,))
        datos = c.fetchall()

    lista = []
    for p in datos:
        lista.append({
            "id"              : p[0],
            "nombre"          : p[1],
            "precio_detal"    : float(p[2]),
            "unidades_vendidas": int(p[3]),
            "total_ingresos"  : float(p[4])
        })
    return lista


def productos_sin_movimiento(dias=15, limite=5):
    """
    Productos activos con inventario que no registran ventas en los ultimos
    `dias` dias corridos (hoy incluido, hora Colombia).

    Un producto cuenta como movido si aparece como producto directo en
    venta_detalle (es_combo = 0), como componente de un combo de catalogo
    (combo_detalle) o como componente de un combo personalizado
    (combo_productos JSON). Se excluyen las ventas anuladas y se toma
    `fecha_entrega` (UTC en la BD, se muestra en hora Colombia).

    Si el producto nunca se vendio, los dias se cuentan desde `created_at`.
    Solo entran productos con stock total > 0:
        bandejas * unidades_por_bandeja + unidades_sueltas
    """
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    hoy = datetime.now(ZoneInfo("America/Bogota")).date()
    desde = hoy - timedelta(days=dias - 1)

    base_sql = """
        SELECT
            p.id,
            p.nombre,
            DATE(DATE_SUB(m.ultima_venta, INTERVAL 5 HOUR)) AS ultima_venta,
            DATEDIFF(%s, DATE(DATE_SUB(
                COALESCE(m.ultima_venta, p.created_at), INTERVAL 5 HOUR
            ))) AS dias_sin_venta,
            CASE WHEN m.ultima_venta IS NULL THEN 1 ELSE 0 END AS nunca_vendido,
            COALESCE(i.bandejas, 0) AS stock_bandejas,
            COALESCE(i.sueltas, 0) AS unidades_sueltas,
            (COALESCE(i.bandejas, 0) * p.unidades_por_bandeja
                + COALESCE(i.sueltas, 0)) AS stock_unidades
        FROM productos p
        LEFT JOIN (
            SELECT producto_id, MAX(fecha_entrega) AS ultima_venta
            FROM (
                SELECT vd.producto_id, v.fecha_entrega
                FROM venta_detalle vd
                JOIN ventas v ON v.id = vd.venta_id
                WHERE vd.es_combo = 0
                  AND vd.producto_id IS NOT NULL
                  AND v.estado IN ('pendiente', 'entregada')

                UNION ALL

                SELECT cd.producto_id, v.fecha_entrega
                FROM venta_detalle vd
                JOIN ventas v ON v.id = vd.venta_id
                JOIN combo_detalle cd ON cd.combo_id = vd.combo_id
                WHERE vd.es_combo = 1
                  AND vd.combo_id IS NOT NULL
                  AND v.estado IN ('pendiente', 'entregada')

                UNION ALL

                SELECT jt.producto_id, v.fecha_entrega
                FROM venta_detalle vd
                JOIN ventas v ON v.id = vd.venta_id
                JOIN JSON_TABLE(
                    IF(JSON_VALID(vd.combo_productos),
                       vd.combo_productos, JSON_ARRAY()),
                    '$[*]' COLUMNS (
                        producto_id INT PATH '$.producto_id'
                    )
                ) AS jt ON TRUE
                WHERE vd.es_combo = 1
                  AND vd.combo_id IS NULL
                  AND vd.combo_productos IS NOT NULL
                  AND v.estado IN ('pendiente', 'entregada')
            ) AS movimientos
            GROUP BY producto_id
        ) AS m ON m.producto_id = p.id
        LEFT JOIN (
            SELECT producto_id,
                   SUM(stock_actual) AS bandejas,
                   SUM(unidades_sueltas) AS sueltas
            FROM inventario
            GROUP BY producto_id
        ) AS i ON i.producto_id = p.id
    """

    filtro = """
        WHERE dias_sin_venta >= %s
          AND stock_unidades > 0
    """

    with cursor_ctx() as c:
        c.execute(
            f"SELECT COUNT(*) FROM ({base_sql}) AS q {filtro}",
            (hoy, dias)
        )
        total = c.fetchone()[0]

        c.execute(
            f"""
                SELECT * FROM ({base_sql}) AS q
                {filtro}
                ORDER BY dias_sin_venta DESC, nombre ASC
                LIMIT %s
            """,
            (hoy, dias, limite)
        )
        filas = c.fetchall()

    lista = []
    for f in filas:
        lista.append({
            "id"              : int(f[0]),
            "nombre"          : f[1],
            "dias_sin_venta"  : int(f[3]) if f[3] is not None else None,
            "ultima_venta"    : f[2].isoformat() if f[2] else None,
            "nunca_vendido"   : bool(f[4]),
            "stock_bandejas"  : int(f[5]),
            "unidades_sueltas": int(f[6]),
            "stock_unidades"  : int(f[7])
        })

    return {
        "dias"     : dias,
        "desde"    : desde.isoformat(),
        "hasta"    : hoy.isoformat(),
        "limite"   : limite,
        "total"    : int(total),
        "productos": lista
    }