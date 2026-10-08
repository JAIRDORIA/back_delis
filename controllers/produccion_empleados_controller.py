from flask import g, jsonify, request

from services.produccion_empleados_services import (
    listado_productos_activos,
    registrar_produccion_empleado,
    listado_pendientes,
    aceptar_produccion_empleado,
    rechazar_produccion_empleado,
    listado_registros,
)


# ─────────────────────────────────────────────
#  HELPERS DE VALIDACIÓN
# ─────────────────────────────────────────────

TOPE_BANDEJAS = 9999
TOPE_UNIDADES_SUELTAS = 99999


def _parse_entero(valor):
    """Solo acepta int de JSON o string numérico; devuelve (entero, error)."""
    if isinstance(valor, bool):
        return None, "debe ser un número entero"
    if isinstance(valor, int):
        return valor, None
    if isinstance(valor, str):
        try:
            return int(valor.strip()), None
        except ValueError:
            return None, "debe ser un número entero"
    return None, "debe ser un número entero"


def _validar_cantidades_finales(data):
    """
    Body opcional del aceptar: si no vienen bandejas/unidades_sueltas devuelve
    (None, None, None) para que el service use lo registrado por el empleado.
    Si viene alguno, los dos son obligatorios.
    """
    tiene_bandejas = "bandejas" in data
    tiene_sueltas = "unidades_sueltas" in data

    if not tiene_bandejas and not tiene_sueltas:
        return None, None, None
    if not (tiene_bandejas and tiene_sueltas):
        return None, None, "Debe enviar 'bandejas' y 'unidades_sueltas' juntos"

    bandejas, error = _parse_entero(data["bandejas"])
    if error:
        return None, None, f"El campo bandejas {error}"
    unidades_sueltas, error = _parse_entero(data["unidades_sueltas"])
    if error:
        return None, None, f"El campo unidades_sueltas {error}"

    if bandejas < 0 or unidades_sueltas < 0:
        return None, None, "Las cantidades finales deben ser mayores o iguales a 0"
    if bandejas > TOPE_BANDEJAS:
        return None, None, f"El campo bandejas no puede superar {TOPE_BANDEJAS}"
    if unidades_sueltas > TOPE_UNIDADES_SUELTAS:
        return None, None, f"El campo unidades_sueltas no puede superar {TOPE_UNIDADES_SUELTAS}"
    if bandejas == 0 and unidades_sueltas == 0:
        return None, None, (
            "No puede dejar las dos cantidades en 0; "
            "si no hubo producción, rechace el registro"
        )

    return bandejas, unidades_sueltas, None


def _body_opcional():
    """Body JSON opcional: devuelve (dict, error). Sin body -> {}."""
    data = request.get_json(silent=True)
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "El cuerpo debe ser JSON"
    return data, None



# ─────────────────────────────────────────────
#  ENDPOINTS
# ─────────────────────────────────────────────

def cntListadoProductos():
    """GET /produccion-empleados/productos  (produccion, admin)"""
    try:
        return jsonify(listado_productos_activos()), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al listar productos: {str(e)}"}), 500


def cntRegistro():
    """POST /produccion-empleados/  (produccion, admin)"""
    if not request.is_json:
        return jsonify({"mensaje": "El cuerpo debe ser JSON"}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"mensaje": "El cuerpo debe ser JSON"}), 400

    requeridos = ["empleado_id", "producto_id", "bandejas", "unidades_sueltas"]
    faltantes = [campo for campo in requeridos if campo not in data]
    if faltantes:
        return jsonify({"mensaje": f"Faltan los siguientes campos: {faltantes}"}), 400

    valores = {}
    for campo in requeridos:
        numero, error = _parse_entero(data[campo])
        if error:
            return jsonify({"mensaje": f"El campo {campo} {error}"}), 400
        if numero < 0:
            return jsonify({"mensaje": f"El campo {campo} debe ser mayor o igual a 0"}), 400
        valores[campo] = numero

    if valores["empleado_id"] == 0:
        return jsonify({"mensaje": "El campo empleado_id debe ser mayor a 0"}), 400
    if valores["producto_id"] == 0:
        return jsonify({"mensaje": "El campo producto_id debe ser mayor a 0"}), 400

    if valores["bandejas"] == 0 and valores["unidades_sueltas"] == 0:
        return jsonify({"mensaje": "Debe registrar al menos una bandeja o una unidad suelta"}), 400

    if valores["bandejas"] > TOPE_BANDEJAS:
        return jsonify({"mensaje": f"El campo bandejas no puede superar {TOPE_BANDEJAS}"}), 400
    if valores["unidades_sueltas"] > TOPE_UNIDADES_SUELTAS:
        return jsonify({"mensaje": f"El campo unidades_sueltas no puede superar {TOPE_UNIDADES_SUELTAS}"}), 400

    try:
        dato, error, status = registrar_produccion_empleado(
            empleado_id      = valores["empleado_id"],
            producto_id      = valores["producto_id"],
            bandejas         = valores["bandejas"],
            unidades_sueltas = valores["unidades_sueltas"],
            usuario_id       = g.usuario["id"],
        )
        if error:
            return jsonify({"mensaje": error}), status

        return jsonify(dato), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar producción: {str(e)}"}), 500


def cntListadoPendientes():
    """GET /produccion-empleados/pendientes  (solo admin)"""
    try:
        return jsonify(listado_pendientes()), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al listar pendientes: {str(e)}"}), 500


def cntAceptar(id):
    """PUT /produccion-empleados/<id>/aceptar  (solo admin)  body opcional {bandejas, unidades_sueltas}"""
    if id <= 0:
        return jsonify({"mensaje": "El id debe ser mayor a 0"}), 400

    data, error = _body_opcional()
    if error:
        return jsonify({"mensaje": error}), 400

    bandejas, unidades_sueltas, error = _validar_cantidades_finales(data)
    if error:
        return jsonify({"mensaje": error}), 400

    try:
        dato, error, status = aceptar_produccion_empleado(
            id               = id,
            bandejas         = bandejas,
            unidades_sueltas = unidades_sueltas,
            usuario_id       = g.usuario["id"],
        )
        if error:
            return jsonify({"mensaje": error}), status

        return jsonify(dato), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al aceptar la producción: {str(e)}"}), 500


def cntRechazar(id):
    """PUT /produccion-empleados/<id>/rechazar  (solo admin)  body opcional {motivo}"""
    if id <= 0:
        return jsonify({"mensaje": "El id debe ser mayor a 0"}), 400

    data, error = _body_opcional()
    if error:
        return jsonify({"mensaje": error}), 400

    motivo = data.get("motivo")
    if motivo is not None:
        if not isinstance(motivo, str):
            return jsonify({"mensaje": "El motivo debe ser texto"}), 400
        motivo = motivo.strip()
        if len(motivo) > 255:
            return jsonify({"mensaje": "El motivo no puede exceder 255 caracteres"}), 400
        if motivo == "":
            motivo = None

    try:
        dato, error, status = rechazar_produccion_empleado(
            id         = id,
            motivo     = motivo,
            usuario_id = g.usuario["id"],
        )
        if error:
            return jsonify({"mensaje": error}), status

        return jsonify(dato), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al rechazar la producción: {str(e)}"}), 500


def cntListadoRegistros():
    """GET /produccion-empleados/registros  (produccion, admin)"""
    try:
        return jsonify(listado_registros()), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al listar registros: {str(e)}"}), 500
