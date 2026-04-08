import re
from flask import request, jsonify
from services.clientes_services import listado_clientes, crear_clientes, existe_email

def cntRegistrar():
    # 1. Validar campos requeridos
    requeridos = ["nombre", "telefono", "direccion", "email"]
    faltantes = [x for x in requeridos if x not in request.json]
    
    
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

    # 2. Extraer y limpiar datos (Sanitización)
    nombre = request.json["nombre"].strip()
    telefono = request.json["telefono"].strip()
    direccion = request.json["direccion"].strip()
    email = request.json["email"].strip()

    # 3. Validar que no estén vacíos tras el strip
    if not nombre or not telefono or not direccion or not email:
        return jsonify({"mensaje": "Todos los campos son obligatorios y no pueden estar vacíos"}), 400

    # 4. Validar formato de Email (Regex)
    # Explicación: Verifica que tenga algo@algo.com
    regex_email = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.match(regex_email, email.lower()):
        return jsonify({"mensaje": "El formato del correo electrónico no es válido"}), 400

    # 5. Validar si el email ya existe en la base de datos (Unicidad)
    if existe_email(email):
        return jsonify({"mensaje": "Este correo ya se encuentra registrado"}), 400
# 6. Llamar al servicio
    resultado = crear_clientes(nombre, telefono, direccion, email)
    
    # Validamos si el servicio nos devolvió una tupla de error (ej: el 400 que configuramos)
    if isinstance(resultado, tuple):
        return jsonify(resultado[0]), resultado[1]
    
    return jsonify({"mensaje": "Cliente registrado con éxito", "datos": resultado}), 201