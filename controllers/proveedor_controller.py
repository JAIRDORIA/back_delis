from flask import jsonify, request
from services.proveedor_services import (
    listado_proveedores, registrar_proveedor,
    actualizar_proveedor, eliminar_proveedor, existe_proveedor
)

def cntListadoProveedores():
    try:
        datos = listado_proveedores()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntRegistroProveedor():
    requeridos = ['nombre', 'contacto', 'direccion', 'compra']
    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"Faltan los siguientes campos: {faltantes}"}), 400

    vacios = [c for c in requeridos if str(request.json[c]).strip() == ""]
    if vacios:
        return jsonify({"mensaje": f"Los siguientes campos no pueden estar vacíos: {vacios}"}), 400

    nombre    = request.json['nombre'].strip()
    contacto  = request.json['contacto'].strip()
    direccion = request.json['direccion'].strip()
    compra    = request.json['compra']

    if len(nombre) < 3 or len(nombre) > 100:
        return jsonify({"mensaje": "El nombre debe tener entre 3 y 100 caracteres"}), 400

    try:
        p = registrar_proveedor(nombre, contacto, direccion, compra)
        return jsonify({"mensaje": "Proveedor registrado", "datos": p}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntActualizarProveedor(id):
    if not str(id).isdigit():
        return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    requeridos = ['nombre', 'contacto', 'direccion', 'compra']
    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"Faltan los siguientes campos: {faltantes}"}), 400

    nombre    = request.json['nombre'].strip()
    contacto  = request.json['contacto'].strip()
    direccion = request.json['direccion'].strip()
    compra    = request.json['compra']

    if len(nombre) < 3 or len(nombre) > 100:
        return jsonify({"mensaje": "El nombre debe tener entre 3 y 100 caracteres"}), 400

    if not existe_proveedor(id):
        return jsonify({"mensaje": "Proveedor no encontrado"}), 404

    actualizado = actualizar_proveedor(id, nombre, contacto, direccion, compra)
    if not actualizado:
        return jsonify({"mensaje": "No se pudo actualizar"}), 400
    return jsonify({"mensaje": "Proveedor actualizado correctamente"}), 200

def cntEliminarProveedor(id):
    if not str(id).isdigit():
        return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    if not existe_proveedor(id):
        return jsonify({"mensaje": "Proveedor no encontrado"}), 404

    eliminado = eliminar_proveedor(id)
    if not eliminado:
        return jsonify({"mensaje": "No se pudo eliminar"}), 400
    return jsonify({"mensaje": "Proveedor eliminado correctamente"}), 200