from flask import Blueprint
from controllers.productos_controller import cntListado, cntRegistro, cntEliminar,cntProductosMasVendidos, cntActualizar, obtenerProducto

productos_bp = Blueprint ('productos', __name__)


@productos_bp.route('/')
def listado():
    return cntListado()

@productos_bp.route('/', methods=["POST"])
def registro():
    return cntRegistro()

@productos_bp.route('/<int:id>', methods=["DELETE"])
def eliminar(id):
    return cntEliminar(id)

@productos_bp.route('/mas-vendidos', methods=['GET'])
def mas_vendidos():
    return cntProductosMasVendidos()

@productos_bp.route('/<int:id>', methods=["PUT"])
def actualizar(id):
    return cntActualizar(id)

@productos_bp.route('/<int:id>', methods=["GET"])
def obtener(id):
    return obtenerProducto(id)