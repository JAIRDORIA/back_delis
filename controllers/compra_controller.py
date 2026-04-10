from flask import jsonify, request
from services.compra_services import listado_compra, registro_compra

def cntListadoCompra():
    try:
        datos = listado_compra()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntRegistroCompra():
    requeridos = ['proveedor_id', 'corte_id', 'usuario_id', 'fecha', 'total']
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"error": f"Faltan los siguientes campos: {faltantes}"}), 400

    proveedor_id = request.json['proveedor_id']
    corte_id     = request.json['corte_id']
    usuario_id   = request.json['usuario_id']
    fecha        = request.json['fecha']
    total        = request.json['total']
    descripcion  = request.json.get('descripcion', None)  # opcional

    c = registro_compra(proveedor_id, corte_id, usuario_id, fecha, total, descripcion)
    return jsonify(c), 201