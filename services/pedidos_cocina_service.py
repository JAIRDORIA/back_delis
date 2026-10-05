"""
Service: pedidos del dia para el panel de cocina.

Devuelve, en UNA sola respuesta, los pedidos pendientes de una fecha con su
detalle completo (productos y combos, incluidos los personalizados), para que
cada tarjeta no tenga que pedir su detalle aparte.

Por diseño NO devuelve ningun dato de dinero (precios, totales, abonos,
saldos): cocina solo necesita saber QUE preparar y PARA CUANDO.

IMPORTANTE: cocina NO entrega en el sentido contable. Marcar un pedido como
entregado en cocina solo deja una marca (ventas.entregada_cocina_at) para avisar
al admin. La venta sigue 'pendiente' y NO se toca el inventario: el descuento
ocurre cuando el admin la marca 'entregada' desde el modulo de ventas.
"""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import current_app

BOGOTA = ZoneInfo("America/Bogota")
UTC = ZoneInfo("UTC")
FMT = "%Y-%m-%d %H:%M:%S"


def _rango_utc_del_dia(fecha_str):
    """
    ventas.fecha_entrega se guarda en UTC. Un dia colombiano (00:00 a 24:00
    hora Bogota) equivale a 05:00 UTC del dia -> 05:00 UTC del dia siguiente.
    """
    dia = datetime.strptime(fecha_str, "%Y-%m-%d").replace(tzinfo=BOGOTA)
    inicio = dia.astimezone(UTC)
    fin = (dia + timedelta(days=1)).astimezone(UTC)
    return inicio.strftime(FMT), fin.strftime(FMT)


def _a_bogota(valor):
    """datetime 'naive' en UTC (asi lo devuelve MySQL) -> datetime en Bogota."""
    if valor is None:
        return None
    return valor.replace(tzinfo=UTC).astimezone(BOGOTA)


def _parsear_json(valor):
    if valor is None:
        return None
    if isinstance(valor, (list, dict)):
        return valor
    if isinstance(valor, (bytes, bytearray)):
        valor = valor.decode()
    try:
        return json.loads(valor)
    except (ValueError, TypeError):
        return None


def _placeholders(n):
    return ",".join(["%s"] * n)


def _cargar_items(c, venta_ids):
    """Devuelve {venta_id: [items]} para todas las ventas pedidas, con 3 queries en total."""
    c.execute(f"""
        SELECT id, venta_id, nombre_producto, cantidad, es_combo, combo_id, combo_productos
        FROM venta_detalle
        WHERE venta_id IN ({_placeholders(len(venta_ids))})
        ORDER BY id ASC
    """, tuple(venta_ids))
    lineas = c.fetchall()

    # Combos de catalogo (combo_id informado, sin composicion propia)
    combo_ids = {l[5] for l in lineas if l[4] and l[5] and l[6] is None}
    catalogo = {}
    if combo_ids:
        c.execute(f"""
            SELECT cd.combo_id, cd.producto_id, p.nombre, cd.cantidad_unidades
            FROM combo_detalle cd
            JOIN productos p ON p.id = cd.producto_id
            WHERE cd.combo_id IN ({_placeholders(len(combo_ids))})
            ORDER BY cd.id ASC
        """, tuple(combo_ids))
        for combo_id, producto_id, nombre, unidades in c.fetchall():
            catalogo.setdefault(combo_id, []).append(
                {"producto_id": producto_id, "nombre": nombre, "unidades": int(unidades)}
            )

    # Combos personalizados: el JSON solo trae producto_id, hay que resolver nombres
    personalizados = {}
    ids_productos = set()
    for l in lineas:
        if l[4] and l[6] is not None:
            lista = _parsear_json(l[6]) or []
            personalizados[l[0]] = lista
            ids_productos.update(p.get("producto_id") for p in lista if p.get("producto_id"))

    nombres = {}
    if ids_productos:
        c.execute(
            f"SELECT id, nombre FROM productos WHERE id IN ({_placeholders(len(ids_productos))})",
            tuple(ids_productos),
        )
        nombres = {r[0]: r[1] for r in c.fetchall()}

    items_por_venta = {}
    for linea_id, venta_id, nombre, cantidad, es_combo, combo_id, combo_productos in lineas:
        item = {
            "id": linea_id,
            "tipo": "combo" if es_combo else "producto",
            "nombre": nombre,
            "cantidad": int(cantidad),
        }

        if es_combo:
            if linea_id in personalizados:
                item["personalizado"] = True
                componentes = [
                    {
                        "producto_id": p.get("producto_id"),
                        "nombre": nombres.get(p.get("producto_id"), "Producto"),
                        "unidades": int(p.get("cantidad_unidades", 0)),
                    }
                    for p in personalizados[linea_id]
                ]
            else:
                item["personalizado"] = False
                componentes = [dict(x) for x in catalogo.get(combo_id, [])]

            # unidades por 1 combo y total a preparar (x cantidad de combos)
            for comp in componentes:
                comp["unidades_total"] = comp["unidades"] * int(cantidad)
            item["componentes"] = componentes

        items_por_venta.setdefault(venta_id, []).append(item)

    return items_por_venta

