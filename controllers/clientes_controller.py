import re
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from services.clientes_services import (
    listado_clientes, crear_clientes, existe_email,clientes_top, 
    obtener_cliente, service_actualizar_cliente, service_eliminar_cliente
)
from utils.decorators import token_requerido

@token_requerido
def get_clientes():
    """
    Listar clientes paginados (RF13)
    ---
    tags: [Clientes]
    security: [{ Bearer: [] }]
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: Lista de clientes obtenida correctamente.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    # Se pasa la paginación al servicio
    w = listado_clientes(page, per_page)
    return jsonify(w)

@jwt_required()
def get_cliente_por_id(id):
    """
    Visualizar detalle de un cliente (RF14)
    ---
    tags: [Clientes]
    security: [{ Bearer: [] }]
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    """
    c = obtener_cliente(id)
    if not c:
        return jsonify({"mensaje": "Cliente no encontrado"}), 404
    return jsonify(c)

@jwt_required()
def cntRegistrar():
    """
    Registrar un nuevo cliente (RF10)
    ---
    tags: [Clientes]
    security: [{ Bearer: [] }]
    """
    # 1. Validar campos requeridos
    requeridos = ["nombre", "telefono", "direccion", "email"]
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

    # 3. Validar que no estén vacíos
    if not nombre or not telefono or not direccion or not email:
        return jsonify({"mensaje": "Todos los campos son obligatorios"}), 400

    # 4. Validar formato de Email (Regex)
    regex_email = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if not re.match(regex_email, email.lower()):
        return jsonify({"mensaje": "El formato del correo electrónico no es válido"}), 400

    # 5. Validar si el email ya existe (Unicidad)
    if existe_email(email):
        return jsonify({"mensaje": "Este correo ya se encuentra registrado"}), 400

    # 6. Llamar al servicio
    resultado = crear_clientes(nombre, telefono, direccion, email)
    
    if isinstance(resultado, tuple):
        return jsonify(resultado[0]), resultado[1]
    
    return jsonify({"mensaje": "Cliente registrado con éxito", "datos": resultado}), 201


def cntClientesTop():
    try:
        limite = request.args.get("limite", 5, type=int)
        if limite < 1 or limite > 20:
            return jsonify({"mensaje": "el limite debe ser entre 1 y 20"}), 400
        datos = clientes_top(limite)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@jwt_required()
def cntActualizar(id):
    """
    Editar información de un cliente (RF11)
    ---
    tags: [Clientes]
    security: [{ Bearer: [] }]
    """
    # Verificar existencia
    if not obtener_cliente(id):
        return jsonify({"mensaje": "Cliente no encontrado para actualizar"}), 404

    if not request.json:
        return jsonify({"mensaje": "No hay datos para actualizar"}), 400

    nombre = str(request.json.get("nombre", "")).strip()
    telefono = str(request.json.get("telefono", "")).strip()
    direccion = str(request.json.get("direccion", "")).strip()
    email = str(request.json.get("email", "")).strip()

    if not nombre or not email:
        return jsonify({"mensaje": "Nombre y Email son obligatorios"}), 400

    # Validar Email duplicado (excluyendo al ID actual)
    if existe_email(email, excluir_id=id):
        return jsonify({"mensaje": "El correo ya pertenece a otro cliente"}), 400

    resultado = service_actualizar_cliente(id, nombre, telefono, direccion, email)
    return jsonify({"mensaje": "Cliente actualizado con éxito", "datos": resultado}), 200

@jwt_required()
def cntEliminar(id):
    """
    Eliminar cliente - Borrado lógico (RF12)
    ---
    tags: [Clientes]
    security: [{ Bearer: [] }]
    """
    if not obtener_cliente(id):
        return jsonify({"mensaje": "Cliente no encontrado"}), 404
    
    service_eliminar_cliente(id)
    return jsonify({"mensaje": f"Cliente con ID {id} eliminado correctamente"}), 200