from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app

from models.produccion_empleado_model import produccion_empleado
from utils.db import cursor_ctx

BOGOTA = ZoneInfo("America/Bogota")
LIMITE_PENDIENTES = 200


# ─────────────────────────────────────────────
#  PRODUCTOS PARA EL SELECTOR
# ─────────────────────────────────────────────

def listado_productos_activos():
    """
    Productos activos (borrado logico: activo = 1) para el selector del panel
    de produccion. Es lo unico de productos que puede leer el rol 'produccion'.
    """
    with cursor_ctx() as c:
        c.execute(
            "SELECT id, nombre, unidades_por_bandeja FROM productos "
            "WHERE activo = 1 ORDER BY nombre"
        )
        filas = c.fetchall()

    return [
        {
            "id":                   f[0],
            "nombre":               f[1],
            "unidades_por_bandeja": f[2],
        }
        for f in filas
    ]


# ─────────────────────────────────────────────
#  REGISTRO (queda PENDIENTE, no toca inventario)
# ─────────────────────────────────────────────

def registrar_produccion_empleado(empleado_id, producto_id, bandejas, unidades_sueltas, usuario_id):
    """
    Valida empleado/producto activos y guarda el registro como 'pendiente' en
    `producciones_empleado`. NO inserta en `producciones` ni toca inventario.

    Normaliza bandejas/unidades_sueltas con la misma formula del sistema:
        bandejas += unidades_sueltas // upb
        unidades_sueltas %= upb
    Si el producto no tiene unidades_por_bandeja (> 0) no se convierte nada.

    Devuelve (dato, error, status_http).
    """
    with cursor_ctx() as c:
        c.execute("SELECT id, nombre FROM empleados WHERE id = %s AND activo = 1", (empleado_id,))
        empleado = c.fetchone()
        if not empleado:
            return None, "El empleado no existe o está inactivo", 404

        c.execute(
            "SELECT id, nombre, unidades_por_bandeja FROM productos WHERE id = %s AND activo = 1",
            (producto_id,)
        )
        producto = c.fetchone()
        if not producto:
            return None, "El producto no existe o está inactivo", 404

        unidades_por_bandeja = producto[2]
        convertido = False
        if unidades_por_bandeja and unidades_por_bandeja > 0:
            bandejas_norm = bandejas + unidades_sueltas // unidades_por_bandeja
            sueltas_norm = unidades_sueltas % unidades_por_bandeja
            convertido = bandejas_norm != bandejas or sueltas_norm != unidades_sueltas
        else:
            bandejas_norm = bandejas
            sueltas_norm = unidades_sueltas

        c.execute(
            """
            INSERT INTO producciones_empleado
                (empleado_id, producto_id, bandejas, unidades_sueltas, estado,
                 registrado_por, created_at)
            VALUES (%s, %s, %s, %s, 'pendiente', %s, UTC_TIMESTAMP())
            """,
            (empleado_id, producto_id, bandejas_norm, sueltas_norm, usuario_id)
        )
        current_app.mysql.connection.commit()
        nuevo_id = c.lastrowid

        c.execute("SELECT created_at FROM producciones_empleado WHERE id = %s", (nuevo_id,))
        fila = c.fetchone()

    created_at = fila[0] if fila else None

    return produccion_empleado(
        id               = nuevo_id,
        empleado_id      = empleado_id,
        empleado_nombre  = empleado[1],
        producto_id      = producto_id,
        producto_nombre  = producto[1],
        bandejas         = bandejas_norm,
        unidades_sueltas = sueltas_norm,
        convertido       = convertido,
        created_at       = created_at,
    ).toDic(), None, None


# ─────────────────────────────────────────────
#  PANEL ADMIN: PENDIENTES Y VALIDACIÓN
# ─────────────────────────────────────────────

def _item_pendiente(f):
    """f = (id, empleado_id, empleado_nombre, producto_id, producto_nombre,
            unidades_por_bandeja, bandejas, unidades_sueltas, created_at)"""
    return {
        "id":                   f[0],
        "empleado_id":          f[1],
        "empleado_nombre":      f[2],
        "producto_id":          f[3],
        "producto_nombre":      f[4],
        "unidades_por_bandeja": f[5],
        "bandejas":             f[6],
        "unidades_sueltas":     f[7],
        "created_at":           str(f[8]) if f[8] is not None else None,
    }