def pedidos_del_dia(fecha_str=None):
    """
    fecha_str: 'YYYY-MM-DD' en hora Colombia. Si viene vacia, se usa hoy (Colombia).
    """
    if not fecha_str:
        fecha_str = datetime.now(BOGOTA).strftime("%Y-%m-%d")

    inicio, fin = _rango_utc_del_dia(fecha_str)

    c = current_app.mysql.connection.cursor()
    try:
        # LEFT JOIN: ventas de clientes ocasionales (sin cliente_id) no deben desaparecer del panel.
        # Las columnas nuevas van al final para no mover los indices f[4] / f[5] de abajo.
        # direccion: la del pedido (ventas.direccion_entrega) manda; si es NULL o vacia,
        # cae a la direccion registrada del cliente (clientes.direccion). No se modifica al cliente.
        c.execute("""
            SELECT v.id, v.nombre_cliente, v.fecha_entrega, v.observacion, v.estado,
                   v.entregada_cocina_at,
                   v.saldo_pendiente,
                   c.identificacion,
                   COALESCE(NULLIF(TRIM(v.direccion_entrega), ''), c.direccion) AS direccion
            FROM ventas v
            LEFT JOIN clientes c ON c.id = v.cliente_id
            WHERE v.estado IN ('pendiente', 'entregada')
              AND COALESCE(v.eliminada, 0) = 0
              AND v.fecha_entrega >= %s AND v.fecha_entrega < %s
            ORDER BY v.fecha_entrega ASC, v.id ASC
        """, (inicio, fin))
        filas = c.fetchall()

        pendientes = [f for f in filas if f[4] == "pendiente" and f[5] is None]
        total_entregados = len(filas) - len(pendientes)

        items = _cargar_items(c, [f[0] for f in pendientes]) if pendientes else {}
    finally:
        c.close()

    pedidos = []
    for (venta_id, nombre_cliente, fecha_entrega, observacion, estado,
         _marca, saldo_pendiente, celular, direccion) in pendientes:
        local = _a_bogota(fecha_entrega)
        pedidos.append({
            "id": venta_id,
            "nombre_cliente": nombre_cliente,
            "celular": str(celular).strip() if celular else None,
            "direccion": direccion.strip() if direccion else None,
            "saldo_pendiente": float(saldo_pendiente or 0),
            "fecha_entrega": str(fecha_entrega),
            "fecha_entrega_local": local.strftime("%Y-%m-%d") if local else None,
            "hora_entrega": local.strftime("%H:%M") if local else None,
            "observacion": observacion,
            "estado": estado,
            "items": items.get(venta_id, []),
        })

    return {
        "fecha": fecha_str,
        "total_pendientes": len(pedidos),
        "total_entregados": total_entregados,
        "pedidos": pedidos,
    }


def estado_para_cocina(venta_id):
    """(estado, entregada_cocina_at) de la venta, o None si no existe / esta eliminada."""
    c = current_app.mysql.connection.cursor()
    try:
        c.execute("""
            SELECT estado, entregada_cocina_at
            FROM ventas
            WHERE id = %s AND COALESCE(eliminada, 0) = 0
        """, (venta_id,))
        return c.fetchone()
    finally:
        c.close()


def marcar_entregado_cocina(venta_id, usuario_id):
    """
    Deja la marca de entrega en cocina. NO cambia el estado ni toca el inventario.

    El UPDATE es condicional (pendiente y sin marca previa), asi un doble toque
    o dos tablets a la vez no pueden marcarlo dos veces. Devuelve True si esta
    llamada fue la que lo marco.
    """
    con = current_app.mysql.connection
    c = con.cursor()
    try:
        c.execute("""
            UPDATE ventas
            SET entregada_cocina_at = NOW(), entregada_cocina_por = %s
            WHERE id = %s
              AND estado = 'pendiente'
              AND entregada_cocina_at IS NULL
              AND COALESCE(eliminada, 0) = 0
        """, (usuario_id, venta_id))
        marcado = c.rowcount > 0
        con.commit()
        return marcado
    finally:
        c.close()


def entregadas_en_cocina_por_confirmar():
    """
    Ventas que cocina ya entrego pero que el admin aun no marca 'entregada'
    (alimenta el aviso "la venta X fue entregada en cocina" del modulo de ventas).
    Desaparecen solas cuando el admin la marca entregada o la anula.
    """
    c = current_app.mysql.connection.cursor()
    try:
        c.execute("""
            SELECT id, nombre_cliente, entregada_cocina_at
            FROM ventas
            WHERE estado = 'pendiente'
              AND entregada_cocina_at IS NOT NULL
              AND COALESCE(eliminada, 0) = 0
            ORDER BY entregada_cocina_at DESC
        """)
        filas = c.fetchall()
    finally:
        c.close()

    resultado = []
    for venta_id, nombre_cliente, marca in filas:
        local = _a_bogota(marca)
        resultado.append({
            "id": venta_id,
            "nombre_cliente": nombre_cliente,
            "entregada_cocina_at": str(marca),                        # UTC, como el resto de la API
            "hora_local": local.strftime("%H:%M") if local else None,  # ya en hora Colombia
        })
    return resultado