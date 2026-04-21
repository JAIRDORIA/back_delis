from flask import jsonify , request
from  services.usuarios_servicies import listado_usuarios, registro, existe_username, eliminar
import re


def cntListado():
    try:
        datos = listado_usuarios()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 

def cntRegistro():
    #validar en la peticion(body) atributos requeridos
    requeridos = ['nombre', 'username', 'password_hash', 'rol']

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
    username      = request.json['username']
    password = request.json['password_hash']
    password_hash = generate_password_hash(password)
    rol           = request.json['rol']
    
    if existe_username(username):
        return jsonify({"mensaje": "El username ya existe"}), 400

    #validar campos 
    if len(nombre) < 3 or len(nombre) > 100:
        return jsonify({"mensaje": "El nombre debe tener entre 3 y 100 caracteres"}), 400
    
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
       return jsonify({"mensaje": "El nombre solo puede contener letras"}), 400

    if len(username) < 4 or len(username) > 50:
        return jsonify({"mensaje": "El username debe tener entre 4 y 50 caracteres"}), 400

    if len(password) < 6 or len(password) > 50:
        return jsonify({"mensaje": "La contraseña debe tener entre 6 y 50 caracteres"}), 400
    
    if rol not in ['admin', 'vendedor']:
        return jsonify({"mensaje": "El rol debe ser admin o vendedor"}), 400
    
    p             = registro(nombre=nombre, username=username, password_hash=password_hash, rol=rol)
    return jsonify({"mensaje":"Usuario registrado","datos":p}), 201

def cntEliminar(id):
    if not id:
        return jsonify({"mensaje": "El id es requerido"}), 400

    eliminado = eliminar(id)

    if not eliminado:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    return jsonify({"mensaje": "Usuario desactivado correctamente"}), 200

    