def _item_revision(f):
    """Igual que _item_pendiente + los campos que llena la validación del admin."""
    item = _item_pendiente(f[0:9])
    item["estado"]                 = f[9]
    item["bandejas_final"]         = f[10]
    item["unidades_sueltas_final"] = f[11]
    item["produccion_id"]          = f[12]
    item["motivo_rechazo"]         = f[13]
    return item


_SQL_DETALLE = """
    SELECT pe.id, pe.empleado_id, e.nombre, pe.producto_id, p.nombre,
           p.unidades_por_bandeja, pe.bandejas, pe.unidades_sueltas, pe.created_at,
           pe.estado, pe.bandejas_final, pe.unidades_sueltas_final,
           pe.produccion_id, pe.motivo_rechazo
    FROM producciones_empleado pe
    JOIN empleados e ON e.id = pe.empleado_id
    JOIN productos p ON p.id = pe.producto_id
    WHERE pe.id = %s
"""


def _normalizar(bandejas, unidades_sueltas, unidades_por_bandeja):
    """Misma fórmula del resto del sistema (ver registrar_produccion_empleado)."""
    if unidades_por_bandeja and unidades_por_bandeja > 0:
        return (
            bandejas + unidades_sueltas // unidades_por_bandeja,
            unidades_sueltas % unidades_por_bandeja,
        )
    return bandejas, unidades_sueltas


def _hoy_colombia():
    """`producciones.fecha` es un DATE: el día que es 'hoy' en Colombia."""
    return datetime.now(BOGOTA).date()


def listado_pendientes():
    """
    Registros en estado 'pendiente' para el aviso del panel admin, del más
    antiguo al más reciente. Límite fijo, sin paginación.
    """
    with cursor_ctx() as c:
        c.execute("""
            SELECT pe.id, pe.empleado_id, e.nombre, pe.producto_id, p.nombre,
                   p.unidades_por_bandeja, pe.bandejas, pe.unidades_sueltas, pe.created_at
            FROM producciones_empleado pe
            JOIN empleados e ON e.id = pe.empleado_id
            JOIN productos p ON p.id = pe.producto_id
            WHERE pe.estado = 'pendiente'
            ORDER BY pe.created_at ASC, pe.id ASC
            LIMIT %s
        """, (LIMITE_PENDIENTES,))
        filas = c.fetchall()

    items = [_item_pendiente(f) for f in filas]
    return {"total": len(items), "items": items}


