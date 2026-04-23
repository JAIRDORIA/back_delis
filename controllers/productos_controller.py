from flask import jsonify , request
from  services.productos_services import listado_productos, registro, eliminar, existe_nombre,productos_mas_vendidos
import re

def cntListado():
    try:
        datos = listado_productos()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntRegistro():
    #validar en la peticion(body) atributos requeridos
    requeridos = ['nombre', 'descripcion', 'precio_venta', 'unidades_por_bandeja']

    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400
    
    #Validar que no existan campos vacios en los requeridos
    vacios = []
    for clave in request.json:
        if str(request.json[clave]).strip() == "":
            vacios.append(clave)

    if vacios:
        return jsonify({"mensaje": f"los siguientes campos no pueden estar vacios {vacios}"}), 400
    
    #validar que no esten vacios
    nombre        = request.json['nombre'] 
    descripcion   = request.json['descripcion']
    precio_venta  = request.json['precio_venta']
    unidades_por_bandeja = request.json['unidades_por_bandeja']

    #validar que el producto no exista
    if existe_nombre(nombre):
        return jsonify({"mensaje": "El nombre ya existe"}), 400

    if len(nombre) < 3 or len(nombre) > 150:
        return jsonify({"mensaje": "El nombre debe tener entre 3 y 150 caracteres"}), 400
    
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
        return jsonify({"mensaje": "El nombre solo puede contener letras"}), 400

    if len(descripcion) < 4 or len(descripcion) > 255:
        return jsonify({"mensaje": "La descripción debe tener entre 4 y 255 caracteres"}), 400
    
    try:
        precio_venta = float(precio_venta)
    except:
        return jsonify({"mensaje": "El precio debe ser numérico"}), 400

    if precio_venta <= 0:
        return jsonify({"mensaje": "El precio debe ser mayor a 0"}), 400

    try:
        unidades_por_bandeja = int(unidades_por_bandeja)
    except:
        return jsonify({"mensaje": "Las unidades deben ser un número entero"}), 400

    if unidades_por_bandeja <= 0:
        return jsonify({"mensaje": "Las unidades deben ser mayor a 0"}), 400

    p             = registro(nombre=nombre, descripcion=descripcion, precio_venta=precio_venta, unidades_por_bandeja=unidades_por_bandeja)
    return jsonify({"mensaje":"Producto registrado","datos":p}), 201

def cntEliminar(id):
    if not id:
        return jsonify({"mensaje": "El id es requerido"}), 400

    eliminado = eliminar(id)

    if not eliminado:
        return jsonify({"mensaje": "Producto no encontrado"}), 404

    return jsonify({"mensaje": "Producto desactivado correctamente"}), 200



def cntProductosMasVendidos():
    try:
        limite = request.args.get("limite", 5, type=int)
        if limite < 1 or limite > 20:
            return jsonify({"mensaje": "el limite debe ser entre 1 y 20"}), 400
        datos = productos_mas_vendidos(limite)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500