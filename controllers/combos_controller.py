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

    # 2. Validar que no estén vacíos (estilo .strip())
    vacios = []
    for campo in requeridos:
        # Convertimos a string por si el precio viene como número
        if str(request.json[campo]).strip() == "":
            vacios.append(campo)
            
    if vacios:
        return jsonify({"mensaje": f"los siguientes campos no pueden estar vacíos {vacios}"}), 400

    # 3. Extraer datos
    nombre      = request.json["nombre"]
    descripcion = request.json["descripcion"]
    precio      = request.json["precio"]

    # 4. Llamar al servicio
    datos = crear_combos(nombre, descripcion, precio)
    
    return jsonify({"mensaje": "Combo registrado", "datos": datos}), 201