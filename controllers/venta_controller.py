from flask import jsonify , request
from  services.ventas_services import listado_ventas,registro
from services.clientes_services import obtener_cliente
from services.cortes_services import obtener_corte
from services.usuarios_servicies import obtener_usuario
from datetime import datetime

def cntListado():
    try:
        datos = listado_ventas()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 

def cntregistrar():
    # 1. validar campos requeridos
    requeridos = ["cliente_id", "corte_id", "usuario_id",
                  "fecha_entrega", "total", "total_abonado"]
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

    # 2. validar campos vacios
    vacios = [x for x in requeridos if request.json[x] == "" 
              or request.json[x] is None]
    if vacios:
        return jsonify({"mensaje": f"los siguientes campos estan vacios {vacios}"}), 400

    id_cliente    = request.json["cliente_id"]
    corte         = request.json["corte_id"]
    usuario       = request.json["usuario_id"]
    fecha_entrega = request.json["fecha_entrega"]
    total         = request.json["total"]
    total_abonado = request.json["total_abonado"]

    # 3. validar que el cliente existe
    cliente = obtener_cliente(id_cliente)
    if not cliente:
        return jsonify({"mensaje": f"el cliente con id {id_cliente} no existe"}), 404

    # 4. validar que el corte existe y no está cerrado
    corte_db = obtener_corte(corte)
    if not corte_db:
        return jsonify({"mensaje": f"el corte con id {corte} no existe"}), 404
    if corte_db["estado"] == "cerrado":
        return jsonify({"mensaje": "no puedes registrar ventas en un corte cerrado"}), 400

    # 5. validar que el usuario existe
    usuario_db = obtener_usuario(usuario)
    if not usuario_db:
        return jsonify({"mensaje": f"el usuario con id {usuario} no existe"}), 404

    # 6. validar que total es positivo
    if total <= 0:
        return jsonify({"mensaje": "el total debe ser mayor a 0"}), 400

    # 7. validar que total_abonado no es negativo
    if total_abonado < 0:
        return jsonify({"mensaje": "el total abonado no puede ser negativo"}), 400

    # 8. validar que abono no supera el total
    if total_abonado > total:
        return jsonify({"mensaje": "el abono no puede ser mayor al total"}), 400

    # 9. validar formato de fecha
    try:
        fecha = datetime.strptime(fecha_entrega, "%d/%m/%Y")
    except ValueError:
        return jsonify({"mensaje": "formato de fecha incorrecto, use DD/MM/YYYY"}), 400

    # 10. validar que fecha no es en el pasado
    if fecha.date() < datetime.now().date():
        return jsonify({"mensaje": "la fecha de entrega no puede ser en el pasado"}), 400

    # registrar la venta
    p = registro(id_cliente, corte, usuario, fecha_entrega, total, total_abonado)
    return jsonify({"mensaje": "venta registrada", "datos": p}), 201