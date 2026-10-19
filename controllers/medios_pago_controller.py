from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import g, jsonify, request

from services.medios_pago_services import (
    listado_medios_pago,
    obtener_medio_pago,
    saldos_transferencias,
    movimientos_cuenta,
    crear_medio_pago,
    actualizar_medio_pago,
    cambiar_estado_medio_pago,
    eliminar_medio_pago,
    retirar_cuenta,
    vaciar_cuentas_transferencia,
)

TIPOS_VALIDOS = ("efectivo", "transferencia")


# ─────────────────────────────────────────────
#  HELPERS DE VALIDACIÓN
# ─────────────────────────────────────────────

def _validar_id(id):
    try:
        id_num = int(id)
    except (ValueError, TypeError):
        return None, "El id debe ser un número entero"
    if id_num <= 0:
        return None, "El id debe ser mayor a 0"
    return id_num, None


def _validar_nombre(valor):
    if not isinstance(valor, str):
        return None, "El nombre debe ser texto"
    nombre = valor.strip()
    if nombre == "":
        return None, "El nombre no puede estar vacío"
    if len(nombre) > 80:
        return None, "El nombre no puede exceder 80 caracteres"
    return nombre, None


def _validar_titular(valor):
    if valor is None:
        return None, None
    if not isinstance(valor, str):
        return None, "El titular debe ser texto"
    titular = valor.strip()
    if titular == "":
        return None, None
    if len(titular) > 100:
        return None, "El titular no puede exceder 100 caracteres"
    return titular, None


def _validar_saldo_inicial(valor):
    if valor is None:
        return 0.0, None
    try:
        saldo = float(valor)
    except (ValueError, TypeError):
        return None, "El saldo_inicial debe ser un número"
    if saldo < 0:
        return None, "El saldo_inicial no puede ser negativo"
    return saldo, None


def _validar_orden(valor):
    if valor is None:
        return None, None
    try:
        orden = int(valor)
    except (ValueError, TypeError):
        return None, "El orden debe ser un número entero"
    return orden, None


def _validar_activo(valor):
    if isinstance(valor, bool):
        return int(valor), None
    if isinstance(valor, int) and valor in (0, 1):
        return valor, None
    if isinstance(valor, str) and valor.strip() in ("0", "1"):
        return int(valor.strip()), None
    return None, "El campo activo debe ser true o false"


def _validar_fecha(valor, nombre):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").strftime("%Y-%m-%d"), None
    except (ValueError, TypeError):
        return None, f"El filtro {nombre} debe tener formato YYYY-MM-DD"


def _validar_monto_retiro(valor):
    if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)):
        return None, "El monto debe ser un número"
    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return None, "El monto debe ser un número"
    if not monto.is_finite():
        return None, "El monto debe ser un número"
    if monto <= 0:
        return None, "El monto debe ser mayor a 0"
    try:
        if monto != monto.quantize(Decimal("0.01")):
            return None, "El monto no puede tener más de 2 decimales"
    except InvalidOperation:
        return None, "El monto debe ser un número válido"
    return monto, None


def _validar_descripcion_retiro(valor, defecto="Retiro a ahorros"):
    if valor is None:
        return defecto, None
    if not isinstance(valor, str):
        return None, "La descripción debe ser texto"
    descripcion = valor.strip()
    if descripcion == "":
        return defecto, None
    if len(descripcion) > 255:
        return None, "La descripción no puede exceder 255 caracteres"
    return descripcion, None


def _status_para_error(error):
    low = error.lower()
    if "no encontrado" in low:
        return 404
    if "ya existe" in low or "duplicado" in low:
        return 409
    if "asociados" in low:
        return 409
    return 400


def _body_json():
    if not request.is_json:
        return None, "El cuerpo debe ser JSON"
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, "El cuerpo debe ser JSON"
    return data, None


def _body_json_opcional():
    """Como _body_json, pero acepta una petición sin cuerpo."""
    if not request.is_json:
        if request.content_length in (None, 0):
            return {}, None
        return None, "El cuerpo debe ser JSON"
    data = request.get_json(silent=True)
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "El cuerpo debe ser JSON"
    return data, None


# ─────────────────────────────────────────────
#  ENDPOINTS
# ─────────────────────────────────────────────

def cntListado():
    """GET /medios-pago/  (cualquier rol autenticado salvo cocina)
    Filtros opcionales: ?activos=1, ?tipo=transferencia y ?asignables=1"""
    try:
        activos = None
        activos_raw = request.args.get("activos")
        if activos_raw is not None:
            if activos_raw not in ("0", "1"):
                return jsonify({"mensaje": "El filtro activos debe ser 0 o 1"}), 400
            activos = activos_raw == "1"

        tipo = None
        tipo_raw = request.args.get("tipo")
        if tipo_raw is not None:
            tipo = tipo_raw.strip().lower()
            if tipo not in TIPOS_VALIDOS:
                return jsonify({
                    "mensaje": f"El filtro tipo debe ser uno de: {list(TIPOS_VALIDOS)}"
                }), 400

        asignables = None
        asignables_raw = request.args.get("asignables")
        if asignables_raw is not None:
            if asignables_raw not in ("0", "1"):
                return jsonify({"mensaje": "El filtro asignables debe ser 0 o 1"}), 400
            asignables = asignables_raw == "1"

        datos = listado_medios_pago(activos=activos, tipo=tipo, asignables=asignables)
        return jsonify({"datos": datos, "total": len(datos)}), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al listar medios de pago: {str(e)}"}), 500


