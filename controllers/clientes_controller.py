from flask import request, jsonify
from services.clientes_services import *

def get_clientes():
    data = listado_clientes()
    return jsonify(data)


def get_cliente(id):
    data = obtener_clientes(id)
    if data:
        return jsonify(data)
    return jsonify({"error": "Cliente no encontrado"}), 404


def create_cliente():
    data = request.json
    res = crear_clientes(data)
    return jsonify(res)


def update_cliente(id):
    data = request.json
    res = actualizar_clientes(id, data)
    return jsonify(res)


def delete_cliente(id):
    res = eliminar_clientes(id)
    return jsonify(res)