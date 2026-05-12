from flask import jsonify, request
from services.compra_services import (
    listado_compras, registrar_compra,
    actualizar_compra, eliminar_compra, existe_compra
)

def cntListadoCompra():
    try:
        datos = listado_compras()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntRegistroCompra():
    requeridos = ['proveedor_id', 'corte_id', 'usuario_id', 'fecha', 'total', 'descripcion']
    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"Faltan los siguientes campos: {faltantes}"}), 400

    proveedor_id = request.json['proveedor_id']
    corte_id     = request.json['corte_id']
    usuario_id   = request.json['usuario_id']
    fecha        = request.json['fecha']
    total        = request.json['total']
    descripcion  = request.json['descripcion'].strip()

    if total <= 0:
        return jsonify({"mensaje": "El total debe ser mayor a 0"}), 400

    try:
        c = registrar_compra(proveedor_id, corte_id, usuario_id, fecha, total, descripcion)
        return jsonify({"mensaje": "Compra registrada", "datos": c}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntActualizarCompra(id):
    if not str(id).isdigit():
        return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    requeridos = ['proveedor_id', 'corte_id', 'usuario_id', 'fecha', 'total', 'descripcion']
    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"Faltan los siguientes campos: {faltantes}"}), 400

    proveedor_id = request.json['proveedor_id']
    corte_id     = request.json['corte_id']
    usuario_id   = request.json['usuario_id']
    fecha        = request.json['fecha']
    total        = request.json['total']
    descripcion  = request.json['descripcion'].strip()

    if total <= 0:
        return jsonify({"mensaje": "El total debe ser mayor a 0"}), 400

    if not existe_compra(id):
        return jsonify({"mensaje": "Compra no encontrada"}), 404

    actualizado = actualizar_compra(id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion)
    if not actualizado:
        return jsonify({"mensaje": "No se pudo actualizar"}), 400
    return jsonify({"mensaje": "Compra actualizada correctamente"}), 200

def cntEliminarCompra(id):
    if not str(id).isdigit():
        return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    if not existe_compra(id):
        return jsonify({"mensaje": "Compra no encontrada"}), 404

    eliminado = eliminar_compra(id)
    if not eliminado:
        return jsonify({"mensaje": "No se pudo eliminar"}), 400
    return jsonify({"mensaje": "Compra eliminada correctamente"}), 200