def cntObtener(id):
    """GET /medios-pago/<id>"""
    id_num, error = _validar_id(id)
    if error:
        return jsonify({"mensaje": error}), 400

    try:
        dato = obtener_medio_pago(id_num)
        if dato is None:
            return jsonify({"mensaje": "Medio de pago no encontrado"}), 404
        return jsonify(dato), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener medio de pago: {str(e)}"}), 500


def cntSaldos():
    """GET /medios-pago/saldos
    Saldos de cuentas de transferencia no de sistema. Filtro opcional
    ?buscar=texto (nombre o titular)."""
    try:
        buscar = request.args.get("buscar", "").strip()
        datos = saldos_transferencias(buscar or None)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener saldos de medios de pago: {str(e)}"}), 500


def cntMovimientos(id):
    """GET /medios-pago/<id>/movimientos
    Movimientos de la cuenta (v_movimientos_cuenta) ordenados por fecha DESC.
    Paginación ?pagina= y ?limite= (máximo 100). Filtros opcionales
    ?desde=YYYY-MM-DD y ?hasta=YYYY-MM-DD (días completos)."""
    id_num, error = _validar_id(id)
    if error:
        return jsonify({"mensaje": error}), 400

    pagina = request.args.get("pagina", 1, type=int)
    limite = request.args.get("limite", 20, type=int)

    if pagina is None or pagina < 1:
        return jsonify({"mensaje": "La página debe ser mayor a 0"}), 400
    if limite is None or limite < 1 or limite > 100:
        return jsonify({"mensaje": "El límite debe ser entre 1 y 100"}), 400

    desde = None
    desde_raw = request.args.get("desde")
    if desde_raw is not None:
        desde, error = _validar_fecha(desde_raw, "desde")
        if error:
            return jsonify({"mensaje": error}), 400

    hasta = None
    hasta_raw = request.args.get("hasta")
    if hasta_raw is not None:
        hasta, error = _validar_fecha(hasta_raw, "hasta")
        if error:
            return jsonify({"mensaje": error}), 400

    if desde and hasta and hasta < desde:
        return jsonify({"mensaje": "El filtro hasta debe ser mayor o igual a desde"}), 400

    try:
        cuenta, total, filas = movimientos_cuenta(id_num, pagina, limite, desde, hasta)
        if cuenta is None:
            return jsonify({"mensaje": "Medio de pago no encontrado"}), 404

        movimientos = [
            {
                "medio_pago_id": f[0],
                "tipo"         : f[1],
                "concepto"     : f[2],
                "referencia_id": f[3],
                "monto"        : float(f[4]) if f[4] is not None else 0.0,
                "fecha"        : str(f[5]) if f[5] is not None else None,
                "corte_id"     : f[6],
                "usuario_id"   : f[7],
                "descripcion"  : f[8],
            }
            for f in filas
        ]

        return jsonify({
            "cuenta": cuenta,
            "total": total,
            "movimientos": movimientos,
        }), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener movimientos del medio de pago: {str(e)}"}), 500


def cntCrear():
    """POST /medios-pago/  (admin)
    Crea una cuenta. El tipo siempre se guarda como 'transferencia'."""
    data, error = _body_json()
    if error:
        return jsonify({"mensaje": error}), 400

    if "nombre" not in data:
        return jsonify({"mensaje": "Faltan los siguientes campos: ['nombre']"}), 400

    nombre, error = _validar_nombre(data.get("nombre"))
    if error:
        return jsonify({"mensaje": error}), 400

    titular, error = _validar_titular(data.get("titular"))
    if error:
        return jsonify({"mensaje": error}), 400

    saldo_inicial, error = _validar_saldo_inicial(data.get("saldo_inicial"))
    if error:
        return jsonify({"mensaje": error}), 400

    orden, error = _validar_orden(data.get("orden"))
    if error:
        return jsonify({"mensaje": error}), 400

    usuario_id = g.usuario["id"]

    try:
        dato, error = crear_medio_pago(nombre, titular, saldo_inicial, orden, usuario_id)
        if error:
            return jsonify({"mensaje": error}), _status_para_error(error)
        return jsonify({"mensaje": "Medio de pago creado", "datos": dato}), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error al crear medio de pago: {str(e)}"}), 500


