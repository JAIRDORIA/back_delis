from flask import request, jsonify
from services.combos_services import listado_combos, crear_combos

def get_combos():
    w = listado_combos()
    return jsonify(w)

def cntRegistrarCombo():
    # 1. Validar campos requeridos
    requeridos = ["nombre", "descripcion", "precio"]
    faltantes = [x for x in requeridos if x not in request.json]
    
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

    # 2. Validar que no estén vacíos y limpiar espacios
    nombre = str(request.json["nombre"]).strip()
    descripcion = str(request.json["descripcion"]).strip()
    precio = request.json["precio"]

    if not nombre or not descripcion:
        return jsonify({"mensaje": "El nombre y la descripción no pueden estar vacíos"}), 400

    # 3. Validar que el precio sea un número válido y positivo
    try:
        precio_num = float(precio)
        if precio_num <= 0:
            return jsonify({"mensaje": "El precio debe ser un número mayor a cero"}), 400
    except (ValueError, TypeError):
        return jsonify({"mensaje": "El precio debe ser un formato numérico válido"}), 400

    # 4. Llamar al servicio y capturar posibles errores (como nombre duplicado)
    resultado = crear_combos(nombre, descripcion, precio_num)
    
    # Si el servicio nos devolvió la tupla de error (ej: el 400 de 'existe_combo')
    if isinstance(resultado, tuple):
        return jsonify(resultado[0]), resultado[1]
    
    return jsonify({"mensaje": "Combo registrado con éxito", "datos": resultado}), 201