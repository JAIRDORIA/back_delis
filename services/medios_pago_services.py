import json
from datetime import datetime, timedelta
from decimal import Decimal

from flask import current_app
from MySQLdb import IntegrityError

from models.medios_pago_model import medios_pago
from utils.db import cursor_ctx

# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────

_SELECT = """
    SELECT id, nombre, tipo, titular, saldo_inicial,
           activo, es_sistema, orden, created_at, updated_at
    FROM medios_pago
"""

# Tablas que referencian medios_pago. Los nombres son fijos del módulo
# (nunca provienen del frontend).
_TABLAS_REFERENCIA = (
    ("abonos",           "medio_pago_id"),
    ("compras",          "medio_pago_id"),
    ("movimientos_caja", "medio_pago_id"),
    ("prestamos",        "medio_pago_id"),
    ("prestamos",        "medio_pago_pago_id"),
    ("pagos_prestamos",  "medio_pago_id"),
)

_NO_ENVIADO = object()


class MedioPagoInvalido(Exception):
    """Excepción de validación de medio de pago.

    Los controllers capturan esta excepción y la convierten en un 400
    con `mensaje`."""
    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


# ─────────────────────────────────────────────
#  VALIDACIÓN DE MEDIO DE PAGO
# ─────────────────────────────────────────────

def resolver_medio_pago(medio_pago, medio_pago_id):
    """Valida el par (medio_pago, medio_pago_id) y devuelve la tupla
    normalizada `(medio_pago, medio_pago_id)`.

    Reglas:
    - 'efectivo': usa siempre la cuenta de sistema id=1. Si llega otro id, error.
    - 'transferencia': exige `medio_pago_id` de una fila existente, de tipo
      'transferencia', activa y no de sistema.
    - cualquier otro valor (None, 'otro', etc.): error.

    Lanza `MedioPagoInvalido` para que el controller lo convierta en 400.
    """
    if medio_pago == "efectivo":
        if medio_pago_id is not None:
            try:
                id_num = int(medio_pago_id)
            except (TypeError, ValueError):
                raise MedioPagoInvalido("El medio de pago efectivo usa la cuenta de sistema (1)")
            if id_num != 1:
                raise MedioPagoInvalido("El medio de pago efectivo usa la cuenta de sistema (1)")
        return "efectivo", 1

    if medio_pago == "transferencia":
        if medio_pago_id is None:
            raise MedioPagoInvalido("Selecciona la cuenta de transferencia")

        try:
            id_num = int(medio_pago_id)
        except (TypeError, ValueError):
            raise MedioPagoInvalido("Selecciona la cuenta de transferencia")

        with cursor_ctx() as cursor:
            cursor.execute(
                "SELECT id, tipo, activo, es_sistema FROM medios_pago WHERE id = %s",
                (id_num,),
            )
            fila = cursor.fetchone()

        if not fila:
            raise MedioPagoInvalido("La cuenta de transferencia seleccionada no existe")

        if fila[1] != "transferencia" or fila[2] != 1 or fila[3] != 0:
            raise MedioPagoInvalido(
                "La cuenta de transferencia seleccionada no está disponible "
                "(debe ser de tipo transferencia, estar activa y no ser de sistema)"
            )

        return "transferencia", id_num

    raise MedioPagoInvalido("Medio de pago inválido: solo se permite 'efectivo' o 'transferencia'")


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _fila_a_dic(fila):
    return medios_pago(
        fila[0], fila[1], fila[2], fila[3], fila[4],
        fila[5], fila[6], fila[7], fila[8], fila[9],
    ).toDic()


def _obtener_fila(cursor, id):
    cursor.execute(_SELECT + " WHERE id = %s", (id,))
    return cursor.fetchone()