def cntActualizar(id):
    """PUT /medios-pago/<id>  (admin)
    Edita nombre, titular, saldo_inicial y/u orden. El tipo no se cambia."""
    id_num, error = _validar_id(id)
    if error:
        return jsonify({"mensaje": error}), 400

    data, error = _body_json()
    if error:
        return jsonify({"mensaje": error}), 400

    editables = ("nombre", "titular", "saldo_inicial", "orden")
    if not any(campo in data for campo in editables):
        return jsonify({
            "mensaje": f"Debe enviar al menos uno de: {list(editables)}"
        }), 400

    kwargs = {}

    if "nombre" in data:
        nombre, error = _validar_nombre(data.get("nombre"))
        if error:
            return jsonify({"mensaje": error}), 400
        kwargs["nombre"] = nombre

    if "titular" in data:
        titular, error = _validar_titular(data.get("titular"))
        if error:
            return jsonify({"mensaje": error}), 400
        kwargs["titular"] = titular

    if "saldo_inicial" in data:
        saldo_inicial, error = _validar_saldo_inicial(data.get("saldo_inicial"))
        if error:
            return jsonify({"mensaje": error}), 400
        kwargs["saldo_inicial"] = saldo_inicial

    if "orden" in data:
        orden, error = _validar_orden(data.get("orden"))
        if error:
            return jsonify({"mensaje": error}), 400
        kwargs["orden"] = orden

    usuario_id = g.usuario["id"]

    try:
        dato, error = actualizar_medio_pago(id_num, usuario_id=usuario_id, **kwargs)
        if error:
            return jsonify({"mensaje": error}), _status_para_error(error)
        return jsonify({"mensaje": "Medio de pago actualizado", "datos": dato}), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al actualizar medio de pago: {str(e)}"}), 500


def cntCambiarEstado(id):
    """PATCH /medios-pago/<id>/estado  (admin)  body {activo: true|false}"""
    id_num, error = _validar_id(id)
    if error:
        return jsonify({"mensaje": error}), 400

    data, error = _body_json()
    if error:
        return jsonify({"mensaje": error}), 400

    if "activo" not in data:
        return jsonify({"mensaje": "Faltan los siguientes campos: ['activo']"}), 400

    activo, error = _validar_activo(data.get("activo"))
    if error:
        return jsonify({"mensaje": error}), 400

    usuario_id = g.usuario["id"]

    try:
        dato, error = cambiar_estado_medio_pago(id_num, activo, usuario_id)
        if error:
            return jsonify({"mensaje": error}), _status_para_error(error)
        return jsonify({"mensaje": "Estado actualizado", "datos": dato}), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al cambiar estado del medio de pago: {str(e)}"}), 500


def cntEliminar(id):
    """DELETE /medios-pago/<id>  (admin)"""
    id_num, error = _validar_id(id)
    if error:
        return jsonify({"mensaje": error}), 400

    usuario_id = g.usuario["id"]

    try:
        ok, error = eliminar_medio_pago(id_num, usuario_id)
        if error:
            return jsonify({"mensaje": error}), _status_para_error(error)
        return jsonify({"mensaje": f"Medio de pago {id_num} eliminado"}), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al eliminar medio de pago: {str(e)}"}), 500


def cntRetiro(id):
    """POST /medios-pago/<id>/retiros  (admin y cajero, igual que /cortes/cerrar)
    Retira dinero de una cuenta de transferencia a ahorros.
    Body: {monto, descripcion?}. El usuario sale del token y el corte del
    corte abierto, nunca del cuerpo."""
    id_num, error = _validar_id(id)
    if error:
        return jsonify({"mensaje": error}), 400

    data, error = _body_json()
    if error:
        return jsonify({"mensaje": error}), 400

    if "monto" not in data:
        return jsonify({"mensaje": "Faltan los siguientes campos: ['monto']"}), 400

    monto, error = _validar_monto_retiro(data.get("monto"))
    if error:
        return jsonify({"mensaje": error}), 400

    descripcion, error = _validar_descripcion_retiro(data.get("descripcion"))
    if error:
        return jsonify({"mensaje": error}), 400

    usuario_id = g.usuario["id"]

    try:
        retiro, error = retirar_cuenta(id_num, monto, descripcion, usuario_id)
        if error:
            return jsonify({"mensaje": error}), _status_para_error(error)
        return jsonify({"mensaje": "Retiro registrado", "retiro": retiro}), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar retiro: {str(e)}"}), 500


def cntVaciar():
    """POST /medios-pago/retiros/vaciar  (admin y cajero, igual que /cortes/cerrar)
    Retira a ahorros el saldo completo de todas las cuentas de transferencia
    no de sistema con saldo > 0. Body opcional: {descripcion?}."""
    data, error = _body_json_opcional()
    if error:
        return jsonify({"mensaje": error}), 400

    descripcion, error = _validar_descripcion_retiro(
        data.get("descripcion"), "Retiro a ahorros (cierre de corte)"
    )
    if error:
        return jsonify({"mensaje": error}), 400

    usuario_id = g.usuario["id"]

    try:
        resultado, error = vaciar_cuentas_transferencia(descripcion, usuario_id)
        if error:
            return jsonify({"mensaje": error}), _status_para_error(error)
        if resultado["cantidad"] == 0:
            return jsonify({
                "mensaje": "No hay saldo para retirar",
                **resultado,
            }), 200
        return jsonify({
            "mensaje": "Vaciado de cuentas registrado",
            **resultado,
        }), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al vaciar cuentas: {str(e)}"}), 500
