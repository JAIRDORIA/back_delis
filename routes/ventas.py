from flask import Blueprint
from controllers.venta_controller import cntListado,cntregistrar

ventas_bp = Blueprint ('ventas', __name__)


@ventas_bp.route('/')
def listado():
    return cntListado()

@ventas_bp.route('/', methods = ["POST"])
def registro():
    return cntregistrar()