def _nombre_duplicado(cursor, nombre, excluir_id=None):
    """La columna `nombre` es UNIQUE; la comparación queda a cargo del
    collation de la columna (igual que en otros módulos)."""
    if excluir_id is None:
        cursor.execute("SELECT id FROM medios_pago WHERE nombre = %s", (nombre,))
    else:
        cursor.execute(
            "SELECT id FROM medios_pago WHERE nombre = %s AND id != %s",
            (nombre, excluir_id),
        )
    return cursor.fetchone() is not None


def _registrar_auditoria(cursor, usuario_id, accion, registro_id, descripcion,
                         datos_anteriores=None, datos_nuevos=None,
                         tabla_afectada="medios_pago"):
    cursor.execute(
        """
        INSERT INTO auditoria (usuario_id, accion, tabla_afectada, registro_id,
                               descripcion, datos_anteriores, datos_nuevos)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            usuario_id,
            accion,
            tabla_afectada,
            registro_id,
            descripcion,
            json.dumps(datos_anteriores) if datos_anteriores is not None else None,
            json.dumps(datos_nuevos) if datos_nuevos is not None else None,
        ),
    )


# ─────────────────────────────────────────────
#  LISTADO Y DETALLE
# ─────────────────────────────────────────────

def listado_medios_pago(activos=None, tipo=None, asignables=None):
    """Lista los medios de pago ordenados por orden y nombre.
    `activos` es un bool (o None para traer todos) y `tipo` ya viene
    validado contra la lista blanca en el controller.
    `asignables` (bool) equivale a tipo='transferencia' AND activo=1 AND
    es_sistema=0, y se combina con los demás filtros."""
    try:
        where = []
        params = []

        if activos is not None:
            where.append("activo = %s")
            params.append(1 if activos else 0)

        if tipo is not None:
            where.append("tipo = %s")
            params.append(tipo)

        if asignables:
            where.append("tipo = %s")
            params.append("transferencia")
            where.append("activo = %s")
            params.append(1)
            where.append("es_sistema = %s")
            params.append(0)

        sql = _SELECT
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY orden ASC, nombre ASC"

        with cursor_ctx() as cursor:
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

        return [_fila_a_dic(fila) for fila in filas]
    except Exception as e:
        raise Exception(str(e))


def obtener_medio_pago(id):
    try:
        with cursor_ctx() as cursor:
            fila = _obtener_fila(cursor, id)
        return _fila_a_dic(fila) if fila else None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  SALDOS DE CUENTAS DE TRANSFERENCIA
# ─────────────────────────────────────────────

def saldos_transferencias(buscar=None):
    """Saldos de la vista v_saldos_cuenta para cuentas de transferencia
    no de sistema. Incluye activas, y las inactivas solo si tienen saldo.
    `buscar` filtra por nombre o titular (LIKE), sin afectar el total."""
    try:
        where = "tipo = 'transferencia' AND es_sistema = 0 AND (activo = 1 OR saldo <> 0)"
        params = []

        with cursor_ctx() as cursor:
            cursor.execute(
                f"SELECT COALESCE(SUM(saldo), 0) FROM v_saldos_cuenta WHERE {where}",
                tuple(params),
            )
            total_transferencia = float(cursor.fetchone()[0])

            sql = f"""
                SELECT medio_pago_id, nombre, titular, activo,
                       saldo_inicial, ingresos, egresos, saldo
                FROM v_saldos_cuenta
                WHERE {where}
            """
            if buscar:
                sql += " AND (nombre LIKE %s OR titular LIKE %s)"
                params.extend([f"%{buscar}%", f"%{buscar}%"])
            sql += " ORDER BY orden ASC, nombre ASC"

            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

        cuentas = [
            {
                "medio_pago_id": f[0],
                "nombre"       : f[1],
                "titular"      : f[2],
                "activo"       : f[3],
                "saldo_inicial": float(f[4]) if f[4] is not None else 0.0,
                "ingresos"     : float(f[5]) if f[5] is not None else 0.0,
                "egresos"      : float(f[6]) if f[6] is not None else 0.0,
                "saldo"        : float(f[7]) if f[7] is not None else 0.0,
            }
            for f in filas
        ]

        return {
            "total_transferencia": total_transferencia,
            "cantidad"           : len(cuentas),
            "cuentas"            : cuentas,
        }
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  MOVIMIENTOS DE CUENTA
# ─────────────────────────────────────────────

def movimientos_cuenta(id, pagina=1, limite=20, desde=None, hasta=None):
    """Movimientos paginados de una cuenta según la vista v_movimientos_cuenta.

    Devuelve (cuenta, total, filas) o (None, None, None) si la cuenta no
    existe. `desde` y `hasta` son cadenas 'YYYY-MM-DD' ya validadas en el
    controller; ambos filtros incluyen el día completo (hasta se convierte
    a fecha < día siguiente).
    """
    offset = (pagina - 1) * limite
    where = ["medio_pago_id = %s"]
    params = [id]

    if desde:
        where.append("fecha >= %s")
        params.append(desde)

    if hasta:
        where.append("fecha < %s")
        params.append(
            (datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        )

    where_sql = " AND ".join(where)

    with cursor_ctx() as cursor:
        cursor.execute(
            "SELECT id, nombre, titular FROM medios_pago WHERE id = %s",
            (id,),
        )
        fila = cursor.fetchone()
        if not fila:
            return None, None, None

        cuenta = {"id": fila[0], "nombre": fila[1], "titular": fila[2]}

        cursor.execute(
            f"SELECT COUNT(*) FROM v_movimientos_cuenta WHERE {where_sql}",
            tuple(params),
        )
        total = int(cursor.fetchone()[0])

        cursor.execute(
            f"""
            SELECT medio_pago_id, tipo, concepto, referencia_id, monto,
                   fecha, corte_id, usuario_id, descripcion
            FROM v_movimientos_cuenta
            WHERE {where_sql}
            ORDER BY fecha DESC
            LIMIT %s OFFSET %s
            """,
            tuple(params) + (limite, offset),
        )
        filas = cursor.fetchall()

    return cuenta, total, filas


# ─────────────────────────────────────────────
#  CREAR
# ─────────────────────────────────────────────

def crear_medio_pago(nombre, titular, saldo_inicial, orden, usuario_id):
    """Crea una cuenta de medio de pago. El tipo siempre se guarda como
    'transferencia' (se ignora lo que envíe el frontend).
    Si `orden` viene None se calcula MAX(orden) + 1 en la misma transacción."""
    try:
        with cursor_ctx() as cursor:
            if _nombre_duplicado(cursor, nombre):
                return None, f"Ya existe un medio de pago con el nombre '{nombre}'"

            if orden is None:
                cursor.execute("SELECT COALESCE(MAX(orden), 0) + 1 FROM medios_pago")
                orden = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO medios_pago (nombre, tipo, titular, saldo_inicial, orden)
                VALUES (%s, 'transferencia', %s, %s, %s)
                """,
                (nombre, titular, saldo_inicial, orden),
            )
            nuevo_id = cursor.lastrowid

            fila = _obtener_fila(cursor, nuevo_id)
            nuevo = _fila_a_dic(fila)

            _registrar_auditoria(
                cursor,
                usuario_id,
                "crear",
                nuevo_id,
                f"Creación de medio de pago '{nombre}'",
                datos_nuevos=nuevo,
            )

            current_app.mysql.connection.commit()

        return nuevo, None
    except IntegrityError:
        # La columna es UNIQUE: cubre la carrera entre la validación y el INSERT.
        return None, f"Ya existe un medio de pago con el nombre '{nombre}'"
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  ACTUALIZAR
# ─────────────────────────────────────────────

