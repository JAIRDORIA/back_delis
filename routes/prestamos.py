from flask import Blueprint
from controllers.prestamos_controller import cntListarPrestamos,cntRegistrarPrestamo,cntAbonarPrestamo,cntListarPagosPrestamo
from utils.decorators import token_requerido


prestamos_bp = Blueprint ('prestamos', __name__)


@prestamos_bp.route('/', methods = ["GET"])
#@token_requerido
def listado():
    return cntListarPrestamos()

@prestamos_bp.route('/', methods = ["POST"])
@token_requerido
def registro():
    return cntRegistrarPrestamo()

@prestamos_bp.route('/<int:prestamo_id>/abonos', methods = ["GET"])
@token_requerido
def listarpagos():
    return cntListarPagosPrestamo()

@prestamos_bp.route('/<int:prestamo_id>/abonos', methods = ["POST"])
@token_requerido
def abonar(prestamo_id):
    return cntAbonarPrestamo(prestamo_id)




