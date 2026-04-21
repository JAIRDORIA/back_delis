from flask import Blueprint
from controllers.abonos_controller import cntListado,cntregistrar, cntListado, cntActualizar,cntEliminar
from flask_jwt_extended import jwt_required

abono_bp = Blueprint ('abonos', __name__)

@abono_bp.route('/')
#@jwt_required()
def listado():
    return cntListado()

@abono_bp.route('/', methods = ["POST"])
#@jwt_required()
def registro():
    return cntregistrar()

@abono_bp.route('/<int:id>', methods=['PUT'])
#@jwt_required()
def actualizar(id):
    return cntActualizar(id)

@abono_bp.route('/<int:id>', methods=['DELETE'])
#@jwt_required()
def eliminar(id):
    return cntEliminar(id)