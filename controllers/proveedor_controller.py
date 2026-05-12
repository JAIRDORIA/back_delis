from flask import jsonify, request
from services.proveedor_services import (
    listado_proveedores,
    obtener_proveedor,
    registro_proveedor,
    actualizar_proveedor,
    eliminar_proveedor
)


def cntListadoProveedores():
    try:
        datos = listado_proveedores()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntObtenerProveedor(id):
    try:
        dato, error = obtener_proveedor(id)
        if error:
            return jsonify({"error": error}), 404
        return jsonify(dato), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntRegistroProveedor():
    # ── Validar que venga JSON ──────────────────────────────────────
    if not request.is_json:
        return jsonify({"error": "El cuerpo debe ser JSON"}), 400

    requeridos = ['nombre', 'telefono', 'direccion', 'email']
    faltantes  = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"error": f"Faltan los siguientes campos: {faltantes}"}), 400

    nombre    = request.json['nombre'].strip()
    telefono  = request.json['telefono'].strip()
    direccion = request.json['direccion'].strip()
    email     = request.json['email'].strip()

    # ── Validaciones de formato ────────────────────────────────────
    if not nombre:
        return jsonify({"error": "El nombre no puede estar vacío"}), 400
    if not email or '@' not in email:
        return jsonify({"error": "El email no tiene un formato válido"}), 400

    try:
        dato, error = registro_proveedor(None, nombre, telefono, direccion, email)
        if error:
            return jsonify({"error": error}), 409
        return jsonify(dato), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntActualizarProveedor(id):
    if not request.is_json:
        return jsonify({"error": "El cuerpo debe ser JSON"}), 400

    requeridos = ['nombre', 'telefono', 'direccion', 'email', 'activo']
    faltantes  = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"error": f"Faltan los siguientes campos: {faltantes}"}), 400

    nombre    = request.json['nombre'].strip()
    telefono  = request.json['telefono'].strip()
    direccion = request.json['direccion'].strip()
    email     = request.json['email'].strip()
    activo    = request.json['activo']

    if not nombre:
        return jsonify({"error": "El nombre no puede estar vacío"}), 400
    if not email or '@' not in email:
        return jsonify({"error": "El email no tiene un formato válido"}), 400
    if activo not in [0, 1]:
        return jsonify({"error": "El campo 'activo' debe ser 0 o 1"}), 400

    try:
        dato, error = actualizar_proveedor(id, nombre, telefono, direccion, email, activo)
        if error:
            status = 404 if "no encontrado" in error else 409
            return jsonify({"error": error}), status
        return jsonify(dato), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntEliminarProveedor(id):
    try:
        ok, error = eliminar_proveedor(id)
        if error:
            return jsonify({"error": error}), 404
        return jsonify({"mensaje": f"Proveedor {id} eliminado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500