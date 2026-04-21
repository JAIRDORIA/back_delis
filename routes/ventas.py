from flask import Blueprint
from controllers.venta_controller import cntListado,cntregistrar, cntActualizar, cntAnular
from flask_jwt_extended import jwt_required

ventas_bp = Blueprint ('ventas', __name__)


@ventas_bp.route('/')
def listado():
    return cntListado()

@ventas_bp.route('/', methods = ["POST"])
#@jwt_required()
def registro():
    return cntregistrar()


@ventas_bp.route('/<int:id>', methods=['PUT'])
#@jwt_required()
def actualizar(id):
    return cntActualizar(id)


@ventas_bp.route('/<int:id>/anulacion', methods=['PUT'])
#@jwt_required()
def anular(id):
    return cntAnular(id)