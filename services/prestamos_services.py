"""
Service: Prestamos a clientes.

Sigue el mismo patron usado en abonos_service.py:
cursor -> execute -> commit -> close -> devolver el registro recien creado/actualizado.

Regla de negocio clave:
El dinero disponible en caja por medio de pago se calcula directamente desde
`movimientos_caja` (ingresos - egresos), que es la fuente de verdad de TODO
movimiento de dinero del sistema: ventas/abonos, compras, ajustes, y ahora
tambien prestamos y pagos de prestamos. Esto evita tener que tocar el
balance_service existente y mantiene todo consistente automaticamente.
"""
from flask import current_app


def obtener_disponible_caja(corte_id, medio_pago):
    """
    Dinero disponible en caja para un medio de pago especifico,
    dentro del corte dado.
    """
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN tipo = 'egreso'  THEN monto ELSE 0 END), 0)
        FROM movimientos_caja
        WHERE corte_id = %s AND medio_pago = %s
    """, (corte_id, medio_pago))
    disponible = float(c.fetchone()[0])
    c.close()
    return disponible
 
 
def obtener_corte_abierto():
    """
    Devuelve el corte con estado='abierto', o None si no existe.
    Se usa para asociar automaticamente el prestamo (y su pago) al corte actual,
    sin depender de que el frontend envie el corte_id.
    """
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT id, numero FROM cortes WHERE estado = 'abierto' LIMIT 1
    """)
    corte = c.fetchone()
    c.close()
    if not corte:
        return None
    return {"id": corte[0], "numero": corte[1]}
 
 
def obtener_prestamo(prestamo_id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT p.id, p.cliente_id, cl.nombre AS cliente_nombre, p.corte_id,
               p.usuario_id, p.monto, p.medio_pago, p.estado, p.observacion,
               p.fecha, p.fecha_pago, p.usuario_pago_id, p.medio_pago_pago
        FROM prestamos p
        JOIN clientes cl ON cl.id = p.cliente_id
        WHERE p.id = %s
    """, (prestamo_id,))
    row = c.fetchone()
    c.close()
    if not row:
        return None
    return _row_a_dict(row)
 
 
def listar_prestamos(estado=None):
    c = current_app.mysql.connection.cursor()
    query = """
        SELECT p.id, p.cliente_id, cl.nombre AS cliente_nombre, p.corte_id,
               p.usuario_id, p.monto, p.medio_pago, p.estado, p.observacion,
               p.fecha, p.fecha_pago, p.usuario_pago_id, p.medio_pago_pago
        FROM prestamos p
        JOIN clientes cl ON cl.id = p.cliente_id
    """
    params = ()
    if estado:
        query += " WHERE p.estado = %s"
        params = (estado,)
    query += " ORDER BY p.fecha DESC"
 
    c.execute(query, params)
    rows = c.fetchall()
    c.close()
    return [_row_a_dict(r) for r in rows]
 
 
def registrar(cliente_id, corte_id, usuario_id, monto, medio_pago, observacion):
    c = current_app.mysql.connection.cursor()
 
    c.execute("""
        INSERT INTO prestamos (cliente_id, corte_id, usuario_id, monto,
                                medio_pago, observacion)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (cliente_id, corte_id, usuario_id, monto, medio_pago, observacion))
    prestamo_id = c.lastrowid
 
    # egreso de caja: el dinero prestado sale de caja
    c.execute("""
        INSERT INTO movimientos_caja (corte_id, usuario_id, tipo, concepto,
                                       referencia_id, monto, descripcion, medio_pago)
        VALUES (%s, %s, 'egreso', 'prestamo', %s, %s, %s, %s)
    """, (
        corte_id, usuario_id, prestamo_id, monto,
        f"Prestamo a cliente ID: {cliente_id}", medio_pago
    ))
 
    current_app.mysql.connection.commit()
    c.close()
    return obtener_prestamo(prestamo_id)
 
 
def pagar(prestamo_id, usuario_id, medio_pago):
    """
    Marca el prestamo como pagado y devuelve el dinero a caja.
 
    `medio_pago` es el medio por el que EL CLIENTE PAGA (puede ser distinto
    al medio_pago con el que se le presto originalmente -- ej: se presto en
    efectivo pero paga por transferencia). Se guarda por separado en
    `medio_pago_pago` para no perder el dato original del prestamo, y es el
    que se usa en el movimiento de caja, ya que es el que determina en cual
    KPI (efectivo/transferencia) debe reflejarse el ingreso.
 
    El pago se asocia al corte que este abierto EN ESE MOMENTO (no al corte
    original del prestamo), igual que ocurre con los abonos de ventas: el
    dinero vuelve "hoy", no en el corte en que se origino la deuda.
    """
    prestamo = obtener_prestamo(prestamo_id)
 
    corte_abierto = obtener_corte_abierto()
    corte_id = corte_abierto["id"]
 
    c = current_app.mysql.connection.cursor()
 
    c.execute("""
        UPDATE prestamos
        SET estado = 'pagado', fecha_pago = NOW(),
            usuario_pago_id = %s, medio_pago_pago = %s
        WHERE id = %s
    """, (usuario_id, medio_pago, prestamo_id))
 
    # ingreso de caja: el dinero vuelve a caja, con el medio de pago real del pago
    c.execute("""
        INSERT INTO movimientos_caja (corte_id, usuario_id, tipo, concepto,
                                       referencia_id, monto, descripcion, medio_pago)
        VALUES (%s, %s, 'ingreso', 'pago_prestamo', %s, %s, %s, %s)
    """, (
        corte_id, usuario_id, prestamo_id, prestamo["monto"],
        f"Pago de prestamo cliente ID: {prestamo['cliente_id']}", medio_pago
    ))
 
    current_app.mysql.connection.commit()
    c.close()
    return obtener_prestamo(prestamo_id)
 
 
def _row_a_dict(row):
    return {
        "id"              : row[0],
        "cliente_id"      : row[1],
        "cliente_nombre"  : row[2],
        "corte_id"        : row[3],
        "usuario_id"      : row[4],
        "monto"           : float(row[5]),
        "medio_pago"      : row[6],
        "estado"          : row[7],
        "observacion"     : row[8],
        "fecha"           : str(row[9]) if row[9] else None,
        "fecha_pago"      : str(row[10]) if row[10] else None,
        "usuario_pago_id" : row[11],
        "medio_pago_pago" : row[12],
    }