def actualizar_medio_pago(id, usuario_id, nombre=_NO_ENVIADO, titular=_NO_ENVIADO,
                          saldo_inicial=_NO_ENVIADO, orden=_NO_ENVIADO):
    """Edita nombre, titular, saldo_inicial y/u orden.
    El tipo no se puede cambiar y el nombre de las filas de sistema no se toca."""
    try:
        with cursor_ctx() as cursor:
            fila = _obtener_fila(cursor, id)
            if not fila:
                return None, "Medio de pago no encontrado"

            anterior = _fila_a_dic(fila)
            es_sistema = anterior["es_sistema"]

            campos = []
            valores = []

            if nombre is not _NO_ENVIADO:
                if es_sistema and nombre != anterior["nombre"]:
                    return None, "No se puede cambiar el nombre de un medio de pago del sistema"
                if _nombre_duplicado(cursor, nombre, excluir_id=id):
                    return None, f"Ya existe otro medio de pago con el nombre '{nombre}'"
                campos.append("nombre = %s")
                valores.append(nombre)

            if titular is not _NO_ENVIADO:
                campos.append("titular = %s")
                valores.append(titular)

            if saldo_inicial is not _NO_ENVIADO:
                campos.append("saldo_inicial = %s")
                valores.append(saldo_inicial)

            if orden is not _NO_ENVIADO:
                campos.append("orden = %s")
                valores.append(orden)

            if not campos:
                return None, "No hay cambios para actualizar"

            campos.append("updated_at = CURRENT_TIMESTAMP")
            valores.append(id)

            cursor.execute(
                f"UPDATE medios_pago SET {', '.join(campos)} WHERE id = %s",
                tuple(valores),
            )

            fila_nueva = _obtener_fila(cursor, id)
            nuevo = _fila_a_dic(fila_nueva)

            _registrar_auditoria(
                cursor,
                usuario_id,
                "editar",
                id,
                f"Edición de medio de pago '{nuevo['nombre']}'",
                datos_anteriores=anterior,
                datos_nuevos=nuevo,
            )

            current_app.mysql.connection.commit()

        return nuevo, None
    except IntegrityError:
        nombre_mostrado = nombre if nombre is not _NO_ENVIADO else ""
        return None, f"Ya existe otro medio de pago con el nombre '{nombre_mostrado}'"
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  CAMBIAR ESTADO
# ─────────────────────────────────────────────

