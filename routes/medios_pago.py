from flask import Blueprint

from controllers.medios_pago_controller import (
    cntListado,
    cntObtener,
    cntSaldos,
    cntMovimientos,
    cntCrear,
    cntActualizar,
    cntCambiarEstado,
    cntEliminar,
    cntRetiro,
    cntVaciar,
)
from utils.decorators import token_requerido, rol_requerido

medios_pago_bp = Blueprint("medios_pago", __name__)


@medios_pago_bp.route("/", methods=["GET"])
@token_requerido
def listado():
    return cntListado()


@medios_pago_bp.route("/saldos", methods=["GET"])
@token_requerido
def saldos():
    return cntSaldos()


@medios_pago_bp.route("/retiros/vaciar", methods=["POST"])
@token_requerido
def vaciar():
    """Mismos roles que POST /cortes/cerrar: token válido, sin rol_requerido.
    Se declara antes de /<int:id> para no chocar con las rutas por id."""
    return cntVaciar()


@medios_pago_bp.route("/<int:id>", methods=["GET"])
@token_requerido
def obtener(id):
    return cntObtener(id)


@medios_pago_bp.route("/<int:id>/movimientos", methods=["GET"])
@token_requerido
def movimientos(id):
    return cntMovimientos(id)


@medios_pago_bp.route("/", methods=["POST"])
@token_requerido
@rol_requerido(["admin"])
def crear():
    return cntCrear()


@medios_pago_bp.route("/<int:id>", methods=["PUT"])
@token_requerido
@rol_requerido(["admin"])
def actualizar(id):
    return cntActualizar(id)


@medios_pago_bp.route("/<int:id>/estado", methods=["PATCH"])
@token_requerido
@rol_requerido(["admin"])
def cambiar_estado(id):
    return cntCambiarEstado(id)


@medios_pago_bp.route("/<int:id>", methods=["DELETE"])
@token_requerido
@rol_requerido(["admin"])
def eliminar(id):
    return cntEliminar(id)


@medios_pago_bp.route("/<int:id>/retiros", methods=["POST"])
@token_requerido
def retiro(id):
    """Mismos roles que POST /cortes/cerrar: token válido, sin rol_requerido."""
    return cntRetiro(id)
