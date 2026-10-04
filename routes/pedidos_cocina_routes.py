"""
Rutas del panel de cocina.

Registra este blueprint en app.py con:
    app.register_blueprint(pedidos_cocina_bp)

Las dos primeras rutas (listar/entregar) son las UNICAS del sistema que
aceptan al rol 'cocina' (@token_requerido_cocina). Todo lo demas usa
@token_requerido y le devuelve 403 a cocina.

La tercera ruta (/por-confirmar) es para el panel ADMIN -- usa el decorador
normal @token_requerido, cocina no tiene por que verla.
"""
from flask import Blueprint

from utils.decorators import token_requerido, token_requerido_cocina, rol_requerido
from controllers.pedidos_cocina_controller import (
    cntListarPedidosCocina, cntEntregarPedido, cntPedidosPorConfirmar
)

pedidos_cocina_bp = Blueprint("pedidos_cocina_bp", __name__, url_prefix="/pedidos-cocina")


@pedidos_cocina_bp.route("/", methods=["GET"])
@token_requerido_cocina
@rol_requerido(["cocina", "admin"])
def listar_pedidos_cocina():
    return cntListarPedidosCocina()


@pedidos_cocina_bp.route("/<int:id>/entregar", methods=["PUT"])
@token_requerido_cocina
@rol_requerido(["cocina", "admin"])
def entregar_pedido(id):
    return cntEntregarPedido(id)


@pedidos_cocina_bp.route("/por-confirmar", methods=["GET"])
@token_requerido
@rol_requerido(["admin", "cajero"])
def pedidos_por_confirmar():
    return cntPedidosPorConfirmar()