def cambiar_estado_medio_pago(id, activo, usuario_id):
    """Activa/desactiva un medio de pago. La fila de tipo 'efectivo'
    no se puede desactivar."""
    try:
        with cursor_ctx() as cursor:
            fila = _obtener_fila(cursor, id)
            if not fila:
                return None, "Medio de pago no encontrado"

            anterior = _fila_a_dic(fila)
            nuevo_activo = 1 if activo else 0

            if not activo and anterior["tipo"] == "efectivo":
                return None, "No se puede desactivar el medio de pago de tipo efectivo"

            if anterior["activo"] == nuevo_activo:
                estado = "activo" if nuevo_activo else "inactivo"
                return None, f"El medio de pago ya está {estado}"

            cursor.execute(
                """
                UPDATE medios_pago
                SET activo = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (nuevo_activo, id),
            )

            fila_nueva = _obtener_fila(cursor, id)
            nuevo = _fila_a_dic(fila_nueva)

            _registrar_auditoria(
                cursor,
                usuario_id,
                "cambiar estado",
                id,
                f"Cambio de estado del medio de pago '{nuevo['nombre']}' a {nuevo_activo}",
                datos_anteriores=anterior,
                datos_nuevos=nuevo,
            )

            current_app.mysql.connection.commit()

        return nuevo, None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  ELIMINAR
# ─────────────────────────────────────────────

def eliminar_medio_pago(id, usuario_id):
    """Elimina solo medios de pago no usados y que no sean de sistema.
    Si tiene registros asociados sugiere desactivarlo en vez de borrarlo."""
    try:
        with cursor_ctx() as cursor:
            fila = _obtener_fila(cursor, id)
            if not fila:
                return False, "Medio de pago no encontrado"

            anterior = _fila_a_dic(fila)

            if anterior["es_sistema"] == 1:
                return False, "No se puede eliminar un medio de pago del sistema"

            for tabla, columna in _TABLAS_REFERENCIA:
                cursor.execute(
                    f"SELECT 1 FROM {tabla} WHERE {columna} = %s LIMIT 1",
                    (id,),
                )
                if cursor.fetchone():
                    return False, (
                        "No se puede eliminar el medio de pago porque tiene "
                        "movimientos asociados. Sugerencia: desactívalo para "
                        "que no se use en nuevos registros."
                    )

            cursor.execute("DELETE FROM medios_pago WHERE id = %s", (id,))

            _registrar_auditoria(
                cursor,
                usuario_id,
                "eliminar",
                id,
                f"Eliminación de medio de pago '{anterior['nombre']}'",
                datos_anteriores=anterior,
                datos_nuevos=None,
            )

            current_app.mysql.connection.commit()

        return True, None
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────────
#  RETIRO DE CUENTA A AHORROS
# ─────────────────────────────────────────────

def retirar_cuenta(medio_pago_id, monto, descripcion, usuario_id):
    """Registra un retiro de una cuenta de transferencia a ahorros.

    Bloquea la cuenta con SELECT ... FOR UPDATE y valida el saldo contra
    v_saldos_cuenta dentro de la misma transacción. El retiro se asocia
    siempre al corte abierto; no lo envía el frontend.
    Devuelve (retiro, error).
    """
    with cursor_ctx() as cursor:
        try:
            cursor.execute(
                """
                SELECT id, nombre, tipo, activo, es_sistema
                FROM medios_pago
                WHERE id = %s
                FOR UPDATE
                """,
                (medio_pago_id,),
            )
            fila = cursor.fetchone()
            if not fila:
                current_app.mysql.connection.rollback()
                return None, "Medio de pago no encontrado"

            nombre = fila[1]
            tipo = fila[2]
            es_sistema = fila[4]

            if tipo != "transferencia":
                current_app.mysql.connection.rollback()
                return None, "Solo se puede retirar de una cuenta de transferencia"

            if es_sistema:
                current_app.mysql.connection.rollback()
                return None, "No se puede retirar de una cuenta del sistema"

            cursor.execute(
                "SELECT id FROM cortes WHERE estado = 'abierto' ORDER BY id ASC LIMIT 1"
            )
            corte = cursor.fetchone()
            if not corte:
                current_app.mysql.connection.rollback()
                return None, "No hay un corte abierto para registrar el retiro"
            corte_id = corte[0]

            cursor.execute(
                "SELECT saldo FROM v_saldos_cuenta WHERE medio_pago_id = %s",
                (medio_pago_id,),
            )
            saldo_fila = cursor.fetchone()
            saldo_anterior = (
                Decimal(str(saldo_fila[0]))
                if saldo_fila and saldo_fila[0] is not None
                else Decimal("0.00")
            )

            if monto > saldo_anterior:
                current_app.mysql.connection.rollback()
                return None, (
                    f"Saldo insuficiente en la cuenta '{nombre}': "
                    f"disponible {saldo_anterior:.2f}"
                )

            cursor.execute(
                """
                INSERT INTO retiros_cuentas
                    (medio_pago_id, corte_id, usuario_id, monto, descripcion)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (medio_pago_id, corte_id, usuario_id, monto, descripcion),
            )
            retiro_id = cursor.lastrowid
            saldo_nuevo = saldo_anterior - monto

            cursor.execute(
                "SELECT fecha FROM retiros_cuentas WHERE id = %s",
                (retiro_id,),
            )
            fecha = cursor.fetchone()[0]

            _registrar_auditoria(
                cursor,
                usuario_id,
                "crear",
                retiro_id,
                f"Retiro a ahorros de la cuenta '{nombre}'",
                datos_anteriores={"saldo_disponible": float(saldo_anterior)},
                datos_nuevos={
                    "medio_pago_id": medio_pago_id,
                    "corte_id": corte_id,
                    "monto": float(monto),
                    "descripcion": descripcion,
                    "saldo_nuevo": float(saldo_nuevo),
                },
                tabla_afectada="retiros_cuentas",
            )

            current_app.mysql.connection.commit()
        except Exception:
            current_app.mysql.connection.rollback()
            raise

    return {
        "id": retiro_id,
        "medio_pago_id": medio_pago_id,
        "nombre": nombre,
        "monto": float(monto),
        "saldo_anterior": float(saldo_anterior),
        "saldo_nuevo": float(saldo_nuevo),
        "corte_id": corte_id,
        "fecha": str(fecha) if fecha is not None else None,
    }, None


