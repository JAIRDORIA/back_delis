from flask import Blueprint
from controllers.venta_controller import cntListado,cntregistrar, cntActualizar, cntAnular
from utils.decorators import token_requerido
from controllers.venta_controller import cntDetalle

ventas_bp = Blueprint ('ventas', __name__)


@ventas_bp.route('/')
#@token_requerido
def listado():
    return cntListado()



@ventas_bp.route('/<int:id>/detalle', methods=['GET'])
#@token_requerido()
def detalle(id):
    return cntDetalle(id)

@ventas_bp.route('/', methods = ["POST"])
#@token_requerido
def registro():
    return cntregistrar()


@ventas_bp.route('/<int:id>', methods=['PUT'])
#@token_requerido
def actualizar(id):
    return cntActualizar(id)


@ventas_bp.route('/<int:id>/anulacion', methods=['PUT'])
@token_requerido
def anular(id):
    return cntAnular(id)