from flask import jsonify , request
from  services.abono_services import listado_abonos, registro
from services.usuarios_servicies import obtener_usuario
from services.cortes_services import obtener_corte
from services.ventas_services import obtener_venta

from datetime import datetime


def cntListado():
    try:
        datos = listado_abonos()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    



def cntregistrar():
    # 1. validar campos requeridos
    # observacion no es requerida porque es NULL en la BD
    requeridos = ["venta_id", "corte_id", "usuario_id", "monto", "fecha"]
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

    # 2. validar campos vacios
    vacios = [x for x in requeridos if request.json[x] == ""
              or request.json[x] is None]
    if vacios:
        return jsonify({"mensaje": f"los siguientes campos estan vacios {vacios}"}), 400

    id_venta = request.json["venta_id"]
    corte    = request.json["corte_id"]
    usuario  = request.json["usuario_id"]
    monto    = request.json["monto"]
    fecha    = request.json["fecha"]
    obs      = request.json.get("observacion", None)  # opcional

    # 3. validar que la venta existe
    venta_db = obtener_venta(id_venta)
    if not venta_db:
        return jsonify({"mensaje": f"la venta con id {id_venta} no existe"}), 404

    # 4. validar que la venta no está entregada
    if venta_db["estado"] == "entregada":
        return jsonify({"mensaje": "no puedes abonar a una venta ya entregada"}), 400

    # 5. validar que el corte existe y no está cerrado
    corte_db = obtener_corte(corte)
    if not corte_db:
        return jsonify({"mensaje": f"el corte con id {corte} no existe"}), 404
    if corte_db["estado"] == "cerrado":
        return jsonify({"mensaje": "no puedes registrar abonos en un corte cerrado"}), 400

    # 6. validar que el usuario existe
    usuario_db = obtener_usuario(usuario)
    if not usuario_db:
        return jsonify({"mensaje": f"el usuario con id {usuario} no existe"}), 404

    # 7. validar que el monto es positivo
    if monto <= 0:
        return jsonify({"mensaje": "el monto debe ser mayor a 0"}), 400

    # 8. validar que el abono no supera el saldo pendiente
    if monto > venta_db["saldo_pendiente"]:
        return jsonify({"mensaje": 
            f"el abono de ${monto} supera el saldo pendiente de ${venta_db['saldo_pendiente']}"}), 400

    # 9. validar formato de fecha
    try:
        fecha = datetime.strptime(fecha, "%d/%m/%Y")
    except ValueError:
        return jsonify({"mensaje": "formato de fecha incorrecto, use DD/MM/YYYY"}), 400

    # 10. validar que fecha no es en el pasado
    if fecha.date() < datetime.now().date():
        return jsonify({"mensaje": "la fecha del abono no puede ser en el pasado"}), 400
    
    fecha = fecha.strftime("%Y-%m-%d")
    

    # registrar el abono
    p = registro(id_venta, corte, usuario, monto, fecha, obs)
    return jsonify({"mensaje": "abono registrado", "datos": p}), 201