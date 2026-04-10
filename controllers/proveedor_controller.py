from flask import jsonify, request
from services.proveedor_services import (
    listado_proveedores,
    registro_proveedor
)

def cntListadoProveedores():
    try:
        datos = listado_proveedores()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntRegistroProveedor():
    requeridos = ['nombre', 'telefono', 'direccion', 'email']
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"error": f"Faltan los siguientes campos: {faltantes}"}), 400

    nombre   = request.json['nombre']
    telefono = request.json['telefono']
    direccion= request.json['direccion']
    email    = request.json['email']

    p = registro_proveedor(None, nombre, telefono, direccion, email)
    return jsonify(p), 201