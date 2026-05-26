from flask import jsonify, request
from services.producciones_services import (
    listado_producciones, registro, obtener_produccion as get_produccion
)
from services.usuarios_servicies import obtener_usuario
from services.productos_services import existe_producto
from datetime import datetime, date 

def cntListado():
    try:
        pagina = int(request.args.get('pagina', 1))
        limite = int(request.args.get('limite', 20))

        if pagina < 1 or limite < 1:
            return jsonify({"mensaje": "pagina y limite deben ser mayores a 0"}), 400

        datos = listado_producciones(pagina=pagina, limite=limite)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntRegistro():
    # 1. Validar campos requeridos — observacion es opcional
    requeridos = ['producto_id', 'cantidad', 'unidades_sueltas', 'usuario_id', 'fecha']
    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"Faltan los siguientes campos: {faltantes}"}), 400

    # 2. Validar que no estén vacíos
    vacios = [c for c in requeridos if str(request.json[c]).strip() == ""]
    if vacios:
        return jsonify({"mensaje": f"Los siguientes campos no pueden estar vacíos: {vacios}"}), 400

    producto_id      = request.json['producto_id']
    cantidad         = request.json['cantidad']
    unidades_sueltas = request.json['unidades_sueltas']
    usuario_id       = request.json['usuario_id']
    fecha            = request.json['fecha']
    observacion      = request.json.get('observacion', None)  # opcional
   
    # 3. Validar que producto_id sea entero positivo
    try:
        producto_id = int(producto_id)
    except:
        return jsonify({"mensaje": "El producto_id debe ser un número entero"}), 400

    if producto_id <= 0:
        return jsonify({"mensaje": "El producto_id debe ser mayor a 0"}), 400

    # 4. Validar que el producto exista
    if not existe_producto(producto_id):
        return jsonify({"mensaje": "El producto no existe o está inactivo"}), 404

    # 5. Validar cantidad
    try:
        cantidad = int(cantidad)
    except:
        return jsonify({"mensaje": "La cantidad debe ser un número entero"}), 400

    if cantidad <= 0:
        return jsonify({"mensaje": "La cantidad debe ser mayor a 0"}), 400

    # 5. Validar unidades_sueltas
    try:
        unidades_sueltas = int(unidades_sueltas)
    except:
        return jsonify({"mensaje": "Las unidades sueltas deben ser un número entero"}), 400

    if unidades_sueltas < 0:
        return jsonify({"mensaje": "Las unidades sueltas deben ser un número entero no negativo"}), 400

    # 6. Validar 
    try:
        usuario_id = int(usuario_id)
    except:
        return jsonify({"mensaje": "El usuario_id debe ser un número entero"}), 400

    if not obtener_usuario(usuario_id):
        return jsonify({"mensaje": "El usuario no existe o está inactivo"}), 404

    # 7. Validar fecha formato DD/MM/YYYY
    try:
        fecha_obj = datetime.strptime(fecha, "%d/%m/%Y").date()
    except:
        return jsonify({"mensaje": "El formato de fecha debe ser DD/MM/YYYY"}), 400
    
    if fecha_obj < date.today():
       return jsonify({"mensaje": "No se permiten fechas anteriores a hoy"}), 400
    
    #observacion es opcional, si viene validar que no sea vacía
    if observacion is not None and str(observacion).strip() == "":
        return jsonify({"mensaje": "Si se proporciona, la observación no puede estar vacía"}), 400
    
    # 8. Registrar
    p = registro(
        producto_id=producto_id,
        cantidad=cantidad,
        unidades_sueltas=unidades_sueltas,
        usuario_id=usuario_id,
        fecha=fecha_obj,
        observacion=observacion
    )
    return jsonify({"mensaje": "Producción registrada", "datos": p}), 201


def cntObtenerProduccion(id):
    if not str(id).isdigit():
        return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    produccion = get_produccion(id)

    if not produccion:
        return jsonify({"mensaje": "Producción no encontrada"}), 404

    return jsonify(produccion), 200