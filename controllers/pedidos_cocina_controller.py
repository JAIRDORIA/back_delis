"""
Controller: panel de cocina.
"""
from datetime import datetime
from flask import request, jsonify, g

from services.pedidos_cocina_service import (
    pedidos_del_dia, marcar_entregado_cocina, estado_para_cocina,
    entregadas_en_cocina_por_confirmar,
)


def cntListarPedidosCocina():
    try:
        fecha = request.args.get("fecha", None, type=str)   # 'YYYY-MM-DD', opcional (por defecto hoy Colombia)
        if fecha:
            try:
                datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                return jsonify({"mensaje": "formato de fecha incorrecto, use YYYY-MM-DD"}), 400

        return jsonify(pedidos_del_dia(fecha)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntEntregarPedido(id):
    """
    Deja constancia de que cocina entrego el pedido. NO cambia ventas.estado
    y NO descuenta inventario: eso solo lo hace el admin desde el modulo de
    ventas (PUT /ventas/<id> con estado='entregada'), como ya funcionaba antes.
    """
    try:
        fila = estado_para_cocina(id)
        if not fila:
            return jsonify({"mensaje": f"el pedido con id {id} no existe"}), 404

        estado, marca_previa = fila
        if estado != "pendiente":
            return jsonify({"mensaje": "Solo se pueden entregar pedidos pendientes"}), 400
        if marca_previa is not None:
            return jsonify({"mensaje": "Este pedido ya fue marcado como entregado en cocina"}), 400

        usuario_id = g.usuario["id"]
        marcado = marcar_entregado_cocina(id, usuario_id)
        if not marcado:
            # otro dispositivo lo marco justo antes (condicion de carrera)
            return jsonify({"mensaje": "Este pedido ya fue entregado en cocina"}), 409

        return jsonify({
            "mensaje": "Pedido marcado como entregado en cocina",
            "datos": {"id": id},
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntPedidosPorConfirmar():
    """
    Para el panel admin: ventas que cocina ya entrego pero que el admin aun no
    confirma (no ha dado clic en 'Entregar' desde el modulo de ventas).
    Alimenta el aviso 'la venta {id} fue entregada en cocina'.
    """
    try:
        return jsonify(entregadas_en_cocina_por_confirmar()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500