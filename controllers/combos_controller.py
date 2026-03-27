from flask import request, jsonify
from services.combos_services import listado_combos, obtener_combo, crear_combos, actualizar_combos

def get_combos():
    data = listado_combos()
    return jsonify(data)

def get_combo(id):
    data = obtener_combo(id)
    if data:
        return jsonify(data)
    return jsonify({"error": "Combo no encontrado"}), 404

def create_combo():
    data = request.json
    res = crear_combos(data)
    return jsonify(res)

def update_combo(id):
    data = request.json
    res = actualizar_combos(id, data)
    return jsonify(res)