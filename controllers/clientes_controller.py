import re
from flask import request, jsonify
from services.clientes_services import listado_clientes, crear_clientes, existe_email

def get_clientes():
    # Eliminamos el import interno ya que está arriba de forma global
    w = listado_clientes()
    return jsonify(w)

def cntRegistrar():
    # 1. Validar campos requeridos
    requeridos = ["nombre", "telefono", "direccion", "email"]
    # Verificamos si el body de la petición tiene los campos
    if not request.json:
        return jsonify({"mensaje": "No se recibió información en formato JSON"}), 400
        
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

    # 2. Extraer y limpiar datos (Sanitización)
    nombre = str(request.json["nombre"]).strip()
    telefono = str(request.json["telefono"]).strip()
    direccion = str(request.json["direccion"]).strip()
    email = str(request.json["email"]).strip()

    # 3. Validar que no estén vacíos tras el strip
    if not nombre or not telefono or not direccion or not email:
        return jsonify({"mensaje": "Todos los campos son obligatorios y no pueden estar vacíos"}), 400

    # 4. Validar formato de Email (Regex)
    regex_email = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.match(regex_email, email.lower()):
        return jsonify({"mensaje": "El formato del correo electrónico no es válido"}), 400

    # 5. Validar si el email ya existe en la base de datos (Unicidad)
    if existe_email(email):
        return jsonify({"mensaje": "Este correo ya se encuentra registrado"}), 400

    # 6. Llamar al servicio
    resultado = crear_clientes(nombre, telefono, direccion, email)
    
    # Validamos si el servicio nos devolvió una tupla de error (ej: el 400 del servicio)
    if isinstance(resultado, tuple):
        return jsonify(resultado[0]), resultado[1]
    
    return jsonify({"mensaje": "Cliente registrado con éxito", "datos": resultado}), 201