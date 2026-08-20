"""
Controller: Prestamos a clientes (v2, con abonos parciales).

IMPORTANTE: ajusta los imports de obtener_cliente / obtener_usuario a las
rutas reales donde ya los tengas definidos en tu proyecto.
"""
from flask import request, jsonify

from services.prestamos_services import (
    registrar, abonar_prestamo, listar_prestamos, listar_pagos_prestamo,
    obtener_prestamo, obtener_disponible_caja, obtener_corte_abierto
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


def cntListarPagosPrestamo(prestamo_id):
    try:
        prestamo_db = obtener_prestamo(prestamo_id)
        if not prestamo_db:
            return jsonify({"mensaje": f"el prestamo con id {prestamo_id} no existe"}), 404
        datos = listar_pagos_prestamo(prestamo_id)
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

        corte_abierto = obtener_corte_abierto()
        if not corte_abierto:
            return jsonify({"mensaje": "no existe un corte abierto"}), 400
        corte_id = corte_abierto["id"]

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


def cntAbonarPrestamo(prestamo_id):
    """
    Registra un abono a un prestamo. Puede ser parcial o cubrir el saldo
    pendiente completo -- en ambos casos es el mismo endpoint (igual que
    los abonos de ventas).
    """
    try:
        requeridos = ["usuario_id", "monto", "medio_pago"]
        faltantes = [x for x in requeridos if x not in request.json]
        if faltantes:
            return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

        vacios = [x for x in requeridos if request.json[x] == "" or request.json[x] is None]
        if vacios:
            return jsonify({"mensaje": f"los siguientes campos estan vacios {vacios}"}), 400

        usuario_id  = request.json["usuario_id"]
        monto       = request.json["monto"]
        medio_pago  = request.json["medio_pago"]
        observacion = request.json.get("observacion", None)

        medios_validos = ["efectivo", "transferencia"]
        if medio_pago not in medios_validos:
            return jsonify({"mensaje": f"medio de pago invalido, debe ser: {medios_validos}"}), 400

        if monto <= 0:
            return jsonify({"mensaje": "el monto debe ser mayor a 0"}), 400

        usuario_db = obtener_usuario(usuario_id)
        if not usuario_db:
            return jsonify({"mensaje": f"el usuario con id {usuario_id} no existe"}), 404

        prestamo_db = obtener_prestamo(prestamo_id)
        if not prestamo_db:
            return jsonify({"mensaje": f"el prestamo con id {prestamo_id} no existe"}), 404

        if prestamo_db["estado"] == "pagado":
            return jsonify({"mensaje": "este prestamo ya fue pagado en su totalidad"}), 400

        if monto > prestamo_db["saldo_pendiente"]:
            return jsonify({
                "mensaje": (
                    f"el abono de ${monto} supera el saldo pendiente "
                    f"de ${prestamo_db['saldo_pendiente']}"
                )
            }), 400

        corte_abierto = obtener_corte_abierto()
        if not corte_abierto:
            return jsonify({"mensaje": "no existe un corte abierto"}), 400

        p = abonar_prestamo(prestamo_id, usuario_id, monto, medio_pago, observacion)
        return jsonify({"mensaje": "abono registrado", "datos": p}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500