from flask import current_app
from models.compra_model import compra
from services.cortes_services import obtener_corte_abierto, obtener_corte
from services.medios_pago_services import resolver_medio_pago
from utils.db import cursor_ctx


# Categorias validas de una compra. 'insumo' = gasto normal; 'domicilio' =
# pago al domiciliario, obligatoriamente ligado a una venta (venta_id).
CATEGORIAS_COMPRA = ("insumo", "domicilio")


class CompraInvalida(Exception):
    """Error de validacion de categoria/venta_id.

    El controller lo traduce a 400 con {"mensaje": ...}. Se usa una excepcion
    para no cambiar el contrato de retorno (dato, error) del resto del modulo.
    """

    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


def _validar_categoria_venta(cursor, categoria, venta_id):
    """Valida categoria/venta_id y devuelve el venta_id normalizado.

    Reglas: 'insumo' no lleva venta; 'domicilio' exige una venta existente,
    no anulada y con valor_domicilio > 0. Una venta puede tener varias
    compras de domicilio y la suma puede superar valor_domicilio (el costo
    real del domicilio puede ser mayor que lo cobrado al cliente).
    """
    if categoria not in CATEGORIAS_COMPRA:
        raise CompraInvalida(
            f"categoria invalida: {categoria}. Valores permitidos: insumo, domicilio"
        )

    if categoria == "insumo":
        if venta_id not in (None, ""):
            raise CompraInvalida("si la categoria es 'insumo', venta_id debe venir vacio")
        return None

    if venta_id in (None, ""):
        raise CompraInvalida("venta_id es obligatorio cuando la categoria es 'domicilio'")

    try:
        venta_id = int(venta_id)
    except (TypeError, ValueError):
        raise CompraInvalida("venta_id debe ser un numero entero")

    cursor.execute(
        "SELECT estado, valor_domicilio FROM ventas WHERE id = %s",
        (venta_id,),
    )
    venta = cursor.fetchone()
    if not venta:
        raise CompraInvalida(f"la venta con id {venta_id} no existe")
    if venta[0] == "anulada":
        raise CompraInvalida(f"la venta {venta_id} esta anulada y no admite compras de domicilio")
    if float(venta[1] or 0) <= 0:
        raise CompraInvalida(f"la venta {venta_id} no tiene valor_domicilio (debe ser mayor a 0)")

    return venta_id


def _existe(cursor, tabla, id):
    cursor.execute(f"SELECT id FROM {tabla} WHERE id = %s", (id,))
    return cursor.fetchone() is not None

def _compra_existe(cursor, id):
    cursor.execute("SELECT id FROM compras WHERE id = %s AND eliminada = 0", (id,))
    return cursor.fetchone() is not None

