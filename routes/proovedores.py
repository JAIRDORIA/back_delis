from flask import Blueprint
from controllers.proveedor_controller import (
    cntListadoProveedores,
    cntObtenerProveedor,
    cntRegistroProveedor,
    cntActualizarProveedor,
    cntEliminarProveedor
)

proveedores_bp = Blueprint('proveedores', __name__)

@proveedores_bp.route('/', methods=['GET'])
def listado():
    return cntListadoProveedores()

@proveedores_bp.route('/<int:id>', methods=['GET'])
def obtener(id):
    return cntObtenerProveedor(id)

@proveedores_bp.route('/', methods=['POST'])
def registro():
    return cntRegistroProveedor()

@proveedores_bp.route('/<int:id>', methods=['PUT'])
def actualizar(id):
    return cntActualizarProveedor(id)

@proveedores_bp.route('/<int:id>', methods=['DELETE'])
def eliminar(id):
    return cntEliminarProveedor(id)