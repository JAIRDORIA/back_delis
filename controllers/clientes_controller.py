from flask import request, jsonify
from services.clientes_services import listado_clientes

def get_clientes():
    data = listado_clientes()
    return jsonify(data)


