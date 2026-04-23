from flask import Blueprint
from controllers.compra_controller import (
    cntListadoCompra,
    cntObtenerCompra,
    cntRegistroCompra,
    cntActualizarCompra,
    cntEliminarCompra
)

compra_bp = Blueprint('compra', __name__)

@compra_bp.route('/', methods=['GET'])
def listado():
    return cntListadoCompra()

@compra_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    return cntObtenerCompra(id)

@compra_bp.route('/', methods=['POST'])
def registro():
    return cntRegistroCompra()

@compra_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    return cntActualizarCompra(id)

@compra_bp.route('/<int:id>', methods=['DELETE'])
def eliminar(id):
    return cntEliminarCompra(id)