from flask import jsonify, request
from services.compra_services import (
    listado_compra,
    obtener_compra,
    registro_compra,
    actualizar_compra,
    eliminar_compra
)


def cntListadoCompra():
    try:
        datos = listado_compra()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntObtenerCompra(id):
    try:
        dato, error = obtener_compra(id)
        if error:
            return jsonify({"error": error}), 404
        return jsonify(dato), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntRegistroCompra():
    if not request.is_json:
        return jsonify({"error": "El cuerpo debe ser JSON"}), 400

    requeridos = ['proveedor_id', 'corte_id', 'usuario_id', 'fecha', 'total']
    faltantes  = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"error": f"Faltan los siguientes campos: {faltantes}"}), 400

    proveedor_id = request.json['proveedor_id']
    corte_id     = request.json['corte_id']
    usuario_id   = request.json['usuario_id']
    fecha        = request.json['fecha']
    total        = request.json['total']
    descripcion  = request.json.get('descripcion', None)

    # ── Validaciones de tipo ───────────────────────────────────────
    if not isinstance(proveedor_id, int) or proveedor_id <= 0:
        return jsonify({"error": "proveedor_id debe ser un entero positivo"}), 400
    if not isinstance(corte_id, int) or corte_id <= 0:
        return jsonify({"error": "corte_id debe ser un entero positivo"}), 400
    if not isinstance(usuario_id, int) or usuario_id <= 0:
        return jsonify({"error": "usuario_id debe ser un entero positivo"}), 400
    try:
        total = float(total)
    except (TypeError, ValueError):
        return jsonify({"error": "El total debe ser un número"}), 400

    try:
        dato, error = registro_compra(proveedor_id, corte_id, usuario_id, fecha, total, descripcion)
        if error:
            return jsonify({"error": error}), 409
        return jsonify(dato), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntActualizarCompra(id):
    if not request.is_json:
        return jsonify({"error": "El cuerpo debe ser JSON"}), 400

    requeridos = ['proveedor_id', 'corte_id', 'usuario_id', 'fecha', 'total']
    faltantes  = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"error": f"Faltan los siguientes campos: {faltantes}"}), 400

    proveedor_id = request.json['proveedor_id']
    corte_id     = request.json['corte_id']
    usuario_id   = request.json['usuario_id']
    fecha        = request.json['fecha']
    total        = request.json['total']
    descripcion  = request.json.get('descripcion', None)

    if not isinstance(proveedor_id, int) or proveedor_id <= 0:
        return jsonify({"error": "proveedor_id debe ser un entero positivo"}), 400
    if not isinstance(corte_id, int) or corte_id <= 0:
        return jsonify({"error": "corte_id debe ser un entero positivo"}), 400
    if not isinstance(usuario_id, int) or usuario_id <= 0:
        return jsonify({"error": "usuario_id debe ser un entero positivo"}), 400
    try:
        total = float(total)
    except (TypeError, ValueError):
        return jsonify({"error": "El total debe ser un número"}), 400

    try:
        dato, error = actualizar_compra(id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion)
        if error:
            status = 404 if "no encontrada" in error else 409
            return jsonify({"error": error}), status
        return jsonify(dato), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntEliminarCompra(id):
    try:
        ok, error = eliminar_compra(id)
        if error:
            return jsonify({"error": error}), 404
        return jsonify({"mensaje": f"Compra {id} eliminada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500