def aceptar_produccion_empleado(id, bandejas, unidades_sueltas, usuario_id):
    """
    Acepta un registro pendiente: inserta en `producciones` (el trigger
    trg_produccion_insert suma al inventario) y marca la fila como 'aceptada'.

    `bandejas`/`unidades_sueltas` son las cantidades finales; si vienen en None
    se usan las que registró el empleado. Todo en UNA transacción con
    SELECT ... FOR UPDATE; un solo commit al final.

    NO llama a producciones_services.registro porque ese service hace commit
    propio y rompería la transacción.

    Devuelve (dato, error, status_http).
    """
    try:
        with cursor_ctx() as c:
            c.execute("""
                SELECT id, empleado_id, producto_id, bandejas, unidades_sueltas, estado
                FROM producciones_empleado
                WHERE id = %s
                FOR UPDATE
            """, (id,))
            fila = c.fetchone()
            if not fila:
                current_app.mysql.connection.rollback()
                return None, f"El registro #{id} no existe", 404
            if fila[5] != "pendiente":
                current_app.mysql.connection.rollback()
                return None, f"El registro #{id} ya fue {fila[5]}", 409

            empleado_id, producto_id = fila[1], fila[2]
            if bandejas is None and unidades_sueltas is None:
                bandejas, unidades_sueltas = fila[3], fila[4]

            c.execute("SELECT nombre FROM empleados WHERE id = %s", (empleado_id,))
            empleado = c.fetchone()
            c.execute(
                "SELECT nombre, unidades_por_bandeja FROM productos WHERE id = %s",
                (producto_id,)
            )
            producto = c.fetchone()

            unidades_por_bandeja = producto[1] if producto else None
            bandejas_final, unidades_sueltas_final = _normalizar(
                bandejas, unidades_sueltas, unidades_por_bandeja
            )

            observacion = f"Producción de {empleado[0]} (registro #{id})"
            c.execute("""
                INSERT INTO producciones
                    (producto_id, cantidad, unidades_sueltas, usuario_id, fecha, observacion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                producto_id, bandejas_final, unidades_sueltas_final,
                usuario_id, _hoy_colombia(), observacion,
            ))
            produccion_id = c.lastrowid

            c.execute("""
                UPDATE producciones_empleado
                SET estado = 'aceptada',
                    revisado_por = %s,
                    revisado_at = UTC_TIMESTAMP(),
                    bandejas_final = %s,
                    unidades_sueltas_final = %s,
                    produccion_id = %s
                WHERE id = %s
            """, (usuario_id, bandejas_final, unidades_sueltas_final, produccion_id, id))

            c.execute(_SQL_DETALLE, (id,))
            detalle = c.fetchone()

            current_app.mysql.connection.commit()

        return _item_revision(detalle), None, None
    except Exception:
        current_app.mysql.connection.rollback()
        raise


def rechazar_produccion_empleado(id, motivo, usuario_id):
    """
    Rechaza un registro pendiente. NO inserta en `producciones` ni toca
    inventario. Devuelve (dato, error, status_http).
    """
    try:
        with cursor_ctx() as c:
            c.execute("""
                SELECT id, estado
                FROM producciones_empleado
                WHERE id = %s
                FOR UPDATE
            """, (id,))
            fila = c.fetchone()
            if not fila:
                current_app.mysql.connection.rollback()
                return None, f"El registro #{id} no existe", 404
            if fila[1] != "pendiente":
                current_app.mysql.connection.rollback()
                return None, f"El registro #{id} ya fue {fila[1]}", 409

            c.execute("""
                UPDATE producciones_empleado
                SET estado = 'rechazada',
                    revisado_por = %s,
                    revisado_at = UTC_TIMESTAMP(),
                    motivo_rechazo = %s
                WHERE id = %s
            """, (usuario_id, motivo, id))

            c.execute(_SQL_DETALLE, (id,))
            detalle = c.fetchone()

            current_app.mysql.connection.commit()

        return _item_revision(detalle), None, None
    except Exception:
        current_app.mysql.connection.rollback()
        raise


# ─────────────────────────────────────────────
#  REGISTROS: últimos 5 de cada empleado activo
# ─────────────────────────────────────────────

def listado_registros():
    """
    Últimos 5 registros (de cualquier estado) de cada empleado activo, en una
    sola consulta. Usa ROW_NUMBER() (MySQL 8+), ordenados del más reciente al
    más antiguo.
    """
    with cursor_ctx() as c:
        c.execute("""
            SELECT pe.id, pe.empleado_id, e.nombre, p.nombre,
                   pe.bandejas, pe.unidades_sueltas, pe.estado,
                   pe.bandejas_final, pe.unidades_sueltas_final, pe.created_at
            FROM (
                SELECT id, empleado_id, producto_id, bandejas, unidades_sueltas,
                       estado, bandejas_final, unidades_sueltas_final, created_at,
                       ROW_NUMBER() OVER (
                           PARTITION BY empleado_id
                           ORDER BY created_at DESC, id DESC
                       ) AS rn
                FROM producciones_empleado
            ) pe
            JOIN empleados e ON e.id = pe.empleado_id
            JOIN productos p ON p.id = pe.producto_id
            WHERE pe.rn <= 5 AND e.activo = 1
            ORDER BY pe.created_at DESC, pe.id DESC
        """)
        filas = c.fetchall()

    items = [
        {
            "id":                     f[0],
            "empleado_id":            f[1],
            "empleado_nombre":        f[2],
            "producto_nombre":        f[3],
            "bandejas":               f[4],
            "unidades_sueltas":       f[5],
            "estado":                 f[6],
            "bandejas_final":         f[7],
            "unidades_sueltas_final": f[8],
            "created_at":             str(f[9]) if f[9] is not None else None,
        }
        for f in filas
    ]
    return {"total": len(items), "items": items}