def listado_compra(pagina=1, limite=20, corte_id=None, busqueda=None, categoria=None):
    try:
        offset = (pagina - 1) * limite

        where = "WHERE c.eliminada = 0 AND c.corte_id = %s"
        params = [corte_id]

        if categoria:
            where += " AND c.categoria = %s"
            params.append(categoria)

        if busqueda:
            where += " AND (c.descripcion LIKE %s OR p.nombre LIKE %s OR CAST(c.id AS CHAR) = %s)"
            params.extend([f"%{busqueda}%", f"%{busqueda}%", busqueda])

        with cursor_ctx() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*) FROM compras c
                JOIN proveedores p ON p.id = c.proveedor_id
                {where}
            """, tuple(params))
            total = cursor.fetchone()[0]

            # Resumen global del corte: no depende de q, de la categoria ni de
            # la paginacion. Los totales van separados por categoria.
            cursor.execute("""
                SELECT COUNT(*),
                       COALESCE(SUM(total), 0),
                       COALESCE(SUM(CASE WHEN categoria = 'insumo' THEN total ELSE 0 END), 0),
                       COALESCE(SUM(CASE WHEN categoria = 'insumo' THEN 1 ELSE 0 END), 0),
                       COALESCE(SUM(CASE WHEN categoria = 'domicilio' THEN total ELSE 0 END), 0),
                       COALESCE(SUM(CASE WHEN categoria = 'domicilio' THEN 1 ELSE 0 END), 0)
                FROM compras
                WHERE eliminada = 0 AND corte_id = %s
            """, (corte_id,))
            res = cursor.fetchone()

            cursor.execute(f"""
                SELECT c.id, c.proveedor_id, p.nombre, c.corte_id, c.usuario_id,
                       c.fecha, c.medio_pago, c.medio_pago_id, mp.nombre AS medio_pago_nombre,
                       c.total, c.descripcion, c.categoria, c.venta_id,
                       cv.nombre AS venta_cliente, v.estado AS venta_estado
                FROM compras c
                JOIN proveedores p ON p.id = c.proveedor_id
                LEFT JOIN medios_pago mp ON mp.id = c.medio_pago_id
                LEFT JOIN ventas v ON v.id = c.venta_id
                LEFT JOIN clientes cv ON cv.id = v.cliente_id
                {where}
                ORDER BY c.fecha DESC
                LIMIT %s OFFSET %s
            """, tuple(params + [limite, offset]))

            datos = cursor.fetchall()

        lista = []
        for fila in datos:
            com = compra(
                fila[0], fila[1], fila[3], fila[4], fila[5], fila[6],
                fila[9], fila[10], fila[7], fila[8],
                categoria=fila[11], venta_id=fila[12],
                venta_cliente=fila[13], venta_estado=fila[14],
            )
            d = com.toDic()
            d['nombre_proveedor'] = fila[2]
            lista.append(d)

        return {
            "total"        : total,
            "pagina"       : pagina,
            "limite"       : limite,
            "total_paginas": -(-total // limite),
            "compras"      : lista,
            "resumen"      : {
                "cantidad_compras": res[0],
                "total_gastado"   : float(res[1]),
                "por_categoria"   : {
                    "insumo"   : {"cantidad": int(res[3]), "total": float(res[2])},
                    "domicilio": {"cantidad": int(res[5]), "total": float(res[4])},
                }
            }
        }
    except Exception as e:
        raise Exception(str(e))


def obtener_compra(id):
    try:
        with cursor_ctx() as cursor:
            if not _compra_existe(cursor, id):
                return None, "Compra no encontrada"

            cursor.execute("""
                SELECT c.id, c.proveedor_id, p.nombre, c.corte_id, c.usuario_id,
                       c.fecha, c.medio_pago, c.medio_pago_id, mp.nombre AS medio_pago_nombre,
                       c.total, c.descripcion, c.categoria, c.venta_id,
                       cv.nombre AS venta_cliente, v.estado AS venta_estado
                FROM compras c
                JOIN proveedores p ON p.id = c.proveedor_id
                LEFT JOIN medios_pago mp ON mp.id = c.medio_pago_id
                LEFT JOIN ventas v ON v.id = c.venta_id
                LEFT JOIN clientes cv ON cv.id = v.cliente_id
                WHERE c.id = %s AND c.eliminada = 0
            """, (id,))
            fila = cursor.fetchone()

        com = compra(
            fila[0], fila[1], fila[3], fila[4], fila[5], fila[6],
            fila[9], fila[10], fila[7], fila[8],
            categoria=fila[11], venta_id=fila[12],
            venta_cliente=fila[13], venta_estado=fila[14],
        )
        d = com.toDic()
        d['nombre_proveedor'] = fila[2]
        return d, None
    except Exception as e:
        raise Exception(str(e))


def registro_compra(proveedor_id, corte_id, usuario_id, fecha, medio_pago, medio_pago_id, total, descripcion,
                    categoria="insumo", venta_id=None):
    try:
        with cursor_ctx() as cursor:
            cursor.execute("SELECT id FROM proveedores WHERE id = %s AND activo = 1", (proveedor_id,))
            if not cursor.fetchone():
                return None, f"El proveedor con id {proveedor_id} no existe o no está activo"

            if not _existe(cursor, "cortes", corte_id):
                return None, f"El corte con id {corte_id} no existe"

            cursor.execute("SELECT id FROM usuarios WHERE id = %s AND activo = 1", (usuario_id,))
            if not cursor.fetchone():
                return None, f"El usuario con id {usuario_id} no existe o no está activo"

            if float(total) <= 0:
                return None, "El total debe ser mayor a 0"

            # categoria/venta_id: error de validacion (400), no de conflicto.
            venta_id = _validar_categoria_venta(cursor, categoria, venta_id)

            cursor.execute("""
                INSERT INTO compras (proveedor_id, corte_id, usuario_id, fecha,
                                     medio_pago, medio_pago_id, total, descripcion,
                                     categoria, venta_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (proveedor_id, corte_id, usuario_id, fecha, medio_pago, medio_pago_id,
                  total, descripcion, categoria, venta_id))
            current_app.mysql.connection.commit()
            nuevo_id = cursor.lastrowid

        # Se relee para devolver categoria, venta_id y los datos de la venta.
        dato, _ = obtener_compra(nuevo_id)
        return dato, None
    except CompraInvalida:
        raise
    except Exception as e:
        raise Exception(str(e))


