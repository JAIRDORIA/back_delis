from flask import Blueprint
from controllers.proveedor_controller import (
    cntListadoProveedores, cntRegistroProveedor,
    cntActualizarProveedor, cntEliminarProveedor
)
from utils.decorators import token_requerido, rol_requerido
proveedores_bp = Blueprint('proveedores', __name__)

@proveedores_bp.route('/', methods=['GET'])
@token_requerido
def listado():
    return cntListadoProveedores()

@proveedores_bp.route('/', methods=['POST'])
@token_requerido
def registro():
    return cntRegistroProveedor()

@proveedores_bp.route('/<int:id>', methods=['PUT'])
@token_requerido
def actualizar(id):
    return cntActualizarProveedor(id)

@proveedores_bp.route('/<int:id>', methods=['DELETE'])
@token_requerido
def eliminar(id):
    return cntEliminarProveedor(id)