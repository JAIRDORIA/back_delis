from flask import Blueprint
from controllers.compra_controller import (
    cntListadoCompra, cntRegistroCompra,
    cntActualizarCompra, cntEliminarCompra
)
from utils.decorators import token_requerido, rol_requerido

compra_bp = Blueprint('compra', __name__)

@compra_bp.route('/', methods=['GET'])
@token_requerido
def listado():
    return cntListadoCompra()

@compra_bp.route('/', methods=['POST'])
@token_requerido
def registro():
    return cntRegistroCompra()

@compra_bp.route('/<int:id>', methods=['PUT'])
@token_requerido
def actualizar(id):
    return cntActualizarCompra(id)

@compra_bp.route('/<int:id>', methods=['DELETE'])
@token_requerido
def eliminar(id):
    return cntEliminarCompra(id)