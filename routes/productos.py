from flask import Blueprint
from controllers.productos_controller import cntListado, cntRegistro, cntEliminar,cntProductosMasVendidos, cntActualizar, obtenerProducto
from utils.decorators import token_requerido, rol_requerido
productos_bp = Blueprint ('productos', __name__)


@productos_bp.route('/')
@token_requerido
def listado():
    return cntListado()

@productos_bp.route('/', methods=["POST"])
@token_requerido
def registro():
    return cntRegistro()

@productos_bp.route('/<int:id>', methods=["DELETE"])
@token_requerido    
def eliminar(id):
    return cntEliminar(id)

@productos_bp.route('/mas-vendidos', methods=['GET'])
@token_requerido
def mas_vendidos():
    return cntProductosMasVendidos()

@productos_bp.route('/<int:id>', methods=["PUT"])
@token_requerido
def actualizar(id):
    return cntActualizar(id)

@productos_bp.route('/<int:id>', methods=["GET"])
@token_requerido
def obtener(id):
    return obtenerProducto(id)