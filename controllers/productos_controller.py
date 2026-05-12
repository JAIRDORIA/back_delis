from flask import jsonify , request
from  services.productos_services import listado_productos, registro, eliminar, existe_nombre,productos_mas_vendidos, actualizar, obtener_producto, existe_nombre_otro  
import re

def cntListado():
    try:
        pagina = int(request.args.get('pagina', 1))
        limite = int(request.args.get('limite', 20))

        if pagina < 1 or limite < 1:
            return jsonify({"mensaje": "pagina y limite deben ser mayores a 0"}), 400

        datos = listado_productos(pagina=pagina, limite=limite)
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
    
    if not str(id).isdigit(): 
        return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    eliminado = eliminar(id)

    if not eliminado:
        return jsonify({"mensaje": "Producto no encontrado"}), 404

    return jsonify({"mensaje": "Producto desactivado correctamente"}), 200

def cntActualizar(id):
    if not request.json:
        return jsonify({"mensaje": "Debe enviar datos"}), 400

    nombre = request.json.get('nombre')
    descripcion = request.json.get('descripcion')
    precio_venta = request.json.get('precio_venta')
    unidades_por_bandeja = request.json.get('unidades_por_bandeja')

    if not any([nombre, descripcion, precio_venta, unidades_por_bandeja]):
        return jsonify({"mensaje": "Debe enviar al menos un campo"}), 400

    if nombre:
        if len(nombre) < 3 or len(nombre) > 150:
            return jsonify({"mensaje": "El nombre debe tener entre 3 y 150 caracteres"}), 400

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
            return jsonify({"mensaje": "El nombre solo puede contener letras"}), 400

        if existe_nombre_otro(nombre, id):
            return jsonify({"mensaje": "El nombre ya existe"}), 400

    if descripcion:
        if len(descripcion) < 4 or len(descripcion) > 255:
            return jsonify({"mensaje": "La descripción debe tener entre 4 y 255 caracteres"}), 400
    if precio_venta is not None:
     try:
        precio_venta = float(precio_venta)
     except:
        return jsonify({"mensaje": "El precio debe ser numérico"}), 400
    if precio_venta <= 0:
        return jsonify({"mensaje": "El precio debe ser mayor a 0"}), 400

    if unidades_por_bandeja is not None:
     try:
        unidades_por_bandeja = int(unidades_por_bandeja)
     except:
        return jsonify({"mensaje": "Las unidades deben ser un número entero"}), 400
    if unidades_por_bandeja <= 0:
        return jsonify({"mensaje": "Las unidades deben ser mayor a 0"}), 400
    
    producto_actual = obtener_producto(id)
    if not producto_actual:
        return jsonify({"mensaje": "Producto no encontrado"}), 404

    cambios = []

    if nombre is not None and nombre != producto_actual["nombre"]:
        cambios.append("nombre")

    if descripcion is not None and descripcion != producto_actual["descripcion"]:
        cambios.append("descripcion")

    if precio_venta is not None and precio_venta != producto_actual["precio_venta"]:
        cambios.append("precio_venta")

    if unidades_por_bandeja is not None and unidades_por_bandeja != producto_actual["unidades_por_bandeja"]:
        cambios.append("unidades_por_bandeja")

    if not cambios:
        return jsonify({"mensaje": "No hay cambios para actualizar"}), 400
    
    actualizado = actualizar(id, nombre, descripcion, precio_venta, unidades_por_bandeja)

    if not actualizado:
        return jsonify({"mensaje": "Producto no encontrado"}), 404

    return jsonify({"mensaje": "Producto actualizado correctamente"}), 200


def obtenerProducto(id):
    if not id:
        return jsonify({"mensaje": "El id es requerido"}), 400

    producto = obtener_producto(id)

    if not producto:
        return jsonify({"mensaje": "Producto no encontrado"}), 404

    return jsonify(producto), 200




def cntProductosMasVendidos():
    try:
        limite = request.args.get("limite", 5, type=int)
        if limite < 1 or limite > 20:
            return jsonify({"mensaje": "el limite debe ser entre 1 y 20"}), 400
        datos = productos_mas_vendidos(limite)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500