def vaciar_cuentas_transferencia(descripcion, usuario_id):
    """Retira a ahorros el saldo completo de todas las cuentas de
    transferencia no de sistema con saldo > 0.

    Todo ocurre en una sola transacción: se bloquean las cuentas con
    FOR UPDATE, se lee el saldo de cada una en v_saldos_cuenta y se inserta
    un retiro (más su auditoría) por el saldo completo en el corte abierto.
    Si algo falla se revierte todo. Devuelve (resultado, error).
    """
    with cursor_ctx() as cursor:
        try:
            cursor.execute(
                "SELECT id FROM cortes WHERE estado = 'abierto' ORDER BY id ASC LIMIT 1"
            )
            corte = cursor.fetchone()
            if not corte:
                current_app.mysql.connection.rollback()
                return None, "No hay un corte abierto para registrar los retiros"
            corte_id = corte[0]

            cursor.execute(
                """
                SELECT id, nombre
                FROM medios_pago
                WHERE tipo = 'transferencia' AND es_sistema = 0
                ORDER BY id ASC
                FOR UPDATE
                """
            )
            cuentas = cursor.fetchall()

            retiros = []
            total = Decimal("0.00")

            for medio_pago_id, nombre in cuentas:
                cursor.execute(
                    "SELECT saldo FROM v_saldos_cuenta WHERE medio_pago_id = %s",
                    (medio_pago_id,),
                )
                saldo_fila = cursor.fetchone()
                saldo_anterior = (
                    Decimal(str(saldo_fila[0]))
                    if saldo_fila and saldo_fila[0] is not None
                    else Decimal("0.00")
                )

                if saldo_anterior <= 0:
                    continue

                cursor.execute(
                    """
                    INSERT INTO retiros_cuentas
                        (medio_pago_id, corte_id, usuario_id, monto, descripcion)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (medio_pago_id, corte_id, usuario_id, saldo_anterior, descripcion),
                )
                retiro_id = cursor.lastrowid

                _registrar_auditoria(
                    cursor,
                    usuario_id,
                    "crear",
                    retiro_id,
                    f"Retiro a ahorros de la cuenta '{nombre}' (vaciado)",
                    datos_anteriores={"saldo_disponible": float(saldo_anterior)},
                    datos_nuevos={
                        "medio_pago_id": medio_pago_id,
                        "corte_id": corte_id,
                        "monto": float(saldo_anterior),
                        "descripcion": descripcion,
                        "saldo_nuevo": 0.0,
                    },
                    tabla_afectada="retiros_cuentas",
                )

                total += saldo_anterior
                retiros.append({
                    "medio_pago_id": medio_pago_id,
                    "nombre": nombre,
                    "monto": float(saldo_anterior),
                })

            if not retiros:
                current_app.mysql.connection.rollback()
                return {"cantidad": 0, "total": 0.0, "retiros": []}, None

            current_app.mysql.connection.commit()
        except Exception:
            current_app.mysql.connection.rollback()
            raise

    return {
        "cantidad": len(retiros),
        "total": float(total),
        "retiros": retiros,
    }, None
