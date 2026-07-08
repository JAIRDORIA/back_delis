from flask import request, jsonify
from flask_jwt_extended import jwt_required
from services.combos_services import (
    listado_combos, crear_combo, existe_combo, 
    obtener_combo_id, actualizar_combos, eliminar_combos,obtener_combo_id
)
from utils.decorators import token_requerido
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

#@jwt_required()
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

#@jwt_required()
def cntRegistrarCombo():
    # 1. validar que venga JSON
    if not request.json:
        return jsonify({"mensaje": "No se recibio informacion en formato JSON"}), 400

    # 2. validar campos requeridos
    requeridos = ["nombre", "precio_frito","precio_congelado", "productos"]
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

    # 3. validar campos vacios
    nombre      = str(request.json["nombre"]).strip()
    
    precio_frito      = request.json["precio_frito"]
    precio_congelado = request.json["precio_congelado"]
    productos   = request.json["productos"]

    if not nombre:
        return jsonify({"mensaje": "el nombre no puede estar vacio"}), 400
   

    # 4. validar precio
    try:
        precio_num = float(precio_frito)
        precio_con = float(precio_congelado)
        if precio_num <= 0 or precio_con <= 0:
            return jsonify({"mensaje": "el precio debe ser mayor a 0"}), 400
    except (ValueError, TypeError):
        return jsonify({"mensaje": "el precio debe ser un numero valido"}), 400

    # 5. validar que productos no este vacio
    if not productos or len(productos) == 0:
        return jsonify({"mensaje": "el combo debe tener al menos un producto"}), 400

    # 6. validar cada producto del detalle
    for item in productos:
        if "producto_id" not in item:
            return jsonify({"mensaje": "cada producto debe tener producto_id"}), 400
        if "cantidad_unidades" not in item:
            return jsonify({"mensaje": "cada producto debe tener cantidad"}), 400
        if item["cantidad_unidades"] <= 0:
            return jsonify({"mensaje": "la cantidad debe ser mayor a 0"}), 400

    # 7. registrar el combo
    resultado = crear_combo(nombre, precio_frito,precio_congelado, productos)

    if isinstance(resultado, tuple):
        return jsonify(resultado[0]), resultado[1]

    return jsonify({"mensaje": "combo registrado exitosamente", "datos": resultado}), 201

#@jwt_required()
def cntActualizarCombos(id):
    # Verificar que el combo existe
    if not obtener_combo_id(id):
        return jsonify({"mensaje": "Combo no encontrado"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"mensaje": "No hay datos para actualizar"}), 400

    nombre = data.get("nombre", "").strip()
    descripcion = data.get("descripcion", "").strip()
    precio_frito = data.get("precio_frito", 0)
    precio_congelado = data.get("precio_congelado", 0)
    productos = data.get("productos", None)  # lista de {producto_id, cantidad_unidades}

    if not nombre:
        return jsonify({"mensaje": "El nombre es obligatorio"}), 400

    resultado = actualizar_combos(id, nombre, descripcion, precio_frito, precio_congelado, productos)
    
    if isinstance(resultado, dict) and "error" in resultado:
        return jsonify({"mensaje": resultado["error"]}), 400

    return jsonify({"mensaje": "Combo actualizado exitosamente", "datos": resultado}), 200

#@jwt_required()
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