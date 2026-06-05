from flask import Blueprint
from controllers.abonos_controller import cntListado,cntregistrar, cntListado, cntActualizar,cntEliminar,cntGenerarRecibo
from flask_jwt_extended import jwt_required
from utils.decorators import token_requerido

abono_bp = Blueprint ('abonos', __name__)

@abono_bp.route('/')
#@token_requerido
def listado():
    return cntListado()

@abono_bp.route('/', methods = ["POST"])
#@token_requerido
def registro():
    return cntregistrar()

@abono_bp.route('/<int:id>', methods=['PUT'])
#@token_requerido
def actualizar(id):
    return cntActualizar(id)

@abono_bp.route('/<int:id>', methods=['DELETE'])
#@token_requerido
def eliminar(id):
    return cntEliminar(id)

@abono_bp.route('/<int:id>/recibo', methods=['GET'])
#@token_requerido
def recibo(id):
    return cntGenerarRecibo(id)