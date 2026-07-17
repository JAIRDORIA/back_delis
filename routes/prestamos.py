from flask import Blueprint
from controllers.prestamos_controller import cntListarPrestamos,cntRegistrarPrestamo,cntPagarPrestamo
from utils.decorators import token_requerido


prestamos_bp = Blueprint ('prestamos', __name__)


@prestamos_bp.route('/', methods = ["GET"])
#@token_requerido
def listado():
    return cntListarPrestamos()

@prestamos_bp.route('/', methods = ["POST"])
#@token_requerido
def registro():
    return cntRegistrarPrestamo()

@prestamos_bp.route('/<int:prestamo_id>/pagar', methods = ["PUT"])
#@token_requerido
def pagar(prestamo_id):
    return cntPagarPrestamo(prestamo_id)



