from flask import jsonify, request
from services.empleados_services import (
    listado_empleados,
    listado_empleados_activos,
    registro_empleado,
    actualizar_empleado,
)


# ─────────────────────────────────────────────
#  HELPERS DE VALIDACIÓN
# ─────────────────────────────────────────────

def _validar_nombre(valor):
    if not isinstance(valor, str):
        return None, "El nombre debe ser texto"
    nombre = valor.strip()
    if nombre == "":
        return None, "El nombre no puede estar vacío"
    if len(nombre) > 100:
        return None, "El nombre no puede exceder 100 caracteres"
    return nombre, None


def _validar_activo(valor):
    if isinstance(valor, bool):
        return int(valor), None
    if isinstance(valor, int) and valor in (0, 1):
        return valor, None
    if isinstance(valor, str) and valor.strip() in ("0", "1"):
        return int(valor.strip()), None
    return None, "El campo activo debe ser 0 o 1"


def _status_para_error(error):
    low = error.lower()
    if "no encontrado" in low:
        return 404
    if "ya existe" in low or "duplicado" in low:
        return 409
    return 400


# ─────────────────────────────────────────────
#  ENDPOINTS
# ─────────────────────────────────────────────

def cntListado():
    """GET /empleados/  (admin)  Filtro opcional ?activo=0|1"""
    try:
        activo_raw = request.args.get("activo")
        activo = None
        if activo_raw is not None:
            if activo_raw not in ("0", "1"):
                return jsonify({"mensaje": "El filtro activo debe ser 0 o 1"}), 400
            activo = int(activo_raw)

        datos = listado_empleados(activo=activo)
        return jsonify({"datos": datos, "total": len(datos)}), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al listar empleados: {str(e)}"}), 500


def cntListadoActivos():
    """GET /empleados/activos  (produccion, admin)  -> [{id, nombre}]"""
    try:
        return jsonify(listado_empleados_activos()), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al listar empleados activos: {str(e)}"}), 500


def cntRegistro():
    """POST /empleados/  (admin)  body {nombre}"""
    if not request.is_json:
        return jsonify({"mensaje": "El cuerpo debe ser JSON"}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"mensaje": "El cuerpo debe ser JSON"}), 400

    if "nombre" not in data:
        return jsonify({"mensaje": "Faltan los siguientes campos: ['nombre']"}), 400

    nombre, error = _validar_nombre(data.get("nombre"))
    if error:
        return jsonify({"mensaje": error}), 400

    try:
        dato, error = registro_empleado(nombre)
        if error:
            return jsonify({"mensaje": error}), _status_para_error(error)

        return jsonify({"mensaje": "Empleado registrado", "datos": dato}), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar empleado: {str(e)}"}), 500


def cntActualizar(id):
    """PUT /empleados/<id>  (admin)  body {nombre} y/o {activo}"""
    if id <= 0:
        return jsonify({"mensaje": "El id debe ser mayor a 0"}), 400

    if not request.is_json:
        return jsonify({"mensaje": "El cuerpo debe ser JSON"}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"mensaje": "El cuerpo debe ser JSON"}), 400

    tiene_nombre = "nombre" in data
    tiene_activo = "activo" in data

    if not tiene_nombre and not tiene_activo:
        return jsonify({"mensaje": "Debe enviar al menos 'nombre' o 'activo'"}), 400

    nombre = None
    if tiene_nombre:
        nombre, error = _validar_nombre(data.get("nombre"))
        if error:
            return jsonify({"mensaje": error}), 400

    activo = None
    if tiene_activo:
        activo, error = _validar_activo(data.get("activo"))
        if error:
            return jsonify({"mensaje": error}), 400

    try:
        dato, error = actualizar_empleado(id, nombre=nombre, activo=activo)
        if error:
            return jsonify({"mensaje": error}), _status_para_error(error)

        return jsonify({"mensaje": "Empleado actualizado", "datos": dato}), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al actualizar empleado: {str(e)}"}), 500
