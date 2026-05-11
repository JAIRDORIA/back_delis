from flask import request, jsonify
from flask_jwt_extended import jwt_required
from services.combos_services import (
    listado_combos, crear_combos, existe_combo, 
    obtener_combo_id, actualizar_combos, eliminar_combos
)

@jwt_required()
def get_combos():
    """
    Listar combos paginados (RF24)
    ---
    tags: [Combos]
    security: [{ Bearer: [] }]
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: Lista de productos disponibles.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    # Se añade lógica de paginación al servicio
    w = listado_combos(page, per_page)
    return jsonify(w)

@jwt_required()
def get_combo_por_id(id):
    """
    Visualizar detalle de un combo
    ---
    tags: [Combos]
    security: [{ Bearer: [] }]
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    """
    res = obtener_combo_id(id)
    if not res:
        return jsonify({"mensaje": "Combo no encontrado"}), 404
    return jsonify(res)

@jwt_required()
def cntRegistrarCombo():
    """
    Registrar un nuevo producto/combo (RF21)
    ---
    tags: [Combos]
    security: [{ Bearer: [] }]
    """
    # 1. Validar campos requeridos
    requeridos = ["nombre", "descripcion", "precio"]
    if not request.json:
        return jsonify({"mensaje": "No se recibió información en formato JSON"}), 400
        
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

    # 2. Validar que no estén vacíos y limpiar espacios
    nombre = str(request.json["nombre"]).strip()
    descripcion = str(request.json["descripcion"]).strip()
    precio = request.json["precio"]

    if not nombre or not descripcion:
        return jsonify({"mensaje": "El nombre y la descripción no pueden estar vacíos"}), 400

    # 3. Validar que el precio sea un número válido y positivo (RF25)
    try:
        precio_num = float(precio)
        if precio_num <= 0:
            return jsonify({"mensaje": "El precio debe ser un número mayor a cero"}), 400
    except (ValueError, TypeError):
        return jsonify({"mensaje": "El precio debe ser un formato numérico válido"}), 400

    # 4. Llamar al servicio y capturar posibles errores (como nombre duplicado)
    resultado = crear_combos(nombre, descripcion, precio_num)
    
    if isinstance(resultado, tuple):
        return jsonify(resultado[0]), resultado[1]
    
    return jsonify({"mensaje": "Combo registrado con éxito", "datos": resultado}), 201

@jwt_required()
def cntActualizarCombo(id):
    """
    Editar un producto/combo (RF22)
    ---
    tags: [Combos]
    security: [{ Bearer: [] }]
    """
    if not obtener_combo_id(id):
        return jsonify({"mensaje": "Combo no encontrado"}), 404

    if not request.json:
        return jsonify({"mensaje": "No hay datos para actualizar"}), 400

    nombre = str(request.json.get("nombre", "")).strip()
    descripcion = str(request.json.get("descripcion", "")).strip()
    precio = request.json.get("precio")

    if not nombre or not descripcion or precio is None:
        return jsonify({"mensaje": "Nombre, descripción y precio son obligatorios"}), 400

    try:
        precio_num = float(precio)
        if precio_num <= 0:
            return jsonify({"mensaje": "Precio inválido"}), 400
    except:
        return jsonify({"mensaje": "Formato de precio incorrecto"}), 400

    # Validar que el nombre no esté en uso por otro combo
    if existe_combo(nombre, excluir_id=id):
        return jsonify({"mensaje": "Ese nombre de combo ya está en uso"}), 400

    resultado = actualizar_combos(id, nombre, descripcion, precio_num)
    return jsonify({"mensaje": "Combo actualizado con éxito", "datos": resultado}), 200

@jwt_required()
def cntEliminarCombo(id):
    """
    Eliminar combo - Borrado lógico (RF23)
    ---
    tags: [Combos]
    security: [{ Bearer: [] }]
    """
    if not obtener_combo_id(id):
        return jsonify({"mensaje": "Combo no existe"}), 404
        
    eliminar_combos(id)
    return jsonify({"mensaje": "Combo eliminado correctamente"}), 200