def actualizar_compra(id, proveedor_id, corte_id, usuario_id, fecha, medio_pago, medio_pago_id, total, descripcion,
                      categoria=None, venta_id=None):
    try:
        with cursor_ctx() as cursor:
            cursor.execute(
                "SELECT medio_pago, medio_pago_id, categoria, venta_id FROM compras WHERE id = %s AND eliminada = 0",
                (id,),
            )
            compra_actual = cursor.fetchone()
            if not compra_actual:
                return None, "Compra no encontrada"

            # Si la categoria no viene, se conserva la actual (junto con su
            # venta_id): el frontend viejo no puede reclasificar una compra de
            # domicilio por accidente.
            if categoria is None:
                categoria = compra_actual[2] or "insumo"
                if venta_id in (None, ""):
                    venta_id = compra_actual[3]
            elif categoria == (compra_actual[2] or "insumo") and venta_id in (None, ""):
                venta_id = compra_actual[3]

            # Si el medio no cambia y no viene cuenta, se conserva la cuenta
            # actual sin validar (permite editar solo el total de una compra antigua).
            if medio_pago == compra_actual[0] and medio_pago_id is None:
                medio_pago_id = compra_actual[1]
            else:
                medio_pago, medio_pago_id = resolver_medio_pago(medio_pago, medio_pago_id)

            cursor.execute("SELECT id FROM proveedores WHERE id = %s AND activo = 1", (proveedor_id,))
            if not cursor.fetchone():
                return None, f"El proveedor con id {proveedor_id} no existe o no está activo"

            if not _existe(cursor, "cortes", corte_id):
                return None, f"El corte con id {corte_id} no existe"

            cursor.execute("SELECT id FROM usuarios WHERE id = %s AND activo = 1", (usuario_id,))
            if not cursor.fetchone():
                return None, f"El usuario con id {usuario_id} no existe o no está activo"

            if float(total) <= 0:
                return None, "El total debe ser mayor a 0"

            venta_id = _validar_categoria_venta(cursor, categoria, venta_id)

            cursor.execute("""
                UPDATE compras
                SET proveedor_id = %s, corte_id = %s, usuario_id = %s,
                    fecha = %s, medio_pago = %s, medio_pago_id = %s,
                    total = %s, descripcion = %s,
                    categoria = %s, venta_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (proveedor_id, corte_id, usuario_id, fecha, medio_pago, medio_pago_id,
                  total, descripcion, categoria, venta_id, id))
            current_app.mysql.connection.commit()

        dato, _ = obtener_compra(id)
        return dato, None
    except CompraInvalida:
        raise
    except Exception as e:
        raise Exception(str(e))


def eliminar_compra(id):
    try:
        with cursor_ctx() as cursor:
            if not _compra_existe(cursor, id):
                return False, "Compra no encontrada"

            cursor.execute(
                "UPDATE compras SET eliminada = 1, updated_at = CURRENT_TIMESTAMP WHERE id = %s", (id,)
            )
            current_app.mysql.connection.commit()
        return True, None
    except Exception as e:
        raise Exception(str(e))