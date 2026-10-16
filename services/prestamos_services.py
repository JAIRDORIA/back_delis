"""
Service: Prestamos a clientes, con abonos parciales (v2).

Sigue el mismo patron usado en abonos_service.py (el de ventas):
un prestamo tiene monto/total_abonado/saldo_pendiente, y cada abono queda
registrado como una fila independiente en `pagos_prestamos`, ademas de
reflejarse en `movimientos_caja`.
"""
from flask import current_app
from utils.db import cursor_ctx


def obtener_disponible_caja(corte_id, medio_pago):
    with cursor_ctx() as c:
        c.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN tipo = 'egreso'  THEN monto ELSE 0 END), 0)
            FROM movimientos_caja
            WHERE corte_id = %s AND medio_pago = %s
        """, (corte_id, medio_pago))
        disponible = float(c.fetchone()[0])
    return disponible


def obtener_saldo_cuenta(medio_pago_id):
    """Saldo disponible de una cuenta de transferencia según v_saldos_cuenta."""
    with cursor_ctx() as c:
        c.execute("""
            SELECT nombre, saldo
            FROM v_saldos_cuenta
            WHERE medio_pago_id = %s
        """, (medio_pago_id,))
        row = c.fetchone()
    if not row:
        return None, 0.0
    return row[0], float(row[1])


def obtener_corte_abierto():
    with cursor_ctx() as c:
        c.execute("SELECT id, numero FROM cortes WHERE estado = 'abierto' LIMIT 1")
        corte = c.fetchone()
    if not corte:
        return None
    return {"id": corte[0], "numero": corte[1]}


def obtener_prestamo(prestamo_id):
    with cursor_ctx() as c:
        c.execute("""
            SELECT p.id, p.cliente_id, cl.nombre AS cliente_nombre, p.corte_id,
                   p.usuario_id, p.monto, p.total_abonado, p.saldo_pendiente,
                   p.medio_pago, p.medio_pago_id, mp.nombre AS medio_pago_nombre,
                   p.estado, p.observacion, p.fecha, p.fecha_pago,
                   p.usuario_pago_id, p.medio_pago_pago, p.medio_pago_pago_id,
                   mpp.nombre AS medio_pago_pago_nombre
            FROM prestamos p
            JOIN clientes cl ON cl.id = p.cliente_id
            LEFT JOIN medios_pago mp ON mp.id = p.medio_pago_id
            LEFT JOIN medios_pago mpp ON mpp.id = p.medio_pago_pago_id
            WHERE p.id = %s
        """, (prestamo_id,))
        row = c.fetchone()
    if not row:
        return None
    return _row_a_dict(row)


def listar_prestamos(estado=None):
    query = """
        SELECT p.id, p.cliente_id, cl.nombre AS cliente_nombre, p.corte_id,
               p.usuario_id, p.monto, p.total_abonado, p.saldo_pendiente,
               p.medio_pago, p.medio_pago_id, mp.nombre AS medio_pago_nombre,
               p.estado, p.observacion, p.fecha, p.fecha_pago,
               p.usuario_pago_id, p.medio_pago_pago, p.medio_pago_pago_id,
               mpp.nombre AS medio_pago_pago_nombre
        FROM prestamos p
        JOIN clientes cl ON cl.id = p.cliente_id
        LEFT JOIN medios_pago mp ON mp.id = p.medio_pago_id
        LEFT JOIN medios_pago mpp ON mpp.id = p.medio_pago_pago_id
    """
    params = ()
    if estado:
        query += " WHERE p.estado = %s"
        params = (estado,)
    query += " ORDER BY p.fecha DESC"

    with cursor_ctx() as c:
        c.execute(query, params)
        rows = c.fetchall()
    return [_row_a_dict(r) for r in rows]


def listar_pagos_prestamo(prestamo_id):
    """Historial de abonos hechos a un prestamo especifico."""
    with cursor_ctx() as c:
        c.execute("""
            SELECT pp.id, pp.prestamo_id, pp.corte_id, pp.usuario_id, pp.monto,
                   pp.medio_pago, pp.medio_pago_id, mp.nombre AS medio_pago_nombre,
                   pp.observacion, pp.fecha
            FROM pagos_prestamos pp
            LEFT JOIN medios_pago mp ON mp.id = pp.medio_pago_id
            WHERE pp.prestamo_id = %s
            ORDER BY pp.fecha DESC
        """, (prestamo_id,))
        rows = c.fetchall()
    return [{
        "id": r[0], "prestamo_id": r[1], "corte_id": r[2], "usuario_id": r[3],
        "monto": float(r[4]), "medio_pago": r[5],
        "medio_pago_id": r[6], "medio_pago_nombre": r[7],
        "observacion": r[8],
        "fecha": str(r[9]) if r[9] else None,
    } for r in rows]


def registrar(cliente_id, corte_id, usuario_id, monto, medio_pago, medio_pago_id, observacion):
    with cursor_ctx() as c:
        c.execute("""
            INSERT INTO prestamos (cliente_id, corte_id, usuario_id, monto,
                                    total_abonado, saldo_pendiente, medio_pago,
                                    medio_pago_id, observacion)
            VALUES (%s, %s, %s, %s, 0, %s, %s, %s, %s)
        """, (cliente_id, corte_id, usuario_id, monto, monto, medio_pago,
              medio_pago_id, observacion))
        prestamo_id = c.lastrowid

        c.execute("""
            INSERT INTO movimientos_caja (corte_id, usuario_id, tipo, concepto,
                                           referencia_id, monto, descripcion, medio_pago,
                                           medio_pago_id)
            VALUES (%s, %s, 'egreso', 'prestamo', %s, %s, %s, %s, %s)
        """, (
            corte_id, usuario_id, prestamo_id, monto,
            f"Prestamo a cliente ID: {cliente_id}", medio_pago, medio_pago_id
        ))

        current_app.mysql.connection.commit()

    return obtener_prestamo(prestamo_id)


def abonar_prestamo(prestamo_id, usuario_id, monto, medio_pago, medio_pago_id, observacion):
    """
    Registra un abono (parcial o que completa el pago) a un prestamo.
    El abono se asocia al corte que este abierto EN ESE MOMENTO (no al
    corte original del prestamo), igual que con los abonos de ventas.
    """
    prestamo = obtener_prestamo(prestamo_id)
    corte_abierto = obtener_corte_abierto()
    corte_id = corte_abierto["id"]

    with cursor_ctx() as c:
        # 1. historial del abono
        c.execute("""
            INSERT INTO pagos_prestamos (prestamo_id, corte_id, usuario_id, monto,
                                          medio_pago, medio_pago_id, observacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (prestamo_id, corte_id, usuario_id, monto, medio_pago, medio_pago_id, observacion))

        # 2. ingreso de caja (alimenta las KPI de efectivo/transferencia)
        c.execute("""
            INSERT INTO movimientos_caja (corte_id, usuario_id, tipo, concepto,
                                           referencia_id, monto, descripcion, medio_pago,
                                           medio_pago_id)
            VALUES (%s, %s, 'ingreso', 'pago_prestamo', %s, %s, %s, %s, %s)
        """, (
            corte_id, usuario_id, prestamo_id, monto,
            f"Abono a prestamo cliente ID: {prestamo['cliente_id']}", medio_pago,
            medio_pago_id
        ))

        # 3. actualizar saldo del prestamo
        nuevo_abonado = prestamo["total_abonado"] + monto
        nuevo_saldo = prestamo["saldo_pendiente"] - monto
        queda_pagado = nuevo_saldo <= 0

        if queda_pagado:
            c.execute("""
                UPDATE prestamos
                SET total_abonado = %s, saldo_pendiente = 0, estado = 'pagado',
                    fecha_pago = NOW(), usuario_pago_id = %s,
                    medio_pago_pago = %s, medio_pago_pago_id = %s
                WHERE id = %s
            """, (nuevo_abonado, usuario_id, medio_pago, medio_pago_id, prestamo_id))
        else:
            c.execute("""
                UPDATE prestamos
                SET total_abonado = %s, saldo_pendiente = %s
                WHERE id = %s
            """, (nuevo_abonado, nuevo_saldo, prestamo_id))

        current_app.mysql.connection.commit()

    return obtener_prestamo(prestamo_id)


def _row_a_dict(row):
    return {
        "id"              : row[0],
        "cliente_id"      : row[1],
        "cliente_nombre"  : row[2],
        "corte_id"        : row[3],
        "usuario_id"      : row[4],
        "monto"           : float(row[5]),
        "total_abonado"   : float(row[6]),
        "saldo_pendiente" : float(row[7]),
        "medio_pago"      : row[8],
        "medio_pago_id"   : row[9],
        "medio_pago_nombre": row[10],
        "estado"          : row[11],
        "observacion"     : row[12],
        "fecha"           : str(row[13]) if row[13] else None,
        "fecha_pago"      : str(row[14]) if row[14] else None,
        "usuario_pago_id" : row[15],
        "medio_pago_pago" : row[16],
        "medio_pago_pago_id": row[17],
        "medio_pago_pago_nombre": row[18],
    }