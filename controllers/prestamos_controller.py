"""
Controller: Prestamos a clientes.

Sigue el mismo patron de validacion usado en ventas_controller.py y
abonos_controller.py: valida campos requeridos -> valida reglas de negocio
-> llama al service.

IMPORTANTE: ajusta los imports de abajo (obtener_cliente, obtener_usuario)
a las rutas reales donde ya los tengas definidos en tu proyecto -- son los
mismos helpers que ya usas en ventas_controller.py y abonos_controller.py.
"""
from flask import request, jsonify

from services.prestamos_services import (
    registrar, pagar, listar_prestamos, obtener_prestamo,
    obtener_disponible_caja, obtener_corte_abierto
)
from services.clientes_services import obtener_cliente
from services.usuarios_servicies import obtener_usuario


def cntListarPrestamos():
    try:
        estado = request.args.get("estado")  # opcional: 'pendiente' | 'pagado'
        datos = listar_prestamos(estado)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
def cntRegistrarPrestamo():
    try:
        requeridos = ["cliente_id", "usuario_id", "monto", "medio_pago"]
        faltantes = [x for x in requeridos if x not in request.json]
        if faltantes:
            return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400
 
        vacios = [x for x in requeridos if request.json[x] == "" or request.json[x] is None]
        if vacios:
            return jsonify({"mensaje": f"los siguientes campos estan vacios {vacios}"}), 400
 
        cliente_id  = request.json["cliente_id"]
        usuario_id  = request.json["usuario_id"]
        monto       = request.json["monto"]
        medio_pago  = request.json["medio_pago"]
        observacion = request.json.get("observacion", None)
 
        medios_validos = ["efectivo", "transferencia"]
        if medio_pago not in medios_validos:
            return jsonify({"mensaje": f"medio de pago invalido, debe ser: {medios_validos}"}), 400
 
        if monto <= 0:
            return jsonify({"mensaje": "el monto debe ser mayor a 0"}), 400
 
        cliente_db = obtener_cliente(cliente_id)
        if not cliente_db:
            return jsonify({"mensaje": f"el cliente con id {cliente_id} no existe"}), 404
 
        usuario_db = obtener_usuario(usuario_id)
        if not usuario_db:
            return jsonify({"mensaje": f"el usuario con id {usuario_id} no existe"}), 404
 
        # el prestamo se asocia automaticamente al corte actualmente abierto
        corte_abierto = obtener_corte_abierto()
        if not corte_abierto:
            return jsonify({"mensaje": "no existe un corte abierto"}), 400
        corte_id = corte_abierto["id"]
 
        # regla de negocio: solo se presta si hay saldo disponible en caja
        # para ese medio de pago especifico
        disponible = obtener_disponible_caja(corte_id, medio_pago)
        if monto > disponible:
            return jsonify({
                "mensaje": (
                    f"saldo insuficiente en caja ({medio_pago}): "
                    f"disponible ${disponible:,.2f}, solicitado ${monto:,.2f}"
                )
            }), 400
 
        p = registrar(cliente_id, corte_id, usuario_id, monto, medio_pago, observacion)
        return jsonify({"mensaje": "prestamo registrado", "datos": p}), 201
 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
def cntPagarPrestamo(prestamo_id):
    try:
        requeridos = ["usuario_id", "medio_pago"]
        faltantes = [x for x in requeridos if x not in request.json]
        if faltantes:
            return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400
 
        vacios = [x for x in requeridos if request.json[x] == "" or request.json[x] is None]
        if vacios:
            return jsonify({"mensaje": f"los siguientes campos estan vacios {vacios}"}), 400
 
        usuario_id = request.json["usuario_id"]
        medio_pago = request.json["medio_pago"]
 
        medios_validos = ["efectivo", "transferencia"]
        if medio_pago not in medios_validos:
            return jsonify({"mensaje": f"medio de pago invalido, debe ser: {medios_validos}"}), 400
 
        usuario_db = obtener_usuario(usuario_id)
        if not usuario_db:
            return jsonify({"mensaje": f"el usuario con id {usuario_id} no existe"}), 404
 
        prestamo_db = obtener_prestamo(prestamo_id)
        if not prestamo_db:
            return jsonify({"mensaje": f"el prestamo con id {prestamo_id} no existe"}), 404
 
        if prestamo_db["estado"] == "pagado":
            return jsonify({"mensaje": "este prestamo ya fue pagado"}), 400
 
        corte_abierto = obtener_corte_abierto()
        if not corte_abierto:
            return jsonify({"mensaje": "no existe un corte abierto"}), 400
 
        p = pagar(prestamo_id, usuario_id, medio_pago)
        return jsonify({"mensaje": "prestamo pagado", "datos": p}), 200
 
    except Exception as e:
        return jsonify({"error": str(e)}), 500