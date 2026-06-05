from flask import jsonify, request
from services.compra_services import (
    listado_compra, obtener_compra, registro_compra,
    actualizar_compra, eliminar_compra
)
from services.cortes_services import obtener_corte_abierto, obtener_corte


def cntListadoCompra():
    try:
        pagina   = request.args.get("pagina", 1, type=int)
        limite   = request.args.get("limite", 20, type=int)
        corte_id = request.args.get("corte_id", None, type=int)

        if pagina < 1:
            return jsonify({"mensaje": "la pagina debe ser mayor a 0"}), 400
        if limite < 1 or limite > 100:
            return jsonify({"mensaje": "el limite debe ser entre 1 y 100"}), 400

        if corte_id is None:
            corte_abierto = obtener_corte_abierto()
            if not corte_abierto:
                return jsonify({"mensaje": "no hay corte abierto"}), 404
            corte_id = corte_abierto["id"]
        else:
            corte_db = obtener_corte(corte_id)
            if not corte_db:
                return jsonify({"mensaje": f"el corte con id {corte_id} no existe"}), 404

        datos = listado_compra(pagina, limite, corte_id)
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

    requeridos = ['proveedor_id', 'usuario_id', 'fecha', 'total']
    faltantes  = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"Faltan los siguientes campos: {faltantes}"}), 400

    proveedor_id = request.json['proveedor_id']
    usuario_id   = request.json['usuario_id']
    fecha        = request.json['fecha']
    total        = request.json['total']
    descripcion  = request.json.get('descripcion', None)

    # corte_id automático desde el corte abierto
    corte_abierto = obtener_corte_abierto()
    if not corte_abierto:
        return jsonify({"error": "no hay corte abierto para registrar la compra"}), 400
    corte_id = corte_abierto["id"]

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

    requeridos = ['proveedor_id', 'usuario_id', 'fecha', 'total']
    faltantes  = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"error": f"Faltan los siguientes campos: {faltantes}"}), 400

    proveedor_id = request.json['proveedor_id']
    usuario_id   = request.json['usuario_id']
    fecha        = request.json['fecha']
    total        = request.json['total']
    descripcion  = request.json.get('descripcion', None)

    corte_abierto = obtener_corte_abierto()
    if not corte_abierto:
        return jsonify({"error": "no hay corte abierto"}), 400
    corte_id = corte_abierto["id"]

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